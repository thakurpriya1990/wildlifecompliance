from django.core.management.base import BaseCommand

import logging

from wildlifecompliance.management.commands.emails import (
    CommandsVerifyNotificationEmail
)
from wildlifecompliance.components.licences.services import (
    LicenceService,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Vertification of licence purposes which require renewal.'

    def handle(self, *args, **options):
        try:
            logger.info('Running command {}'.format(__name__))

            total = LicenceService.verify_licence_renewals()

            notify = CommandsVerifyNotificationEmail()
            notify.set_verified_total(total)
            notify.set_subject('verified_licence_renewals ran successfully')
            notify.out()

            logger.info('Command {} finished'.format(__name__))

        except Exception as e:
            logger.error('Error command {0} : {1}'.format(
                __name__, e))

