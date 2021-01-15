from django.core.management.base import BaseCommand

import logging

from wildlifecompliance.components.returns.services import (
    ReturnService,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Vertification of return due date seven days before it is due.'

    def handle(self, *args, **options):
        try:
            logger.info('Running command {}'.format(__name__))

            ReturnService.verify_due_returns()

            logger.info('Command {} finished'.format(__name__))

        except Exception as e:
            logger.error('Error command {0} : {1}'.format(
                __name__, e))
