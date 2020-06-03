from django.db import transaction

from django.core.management.base import BaseCommand
from django.db.models import Q, Max
from django.utils import timezone

import logging

from ledger.payments.invoice.models import Invoice

from wildlifecompliance import settings
from wildlifecompliance.components.sanction_outcome.email import send_remind_1st_period_overdue_mail
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, SanctionOutcomeUserAction
from wildlifecompliance.components.sanction_outcome.serializers import SanctionOutcomeCommsLogEntrySerializer
from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDate
from wildlifecompliance.components.sanction_outcome_due.serializers import SaveSanctionOutcomeDueDateSerializer
from wildlifecompliance.components.wc_payments.models import InfringementPenalty, InfringementPenaltyInvoice
from wildlifecompliance.helpers import DEBUG
from wildlifecompliance.management.commands.cron_tasks import get_infringement_notice_coordinators

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Extend original due date to 2nd due date'

    def handle(self, *args, **options):
        try:
            logger.info('Running command {}'.format(__name__))
            today = timezone.localtime(timezone.now()).date()

            # Retrieve sanction outcomes whose type is Infringement Notice and which is unpaid
            sanction_outcomes_base = SanctionOutcome.objects.filter(
                Q(type=SanctionOutcome.TYPE_INFRINGEMENT_NOTICE) &
                Q(status=SanctionOutcome.STATUS_AWAITING_PAYMENT) &
                Q(payment_status=SanctionOutcome.PAYMENT_STATUS_UNPAID)) \
                .filter(due_dates__in=SanctionOutcomeDueDate.objects.filter(Q(due_date_1st__lt=today) & Q(due_date_term_currently_applied='1st'))) \
                .exclude(due_dates__in=SanctionOutcomeDueDate.objects.filter(Q(due_date_term_currently_applied='2nd')))

            if DEBUG:
                # For debugging purpose, infringement notice which has the string '__overdue1st__' in the description field is also selected.
                logger.info('DEBUG = True')
                sanction_outcomes_debug = SanctionOutcome.objects.filter(
                    Q(type=SanctionOutcome.TYPE_INFRINGEMENT_NOTICE) &
                    # Q(status=SanctionOutcome.STATUS_AWAITING_PAYMENT) &
                    # Q(payment_status=SanctionOutcome.PAYMENT_STATUS_UNPAID) &
                    Q(description__icontains='__overdue1st__'))
                    # .filter(due_dates__in=SanctionOutcomeDueDate.objects.filter(Q(due_date_term_currently_applied='1st'))) \
                    # .exclude(due_dates__in=SanctionOutcomeDueDate.objects.filter(Q(due_date_term_currently_applied='2nd')))

            # Merge querysets
            sanction_outcomes = (sanction_outcomes_base | sanction_outcomes_debug).distinct()

            count = sanction_outcomes.count()
            logger.info('{} overdue (1st) infringement notice(s) found.'.format(str(count)))

            # Process each overdue sanction outcome
            for overdue_sanction_outcome in sanction_outcomes.all():
                try:
                    with transaction.atomic():
                        latest_due_date = SanctionOutcomeDueDate.objects.filter(
                            sanction_outcome=overdue_sanction_outcome).order_by('id').last()

                        # Create new due_date record
                        data = {}
                        data['due_date_1st'] = latest_due_date.due_date_1st
                        data['due_date_2nd'] = latest_due_date.due_date_2nd
                        data['reason_for_extension'] = 'Overdue 1st due date'
                        data['extended_by_id'] = None
                        data['sanction_outcome_id'] = overdue_sanction_outcome.id
                        data['due_date_term_currently_applied'] = '2nd'
                        serializer = SaveSanctionOutcomeDueDateSerializer(data=data)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()

                        # Create comms log entry
                        data = {'sanction_outcome': overdue_sanction_outcome.id}
                        serializer = SanctionOutcomeCommsLogEntrySerializer(data=data)
                        serializer.is_valid(raise_exception=True)
                        comms_log_entry = serializer.save()

                        # Determine the bcc
                        members = get_infringement_notice_coordinators()
                        bcc_list = [member.email for member in members] if members else [settings.NOTIFICATION_EMAIL]
                        if overdue_sanction_outcome.responsible_officer:
                            bcc_list.append(overdue_sanction_outcome.responsible_officer.email)

                        # Email
                        to_address = [overdue_sanction_outcome.get_offender()[0].email, ]
                        cc = None
                        bcc = bcc_list
                        email_data = send_remind_1st_period_overdue_mail(to_address, overdue_sanction_outcome,
                                                                         comms_log_entry, cc, bcc)

                        # Add communication log
                        if email_data:
                            serializer = SanctionOutcomeCommsLogEntrySerializer(instance=comms_log_entry, data=email_data,
                                                                                partial=True)
                            serializer.is_valid(raise_exception=True)
                            serializer.save()

                        # Add action log
                        overdue_sanction_outcome.log_user_action(
                            SanctionOutcomeUserAction.ACTION_INCREASE_FEE_AND_EXTEND_DUE.format(
                                latest_due_date.due_date_1st,
                                latest_due_date.due_date_2nd,
                                overdue_sanction_outcome.penalty_amount_1st,
                                overdue_sanction_outcome.penalty_amount_2nd,
                            ))
                except Exception as e:
                    logger.error('Error command {}'.format(__name__))

            logger.info('Command {} finished'.format(__name__))

        except Exception as e:
            logger.error('Error command {}'.format(__name__))
