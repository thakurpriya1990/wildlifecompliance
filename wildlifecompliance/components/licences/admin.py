from django.contrib import admin
from wildlifecompliance.components.licences import models
from wildlifecompliance.components.applications.services import (
    ApplicationService
)
# Register your models here.


@admin.register(models.LicenceCategory)
class LicenceCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(models.LicenceActivity)
class LicenceActivityAdmin(admin.ModelAdmin):
    pass


@admin.register(models.WildlifeLicence)
class WildlifeLicence(admin.ModelAdmin):
    pass


@admin.register(models.LicencePurpose)
class LicencePurposeAdmin(admin.ModelAdmin):
    pass


@admin.register(models.LicencePurposeDetail)
class LicencePurposeDetailAdmin(admin.ModelAdmin):
    list_display = ['detail', 'purpose', 'index']


@admin.register(models.LicenceSpecies)
class LicenceSpeciesAdmin(admin.ModelAdmin):
    list_display = [
        'specie_id',
        'verify_date']
    readonly_fields = [
        'verify_date',
        'verify_id',
        'verify_token',
        'data']
    actions = ['verify_species']

    def verify_species(self, request, queryset):
        for selected in queryset:
            ApplicationService.verify_licence_specie_id(selected.specie_id)
        self.message_user(request, 'Selected species have been verified.')
