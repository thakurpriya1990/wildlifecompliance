import datetime

from dateutil.relativedelta import relativedelta
from django.db import transaction

from django.core.management.base import BaseCommand
from django.db.models import Q, Max
from django.utils import timezone

import logging

from wildlifecompliance import settings
from wildlifecompliance.components.sanction_outcome.email import send_remind_1st_period_overdue_mail, \
    email_detais_to_department_of_transport, send_notification_close_to_due_remediation_action
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, SanctionOutcomeUserAction, \
    AllegedCommittedOffence, DotRequestFile, RemediationAction, RemediationActionNotification
from wildlifecompliance.components.sanction_outcome.serializers import SanctionOutcomeCommsLogEntrySerializer, \
    RemediationActionNotificationCreateSerializer
from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDate
from wildlifecompliance.components.sanction_outcome_due.serializers import SaveSanctionOutcomeDueDateSerializer
from wildlifecompliance.helpers import DEBUG
from wildlifecompliance.management.commands.cron_tasks import get_infringement_notice_coordinators

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send the notification mail to the external user one week before the due date of the a remediation action'

    def handle(self, *args, **options):
        try:
            logger.info('Running command {}'.format(__name__))
            today = timezone.localtime(timezone.now()).date()
            one_week_before = today + relativedelta(days=7)

            # Pick up all the remediation actions which are close to due and no notifications sent yet
            ras = RemediationAction.objects\
                .filter(
                    Q(due_date__lt=one_week_before) &
                    Q(status=RemediationAction.STATUS_OPEN))\
                .exclude(notifications__in=RemediationActionNotification.objects.filter(type=RemediationActionNotification.TYPE_CLOSE_TO_DUE))

            for ra in ras:
                print(ra)

            # Send email (to: offender, bcc: officers)
            for ra in ras:
                try:
                    with transaction.atomic():
                        data = {'sanction_outcome': ra.sanction_outcome.id}
                        serializer = SanctionOutcomeCommsLogEntrySerializer(data=data)
                        serializer.is_valid(raise_exception=True)
                        workflow_entry = serializer.save()

                        to_address = [ra.sanction_outcome.get_offender()[0].email,]
                        cc = None
                        bcc = [member.email for member in ra.sanction_outcome.allocated_group.members]
                        attachments = []
                        email_data = send_notification_close_to_due_remediation_action(to_address, ra.sanction_outcome, workflow_entry, cc, bcc, attachments)

                        # Record in the RemediationActionNotification
                        data = {
                            'remediation_action_id': ra.id,
                            'sanction_outcome_comms_log_entry_id': workflow_entry.id,
                            'type': RemediationActionNotification.TYPE_CLOSE_TO_DUE,
                        }
                        serializer = RemediationActionNotificationCreateSerializer(data=data)
                        serializer.is_valid(raise_exception=True)
                        ran = serializer.save()

                        # Comms log
                        if email_data:
                            serializer = SanctionOutcomeCommsLogEntrySerializer(workflow_entry, data=email_data, partial=True)
                            serializer.is_valid(raise_exception=True)
                            serializer.save()

                        # Action log: sending reminder mail doesn't require an action log entry
                except Exception as e:
                    logger.error('Error command {}'.format(__name__))

            logger.info('Command {} completed'.format(__name__))

        except Exception as e:
            logger.error('Error command {}'.format(__name__))
