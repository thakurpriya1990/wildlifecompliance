from django.contrib import admin
from ledger.accounts.models import EmailUser
from wildlifecompliance.components.legal_case import models
from reversion.admin import VersionAdmin


@admin.register(models.Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    pass

