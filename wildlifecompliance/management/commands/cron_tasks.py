from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
import subprocess
import logging
from wildlifecompliance.components.users.models import CompliancePermissionGroup

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the Wildlife Compliance Cron tasks'

    def handle(self, *args, **options):
        logger.info('Running command {}'.format(__name__))

        subprocess.call('python manage_wc.py verify_due_returns', shell=True)
        subprocess.call('python manage_wc.py verify_expired_licences', shell=True)
        subprocess.call('python manage_wc.py verify_licence_renewals', shell=True)
        subprocess.call('python manage_wc.py verify_species', shell=True)

        # subprocess.call('python manage_wc.py send_unpaid_infringements_file', shell=True)
        # subprocess.call('python manage_wc.py extend_due_date_from_1st_to_2nd', shell=True)
        # subprocess.call('python manage_wc.py send_rego_to_dot', shell=True)
        # subprocess.call('python manage_wc.py close_document_and_physical_artifacts', shell=True)
        # subprocess.call('python manage_wc.py notification_close_to_due_remediation_action', shell=True)
        # subprocess.call('python manage_wc.py notification_overdue_remediation_action', shell=True)

        logger.info('Command {} completed'.format(__name__))


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

