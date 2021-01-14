from django.core.management.base import BaseCommand

import logging

from wildlifecompliance.components.licences.services import (
    LicenceService,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Vertification of licence purposes which require renewal.'

    def handle(self, *args, **options):
        try:
            logger.info('Running command {}'.format(__name__))

            LicenceService.verify_licence_renewals()

            logger.info('Command {} finished'.format(__name__))

        except Exception as e:
            logger.error('Error command {0} : {1}'.format(
                __name__, e))

