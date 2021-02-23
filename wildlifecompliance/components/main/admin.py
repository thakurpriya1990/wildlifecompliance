from django.contrib import admin
from wildlifecompliance.components.main import models, forms
from wildlifecompliance.components.main.models import SanctionOutcomeWordTemplate
from wildlifecompliance.components.main.utils import to_local_tz


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


@admin.register(SanctionOutcomeWordTemplate)
class SanctionOutcomeWordTemplateAdmin(admin.ModelAdmin):
    list_display = ('Version', '_file', 'description', 'Date', 'Time')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['_file', 'description', 'Date', 'Time']
        else:
            return []

    def Version(self, obj):
        return obj.id

    def Date(self, obj):
        local_date = to_local_tz(obj.uploaded_date)
        return local_date.strftime('%d/%m/%Y')

    def Time(self, obj):
        local_date = to_local_tz(obj.uploaded_date)
        return local_date.strftime('%H:%M')