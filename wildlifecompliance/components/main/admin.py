from django.contrib import admin
#from ledger.accounts.models import EmailUser
from wildlifecompliance.components.main import models, forms
#from reversion.admin import VersionAdmin


@admin.register(models.GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']
    ordering = ('key',)


@admin.register(models.SystemMaintenance)
class SystemMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'start_date', 'end_date', 'duration']
    ordering = ('start_date',)
    readonly_fields = ('duration',)
    form = forms.SystemMaintenanceAdminForm
