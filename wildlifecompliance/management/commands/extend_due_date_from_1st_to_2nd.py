from django.db import transaction

from django.core.management.base import BaseCommand
from django.db.models import Q, Max
from django.utils import timezone

import logging

from wildlifecompliance.components.sanction_outcome.email import send_remind_1st_period_overdue_mail
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, SanctionOutcomeUserAction
from wildlifecompliance.components.sanction_outcome.serializers import SanctionOutcomeCommsLogEntrySerializer
from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDate
from wildlifecompliance.components.sanction_outcome_due.serializers import SaveSanctionOutcomeDueDateSerializer
from wildlifecompliance.helpers import DEBUG

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Extend original due date to 2nd due date'

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
                    Q(due_date_1st__lt=today) &
                    Q(due_date_term_currently_applied='1st') &
                    Q(sanction_outcome__in=sanction_outcomes))

                # Final query
                # retrieve all the sanction_outcomes which expires 1st due date
                due_dates = SanctionOutcomeDueDate.objects.filter(due_date_condition).\
                    values('sanction_outcome').annotate(max_id=Max('id')).order_by('sanction_outcome').distinct()

                if DEBUG:
                    # For debugging purpose, infringement notice which has the string '__overdue1st__' in the description field is also selected.
                    logger.info('DEBUG = True')
                    sanction_outcomes = SanctionOutcome.objects.filter(
                        Q(type=SanctionOutcome.TYPE_INFRINGEMENT_NOTICE) &
                        Q(status=SanctionOutcome.STATUS_AWAITING_PAYMENT) &
                        Q(payment_status=SanctionOutcome.PAYMENT_STATUS_UNPAID) &
                        Q(description__icontains='__overdue1st__'))

                    # Conditions for filter the SanctionOutcomeDueDate
                    due_date_condition = (
                        Q(due_date_term_currently_applied='1st') &
                        Q(sanction_outcome__in=sanction_outcomes))

                    # Final query
                    # retrieve all the sanction_outcomes which expires 1st due date
                    due_dates_dev = SanctionOutcomeDueDate.objects.filter(due_date_condition). \
                        values('sanction_outcome').annotate(max_id=Max('id')).order_by('sanction_outcome').distinct()

                # Merge querysets
                due_dates = due_dates | due_dates_dev if due_dates_dev else due_dates
                due_dates = due_dates.distinct()

                count = due_dates.count()
                logger.info('{} overdue (1st) infringement notice(s) found.'.format(str(count)))

                if count:
                    # Create another due-date record
                    for dict_item in due_dates:
                        latest_due_date = SanctionOutcomeDueDate.objects.get(id=dict_item.get('max_id'))
                        overdue_sanction_outcome = SanctionOutcome.objects.get(id=dict_item.get('sanction_outcome'))
                        data = {}
                        data['due_date_1st'] = latest_due_date.due_date_1st
                        data['due_date_2nd'] = latest_due_date.due_date_2nd
                        data['reason_for_extension'] = 'overdue 1st due date'
                        data['extended_by_id'] = None
                        data['sanction_outcome_id'] = overdue_sanction_outcome.id
                        data['due_date_term_currently_applied'] = '2nd'
                        serializer = SaveSanctionOutcomeDueDateSerializer(data=data)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()

                        # Send reminder email (to: offender, cc: , bcc: respoinsible officer)
                        to_address = [overdue_sanction_outcome.get_offender().email, ]
                        cc = None
                        bcc = [overdue_sanction_outcome.responsible_officer.email,] if overdue_sanction_outcome.responsible_officer else None
                        email_data = send_remind_1st_period_overdue_mail(to_address, overdue_sanction_outcome, cc, bcc)

                        # Add communication log
                        if email_data:
                            email_data['sanction_outcome'] = overdue_sanction_outcome.id
                            serializer = SanctionOutcomeCommsLogEntrySerializer(data=email_data, partial=True)
                            serializer.is_valid(raise_exception=True)
                            serializer.save()

                        # Add action log
                        overdue_sanction_outcome.log_user_action(SanctionOutcomeUserAction.ACTION_INCREASE_FEE_AND_EXTEND_DUE.format(
                            overdue_sanction_outcome.penalty_amount_1st,
                            overdue_sanction_outcome.penalty_amount_2nd,
                            latest_due_date.due_date_1st,
                            latest_due_date.due_date_2nd,
                        ))

                logger.info('Command {} completed'.format(__name__))

        except Exception as e:
            logger.error('Error command {}'.format(__name__))
