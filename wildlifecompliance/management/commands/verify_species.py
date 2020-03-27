from django.core.management.base import BaseCommand

import logging

from wildlifecompliance.components.applications.services import (
    ApplicationService,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Extend original due date to 2nd due date'

    def handle(self, *args, **options):
        try:
            logger.info('Running command {}'.format(__name__))

            ApplicationService.verify_licence_species()

            logger.info('Command {} finished'.format(__name__))

        except Exception as e:
            print e
            logger.error('Error command {}'.format(__name__))
