from django.core.management.base import BaseCommand

import logging

from wildlifecompliance.management.commands.emails import (
    CommandsVerifyNotificationEmail
)
from wildlifecompliance.components.applications.services import (
    ApplicationService,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Vertification of species existing on TSC server.'

    def handle(self, *args, **options):
        try:
            logger.info('Running command {}'.format(__name__))

            ApplicationService.verify_licence_species()

            notify = CommandsVerifyNotificationEmail()
            notify.set_verified_total(0)
            notify.set_subject('verify_species was executed.')
            notify.out()            

            logger.info('Command {} finished'.format(__name__))

        except Exception as e:
            logger.error('Error command {0} : {1}'.format(
                __name__, e))

