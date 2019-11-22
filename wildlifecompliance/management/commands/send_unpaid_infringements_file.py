import datetime
from django.db import transaction

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from django.core.mail import EmailMessage
from six.moves import StringIO
import csv

import logging

from wildlifecompliance import settings
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, SanctionOutcomeUserAction
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

                unpaid_infringements = SanctionOutcome.objects.filter(Q(type=SanctionOutcome.TYPE_INFRINGEMENT_NOTICE) &
                                                                      Q(status=SanctionOutcome.STATUS_AWAITING_PAYMENT) &
                                                                      Q(payment_status=SanctionOutcome.PAYMENT_STATUS_UNPAID) &
                                                                      Q(due_date_extended_max__lt=today))

                if DEBUG:
                    # For debugging purpose, infringement notice which has the string '__overdue__' in the description field is also selected.
                    logger.info('DEBUG = True')
                    unpaid_infringements = SanctionOutcome.objects.filter(
                        Q(type=SanctionOutcome.TYPE_INFRINGEMENT_NOTICE) &
                        Q(status=SanctionOutcome.STATUS_AWAITING_PAYMENT) &
                        Q(payment_status=SanctionOutcome.PAYMENT_STATUS_UNPAID) &
                        (Q(due_date_extended_max__lt=today) | Q(description__icontains='__overdue__')))

                count = unpaid_infringements.count()
                logger.info('{} unpaid infringement notice(s) found.'.format(str(count)))

                if count:
                    # Generate CSV file
                    strIO = StringIO()
                    fieldnames = ['Infringement Number', 'Offence Date/Time', ]
                    writer = csv.writer(strIO)
                    writer.writerow(fieldnames)
                    for infringement in unpaid_infringements.all():
                        # fullname = '{} {}'.format(o.details.get('first_name'),o.details.get('last_name'))
                        # writer.writerow([o.confirmation_number,fullname,o.campground.name,o.arrival.strftime('%d/%m/%Y'),o.departure.strftime('%d/%m/%Y'),o.outstanding])
                        writer.writerow([infringement.lodgement_number, infringement.offence_occurrence_datetime])
                    strIO.flush()
                    strIO.seek(0)
                    _file = strIO

                    dt = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')

                    # Determine the recipients
                    compliance_content_type = ContentType.objects.get(model="compliancepermissiongroup")
                    permissions = Permission.objects.filter(codename='infringement_notice_coordinator', content_type_id=compliance_content_type.id)
                    allowed_groups = CompliancePermissionGroup.objects.filter(permissions__in=permissions)
                    groups = [group for group in allowed_groups.all()]
                    members = [member for member in group.members for group in groups]

                    email = EmailMessage(
                        'Unpaid Infringements File at {}'.format(dt),
                        'Unpaid Infringements File',
                        settings.EMAIL_FROM,
                        to=[member.email for member in members] if members else [settings.NOTIFICATION_EMAIL]
                    )
                    email.attach('UnpaidInfringementsFile_{}.csv'.format(dt), _file.getvalue(), 'text/csv')
                    email.send()

                    # Record action log per infringement notice
                    for infringement in unpaid_infringements.all():
                        infringement.log_user_action(SanctionOutcomeUserAction.ACTION_SEND_DETAILS_TO_INFRINGEMENT_NOTICE_COORDINATOR.format(infringement))
                        # Update status to Overdue but the allocated group should be already in 'infringement_notice_coordinator', so no need to change it.
                        infringement.status = SanctionOutcome.STATUS_OVERDUE
                        infringement.save()

                logger.info('Command {} completed'.format(__name__))

        except Exception as e:
            logger.error('Error command {}'.format(__name__))
