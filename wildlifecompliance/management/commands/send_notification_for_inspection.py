import datetime

import pytz
from django.db import transaction
from django.core.management.base import BaseCommand
from django.db.models import Q, Max
from django.utils import timezone
import logging

from ledger.payments.invoice.models import Invoice
from ledger.settings_base import TIME_ZONE

from wildlifecompliance import settings
from wildlifecompliance.components.inspection.email import send_notification_of_inspection_email
from wildlifecompliance.components.inspection.models import Inspection
from wildlifecompliance.components.inspection.serializers import InspectionCommsLogEntrySerializer
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
    help = 'Send an email to the party to be inspected if the party to be informed'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                logger.info('Running command {}'.format(__name__))
                now_local = datetime.datetime.now(pytz.timezone(TIME_ZONE))
                today_local = now_local.date()
                days_7 = datetime.timedelta(days=7)
                week_after_today = today_local + days_7

                inspections = Inspection.objects.filter(
                    Q(inform_party_being_inspected=True) &
                    Q(planned_for_date__lte=week_after_today) &
                    Q(informed_datetime=None)
                )

                for inspection in inspections:
                    try:
                        if inspection.party_inspected == Inspection.PARTY_INDIVIDUAL:
                            to_address = [inspection.individual_inspected.email,]
                        else:
                            to_address = [inspection.organisation_inspected.email,]

                        cc = None
                        bcc = None
                        attachments = []
                        email_data = send_notification_of_inspection_email(to_address, inspection, cc, bcc, attachments)

                        # Add communication log
                        if email_data:
                            email_data['inspection'] = inspection.id
                            serializer = InspectionCommsLogEntrySerializer(data=email_data, partial=True)
                            serializer.is_valid(raise_exception=True)
                            serializer.save()

                        # Update inspection
                        inspection.informed_datetime = now_local
                        inspection.save()

                    except Exception as e:
                        logger.error('Error command {} for the inspection: {}'.format(__name__, inspection.number))
                        continue

                logger.info('Command {} completed'.format(__name__))

        except Exception as e:
            logger.error('Error command {}'.format(__name__))
