from django.contrib import admin
from ledger.accounts.models import EmailUser
from wildlifecompliance.components.artifact import models
from reversion.admin import VersionAdmin


@admin.register(models.Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    pass

@admin.register(models.DocumentArtifact)
class DocumentArtifactAdmin(admin.ModelAdmin):
    pass

@admin.register(models.PhysicalArtifact)
class PhysicalArtifactAdmin(admin.ModelAdmin):
    pass

@admin.register(models.DocumentArtifactType)
class DocumentArtifactTypeAdmin(admin.ModelAdmin):
    pass

@admin.register(models.PhysicalArtifactType)
class PhysicalArtifactTypeAdmin(admin.ModelAdmin):
    pass

@admin.register(models.PhysicalArtifactDisposalMethod)
class PhysicalArtifactDisposalMethodAdmin(admin.ModelAdmin):
    pass

