import datetime
from django.db import transaction
from django.core.management.base import BaseCommand
from django.db.models import Q, Max
from django.utils import timezone
import logging

from ledger.payments.invoice.models import Invoice

from wildlifecompliance import settings
from wildlifecompliance.components.sanction_outcome.email import send_unpaid_infringements_file
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, SanctionOutcomeUserAction, \
    UnpaidInfringementFile
from wildlifecompliance.components.sanction_outcome.serializers import SanctionOutcomeCommsLogEntrySerializer
from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDate
from wildlifecompliance.components.sanction_outcome_due.serializers import SaveSanctionOutcomeDueDateSerializer
from wildlifecompliance.components.wc_payments.models import InfringementPenalty, InfringementPenaltyInvoice
from wildlifecompliance.helpers import DEBUG
from wildlifecompliance.management.classes.unpaid_infringement_file import UnpaidInfringementFileHeader, \
    UnpaidInfringementFileTrailer
from wildlifecompliance.management.commands.cron_tasks import get_infringement_notice_coordinators

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send unpaid infringements file emails for infringements which have past payment due dates'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                logger.info('Running command {}'.format(__name__))
                today = timezone.localtime(timezone.now()).date()

                # Retrieve sanction outcomes whose type is Infringement Notice and which is unpaid
                sanction_outcomes_base = SanctionOutcome.objects.filter(
                    Q(type=SanctionOutcome.TYPE_INFRINGEMENT_NOTICE) &
                    Q(status=SanctionOutcome.STATUS_AWAITING_PAYMENT) &
                    Q(payment_status=SanctionOutcome.PAYMENT_STATUS_UNPAID))\
                    .filter(due_dates__in=SanctionOutcomeDueDate.objects.filter(Q(due_date_2nd__lt=today) & Q(due_date_term_currently_applied='2nd')))

                if DEBUG:
                    # For debugging purpose, infringement notice which has the string '__overdue2nd__' in the description field is also selected.
                    logger.info('DEBUG = True')
                    sanction_outcomes_debug = SanctionOutcome.objects.filter(
                        Q(type=SanctionOutcome.TYPE_INFRINGEMENT_NOTICE) &
                        # Q(status=SanctionOutcome.STATUS_AWAITING_PAYMENT) &
                        # Q(payment_status=SanctionOutcome.PAYMENT_STATUS_UNPAID) &
                        Q(description__icontains='__overdue2nd__'))
                        # .filter(due_dates__in=SanctionOutcomeDueDate.objects.filter(Q(due_date_term_currently_applied='2nd')))

                # Merge querysets
                sanction_outcomes = (sanction_outcomes_base | sanction_outcomes_debug).distinct()

                count = sanction_outcomes.count()
                logger.info('{} overdue (1st) infringement notice(s) found.'.format(str(count)))

                if count:
                    # Create record first to generate filename based on the ID
                    uin_file = UnpaidInfringementFile()
                    uin_file.save()

                    # Construct header
                    uin_header = UnpaidInfringementFileHeader()
                    uin_header.agency_code.set('DPW')
                    uin_header.uin_file_reference.set(uin_file.filename)
                    uin_header.date_created.set(datetime.date.today())
                    uin_header.responsible_officer.set('')
                    content_header = uin_header.get_content()

                    # Construct body
                    content_body = ''
                    penalty_amount_total = 0
                    for so in sanction_outcomes:
                        try:
                            content_body += so.get_content_for_uin()
                            penalty_amount_total += so.penalty_amount_2nd
                        except Exception as e:
                            logger.error('Error command {} for the sanction outcome: {}'.format(__name__, str(so.id)))

                    # Construct trailer
                    uin_trailer = UnpaidInfringementFileTrailer()
                    uin_trailer.number_of_records.set(sanction_outcomes.count())
                    uin_trailer.total_penalty_amount.set(penalty_amount_total)
                    uin_trailer.first_additional_cost_code.set('')
                    uin_trailer.first_additional_cost_total.set('')
                    uin_trailer.second_additional_cost_code.set('')
                    uin_trailer.second_additional_cost_total.set('')
                    content_trailer = uin_trailer.get_content()

                    # Construct file contents
                    contents_to_attach = content_header + content_body + content_trailer

                    # Save contents in the DB, too
                    uin_file.contents = contents_to_attach
                    uin_file.save()

                    # Determine the recipients
                    members = get_infringement_notice_coordinators()

                    # Emailing

                    to_address = [member.email for member in members] if members else [settings.NOTIFICATION_EMAIL]
                    cc = None
                    bcc = None
                    attachments = [(uin_file.filename, contents_to_attach, 'text/plain'),]
                    email_data = send_unpaid_infringements_file(to_address, cc, bcc, attachments)

                    # # Add communication log
                    if email_data:
                        for so in sanction_outcomes:
                            email_data['sanction_outcome'] = so.id
                            serializer = SanctionOutcomeCommsLogEntrySerializer(data=email_data, partial=True)
                            serializer.is_valid(raise_exception=True)
                            serializer.save()

                    # Record action log per infringement notice
                    # for dict_item in due_dates:
                    for so in sanction_outcomes:
                        so.log_user_action(SanctionOutcomeUserAction.ACTION_SEND_DETAILS_TO_INFRINGEMENT_NOTICE_COORDINATOR.format(so.lodgement_number))
                        so.status = SanctionOutcome.STATUS_OVERDUE
                        so.save()

                        # Create new due_date record
                        data = {}
                        data['due_date_1st'] = None
                        data['due_date_2nd'] = None
                        data['reason_for_extension'] = 'Overdue 2nd due date'
                        data['extended_by_id'] = None
                        data['sanction_outcome_id'] = so.id
                        data['due_date_term_currently_applied'] = 'overdue'
                        serializer = SaveSanctionOutcomeDueDateSerializer(data=data)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()

                logger.info('Command {} completed'.format(__name__))

        except Exception as e:
            logger.error('Error command {}'.format(__name__))
