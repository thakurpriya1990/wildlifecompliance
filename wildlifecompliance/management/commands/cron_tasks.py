from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
import datetime

import subprocess

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the Wildlife Compliance Cron tasks'

    def handle(self, *args, **options):
        logger.info('Running command {}'.format(__name__))

        subprocess.call('python manage_wc.py send_unpaid_infringements_file', shell=True)
        # subprocess.call('python manage_wc.py extend_due_date_from_1st_to_2nd', shell=True)

        # TODO: Add another cron job so that the system is to remind the offende of an unpaid infringement notice after 28 days after issuing.

        logger.info('Command {} completed'.format(__name__))