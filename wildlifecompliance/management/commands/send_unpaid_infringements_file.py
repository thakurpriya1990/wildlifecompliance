import datetime

from django.db import transaction

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Q, Max

from django.utils import timezone
import logging

from wildlifecompliance import settings
from wildlifecompliance.components.sanction_outcome.email import send_unpaid_infringements_file
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, SanctionOutcomeUserAction, \
    UnpaidInfringementFile
from wildlifecompliance.components.sanction_outcome.serializers import SanctionOutcomeCommsLogEntrySerializer
from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDate
from wildlifecompliance.components.users.models import CompliancePermissionGroup
from wildlifecompliance.helpers import DEBUG
from wildlifecompliance.management.classes.unpaid_infringement_file import UnpaidInfringementFileHeader, \
    UnpaidInfringementFileTrailer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send unpaid infringements file emails for infringements which have past payment due dates'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                logger.info('Running command {}'.format(__name__))
                today = timezone.localtime(timezone.now()).date()

                # Retrieve sanction outcomes whose type is Infringement Notice and which is unpaid
                sanction_outcomes = SanctionOutcome.objects.filter(
                    Q(type=SanctionOutcome.TYPE_INFRINGEMENT_NOTICE) &
                    Q(status=SanctionOutcome.STATUS_AWAITING_PAYMENT) &
                    Q(payment_status=SanctionOutcome.PAYMENT_STATUS_UNPAID))

                # Conditions for filter the SanctionOutcomeDueDate
                due_date_condition = (
                        Q(due_date_2nd__lt=today) &
                        Q(due_date_term_currently_applied='2nd') &
                        Q(sanction_outcome__in=sanction_outcomes))

                # Final query
                # retrieve all the sanction_outcomes which expires 1st due date
                due_dates = SanctionOutcomeDueDate.objects.filter(due_date_condition). \
                    values('sanction_outcome').annotate(max_id=Max('id')).order_by('sanction_outcome').distinct()

                if DEBUG:
                    # For debugging purpose, infringement notice which has the string '__overdue2nd__' in the description field is also selected.
                    logger.info('DEBUG = True')
                    sanction_outcomes = SanctionOutcome.objects.filter(
                        Q(type=SanctionOutcome.TYPE_INFRINGEMENT_NOTICE) &
                        Q(status=SanctionOutcome.STATUS_AWAITING_PAYMENT) &
                        Q(payment_status=SanctionOutcome.PAYMENT_STATUS_UNPAID) &
                        Q(description__icontains='__overdue2nd__'))

                    # Conditions for filter the SanctionOutcomeDueDate
                    due_date_condition = (
                            # Q(due_date_term_currently_applied='2nd') &
                            Q(sanction_outcome__in=sanction_outcomes))

                    # Final query
                    # retrieve all the sanction_outcomes which expires 1st due date
                    due_dates_dev = SanctionOutcomeDueDate.objects.filter(due_date_condition). \
                        values('sanction_outcome').annotate(max_id=Max('id')).order_by('sanction_outcome').distinct()

                # Merge querysets
                due_dates = due_dates | due_dates_dev if due_dates_dev else due_dates
                due_dates = due_dates.distinct()

                count = due_dates.count()
                sanction_outcome_ids = []  # Used when logging
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
                    for dict_item in due_dates:
                        sanction_outcome_id = dict_item.get('sanction_outcome')
                        sanction_outcome_ids.append(sanction_outcome_id)
                        so = SanctionOutcome.objects.get(id=sanction_outcome_id)
                        content_body += so.get_content_for_uin()
                        penalty_amount_total += so.penalty_amount_2nd

                    # Construct trailer
                    uin_trailer = UnpaidInfringementFileTrailer()
                    uin_trailer.number_of_records.set(due_dates.count())
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
                    compliance_content_type = ContentType.objects.get(model="compliancepermissiongroup")
                    permissions = Permission.objects.filter(codename='infringement_notice_coordinator', content_type_id=compliance_content_type.id)
                    allowed_groups = CompliancePermissionGroup.objects.filter(permissions__in=permissions)
                    groups = [group for group in allowed_groups.all()]
                    members = [member for member in group.members for group in groups]

                    # Emailing
                    to_address = [member.email for member in members] if members else [settings.NOTIFICATION_EMAIL]
                    cc = None
                    bcc = None
                    attachments = [(uin_file.filename, contents_to_attach, 'text/plain'),]
                    email_data = send_unpaid_infringements_file(to_address, cc, bcc, attachments)

                    # # Add communication log
                    if email_data:
                        for id in sanction_outcome_ids:
                            email_data['sanction_outcome'] = id
                            serializer = SanctionOutcomeCommsLogEntrySerializer(data=email_data, partial=True)
                            serializer.is_valid(raise_exception=True)
                            serializer.save()

                    # Record action log per infringement notice
                    for dict_item in due_dates:
                        # latest_due_date = SanctionOutcomeDueDate.objects.get(id=dict_item.get('max_id'))
                        infringement = SanctionOutcome.objects.get(id=dict_item.get('sanction_outcome'))
                        infringement.log_user_action(SanctionOutcomeUserAction.ACTION_SEND_DETAILS_TO_INFRINGEMENT_NOTICE_COORDINATOR.format(infringement))
                        # Update status to Overdue but the allocated group should be already in 'infringement_notice_coordinator', so no need to change it.
                        infringement.status = SanctionOutcome.STATUS_OVERDUE
                        infringement.save()

                logger.info('Command {} completed'.format(__name__))

        except Exception as e:
            logger.error('Error command {}'.format(__name__))
