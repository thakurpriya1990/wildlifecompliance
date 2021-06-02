import logging
import abc

from django.contrib import admin
from wildlifecompliance.components.main import models, forms

logger = logging.getLogger(__name__)


class AdministrationAction(object):
    '''
    An abstract class for Adminstration Actions allowing for actions to be
    applied to a single object which can be accessed from either the change
    list view or the change form view.

    '''
    logger_title = 'AdministrationAction()'    # logger.
    request = None                              # property for client request.

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def do_action(self, row_ids=None) -> bool:
        '''
        Method to execute an Action from Administration on selected rows.
        '''
        pass

    @abc.abstractmethod
    def log_action(self) -> bool:
        '''
        Method to log this command action.
        '''
        pass


@admin.register(models.GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']
    ordering = ('key',)


@admin.register(models.SystemMaintenance)
class SystemMaintenanceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'description', 'start_date', 'end_date', 'duration'
    ]
    ordering = ('start_date',)
    readonly_fields = ('duration',)
    form = forms.SystemMaintenanceAdminForm
