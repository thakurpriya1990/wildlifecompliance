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
from wildlifecompliance.components.sanction_outcome.email import send_remind_1st_period_overdue_mail, \
    send_unpaid_infringements_file
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, SanctionOutcomeUserAction
from wildlifecompliance.components.sanction_outcome.serializers import SanctionOutcomeCommsLogEntrySerializer
from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDate
from wildlifecompliance.components.users.models import CompliancePermissionGroup
from wildlifecompliance.helpers import DEBUG

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
                            Q(due_date_term_currently_applied='2nd') &
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
                    # START: Generate CSV file
                    strIO = StringIO()
                    fieldnames = ['Infringement Number', 'Offence Date/Time', ]
                    writer = csv.writer(strIO)
                    writer.writerow(fieldnames)
                    for dict_item in due_dates:
                        # latest_due_date = SanctionOutcomeDueDate.objects.get(id=dict_item.get('max_id'))
                        overdue_sanction_outcome = SanctionOutcome.objects.get(id=dict_item.get('sanction_outcome'))
                        # fullname = '{} {}'.format(o.details.get('first_name'),o.details.get('last_name'))
                        # writer.writerow([o.confirmation_number,fullname,o.campground.name,o.arrival.strftime('%d/%m/%Y'),o.departure.strftime('%d/%m/%Y'),o.outstanding])
                        writer.writerow([overdue_sanction_outcome.lodgement_number, overdue_sanction_outcome.offence_occurrence_datetime])
                    strIO.flush()
                    strIO.seek(0)
                    _file = strIO
                    # END: Generate CSV file

                    dt = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')

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
                    attachments = [('UnpaidInfringementsFile_{}.csv'.format(dt), _file.getvalue(), 'text/csv'),]
                    email_data = send_unpaid_infringements_file(to_address, cc, bcc, attachments)

                    # # Add communication log
                    if email_data:
                        email_data['sanction_outcome'] = overdue_sanction_outcome.id
                        serializer = SanctionOutcomeCommsLogEntrySerializer(data=email_data, partial=True)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()

                        # Create SanctionOutcomeCommsLogDocument object
                        # so that the link to the infringement notice file can be created in the comms log
                        # temp = SanctionOutcomeCommsLogDocument(log_entry=serializer.instance, _file=File(BytesIO()), name=pdf_file_name)
                        # temp.save()

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
