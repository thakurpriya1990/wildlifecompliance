from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from pathlib import Path
import subprocess
import logging
from wildlifecompliance.components.users.models import CompliancePermissionGroup

logger = logging.getLogger(__name__)

LOGFILE = 'logs/cron_tasks.log'

class Command(BaseCommand):
    help = 'Run the Wildlife Compliance Cron tasks'

    def handle(self, *args, **options):
        stdout_redirect = ' | tee -a {}'.format(LOGFILE)
        subprocess.call('cat /dev/null > {}'.format(LOGFILE), shell=True)  # empty the log file

        logger.info('Running command {}'.format(__name__))

        subprocess.call('python manage_wc.py verify_due_returns' + stdout_redirect, shell=True)
        subprocess.call('python manage_wc.py verify_expired_licences' + stdout_redirect, shell=True)
        subprocess.call('python manage_wc.py verify_licence_renewals' + stdout_redirect, shell=True)
        subprocess.call('python manage_wc.py verify_species' + stdout_redirect, shell=True)

        # subprocess.call('python manage_wc.py send_unpaid_infringements_file', shell=True)
        # subprocess.call('python manage_wc.py extend_due_date_from_1st_to_2nd', shell=True)
        # subprocess.call('python manage_wc.py send_rego_to_dot', shell=True)
        # subprocess.call('python manage_wc.py close_document_and_physical_artifacts', shell=True)
        # subprocess.call('python manage_wc.py notification_close_to_due_remediation_action', shell=True)
        # subprocess.call('python manage_wc.py notification_overdue_remediation_action', shell=True)

        logger.info('Command {} completed'.format(__name__))
        self.send_email()

    def send_email(self):
        '''
        Reads stdout_redirect (LOGFILE) and emails to notification list.
        '''
        log_txt = Path(LOGFILE).read_text()
        subject = '{0} - Cronjob'.format(settings.SYSTEM_NAME)
        body = ''
        to = settings.NOTIFICATION_EMAIL if isinstance(settings.NOTIFICATION_EMAIL, list) else [settings.NOTIFICATION_EMAIL]
        send_mail(subject, body, settings.EMAIL_FROM, to, fail_silently=False, html_message=log_txt)


def get_infringement_notice_coordinators():
    compliance_content_type = ContentType.objects.get(model="compliancepermissiongroup")
    permissions = Permission.objects.filter(codename='infringement_notice_coordinator',
                                            content_type_id=compliance_content_type.id)
    allowed_groups = CompliancePermissionGroup.objects.filter(permissions__in=permissions)
    members = []
    for group in allowed_groups.all():
        for member in group.members:
            members.append(member)
    return members

