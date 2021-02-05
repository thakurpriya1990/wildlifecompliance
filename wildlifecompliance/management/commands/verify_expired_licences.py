from django.core.management.base import BaseCommand

import logging

from wildlifecompliance.management.commands.emails import (
    CommandsVerifyNotificationEmail
)
from wildlifecompliance.components.licences.services import LicenceService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Vertification of licence purposes which have expired.'

    def handle(self, *args, **options):
        try:
            logger.info('Running command {}'.format(__name__))

            total = LicenceService.verify_expired_licences()

            email = CommandsVerifyNotificationEmail()
            email.set_verified_total(total)
            email.set_subject('verify_expired_licences ran successfully')
            email.out()

            logger.info('Command {} finished'.format(__name__))

        except Exception as e:
            logger.error('Error command {0} : {1}'.format(
                __name__, e))
