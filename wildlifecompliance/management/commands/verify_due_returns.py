from django.core.management.base import BaseCommand

import logging

from wildlifecompliance.management.commands.emails import (
    CommandsVerifyNotificationEmail
)
from wildlifecompliance.components.returns.services import (
    ReturnService,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Vertification of return due date seven days before it is due.'

    def handle(self, *args, **options):
        try:
            logger.info('Running command {}'.format(__name__))

            total = ReturnService.verify_due_returns()

            notify = CommandsVerifyNotificationEmail()
            notify.set_verified_total(total)
            notify.set_subject('verify_due_returns ran successfully')
            notify.out()

            logger.info('Command {} finished'.format(__name__))

        except Exception as e:
            logger.error('Error command {0} : {1}'.format(
                __name__, e))
