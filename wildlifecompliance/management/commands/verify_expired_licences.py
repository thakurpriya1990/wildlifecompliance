from django.core.management.base import BaseCommand

import logging

from wildlifecompliance.components.licences.services import (
    LicenceService,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Vertification of licence purposes which have expired.'

    def handle(self, *args, **options):
        try:
            logger.info('Running command {}'.format(__name__))

            LicenceService.verify_expired_licences()

            logger.info('Command {} finished'.format(__name__))

        except Exception as e:
            print e
            logger.error('Error command {}'.format(__name__))
