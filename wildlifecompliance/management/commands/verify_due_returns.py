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
        errors = []
        updates = []
        try:
            logger.info('Running command {}'.format(__name__))

            updates = ReturnService.verify_due_returns()

            logger.info('Command {} finished'.format(__name__))

        except Exception as e:
            logger.error('Error command {0} : {1}'.format(
                __name__, e))
            errors.append(e)

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        err_str = '<strong style="color: red;">Errors: {}</strong>'.format(
            len(errors)
        ) if len(errors)>0 else '<strong style="color: green;">Errors: 0</strong>'
        msg = '<p>{} completed. {}. IDs updated: {}.</p>'.format(
            cmd_name, err_str, updates
        )
        logger.info(msg)
        print(msg) # will redirect to cron_tasks.log file, by the parent script