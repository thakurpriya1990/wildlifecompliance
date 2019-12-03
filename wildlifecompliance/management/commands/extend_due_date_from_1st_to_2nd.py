import datetime
from django.db import transaction

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Q, Max
from django.utils import timezone
from django.core.mail import EmailMessage
from six.moves import StringIO
import csv

import logging

from wildlifecompliance import settings
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, SanctionOutcomeUserAction
from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDate
from wildlifecompliance.components.sanction_outcome_due.serializers import SaveSanctionOutcomeDueDateSerializer
from wildlifecompliance.components.users.models import CompliancePermissionGroup
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
                sanction_outcomes = SanctionOutcome.objects.filter(Q(type=SanctionOutcome.TYPE_INFRINGEMENT_NOTICE) &
                                                       Q(status=SanctionOutcome.STATUS_AWAITING_PAYMENT) &
                                                       Q(payment_status=SanctionOutcome.PAYMENT_STATUS_UNPAID))

                # Conditions for filter the SanctionOutcomeDueDate
                due_date_condition = (Q(due_date_1st__lt=today) &
                                      Q(due_date_term_currently_applied='1st') &
                                      Q(sanction_outcome__in=sanction_outcomes))
                # Final query
                due_dates = SanctionOutcomeDueDate.objects.filter(due_date_condition).\
                    values('sanction_outcome').annotate(max_id=Max('id')).order_by('sanction_outcome').distinct()

                if DEBUG:
                    # For debugging purpose, infringement notice which has the string '__overdue__' in the description field is also selected.
                    logger.info('DEBUG = True')
                    sanction_outcomes = SanctionOutcome.objects.filter(
                        Q(type=SanctionOutcome.TYPE_INFRINGEMENT_NOTICE) &
                        Q(status=SanctionOutcome.STATUS_AWAITING_PAYMENT) &
                        Q(payment_status=SanctionOutcome.PAYMENT_STATUS_UNPAID))
                    due_date_condition = (Q(due_date_term_currently_applied='1st') &
                                         Q(sanction_outcome__in=sanction_outcomes))
                    # Final query
                    due_dates = SanctionOutcomeDueDate.objects.filter(due_date_condition). \
                        values('sanction_outcome').annotate(max_id=Max('id')).order_by('sanction_outcome').distinct()

                count = due_dates.count()
                logger.info('{} overdue (1st) infringement notice(s) found.'.format(str(count)))

                if count:
                    # Create another due-date record
                    for due_date in due_dates:
                        data = {}
                        data['due_date_1st'] = due_date.due_date_1st
                        data['due_date_2nd'] = due_date.due_date_2nd
                        data['reason_for_extension'] = 'overdue 1st due date'
                        data['extended_by_id'] = None
                        data['sanction_outcome_id'] = due_date.sanction_outcome.id
                        serializer = SaveSanctionOutcomeDueDateSerializer(data=data)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()

                logger.info('Command {} completed'.format(__name__))

        except Exception as e:
            logger.error('Error command {}'.format(__name__))
