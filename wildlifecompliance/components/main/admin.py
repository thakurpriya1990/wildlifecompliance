from django.contrib import admin
#from ledger.accounts.models import EmailUser
from wildlifecompliance.components.main import models
#from reversion.admin import VersionAdmin


@admin.register(models.GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']
    ordering = ('key',)
