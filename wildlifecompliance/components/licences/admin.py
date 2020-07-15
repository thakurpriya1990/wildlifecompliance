from django.contrib import admin
from wildlifecompliance.components.licences import models


@admin.register(models.LicenceCategory)
class LicenceCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(models.LicenceActivity)
class LicenceActivityAdmin(admin.ModelAdmin):
    pass


@admin.register(models.WildlifeLicence)
class WildlifeLicence(admin.ModelAdmin):
    actions = ['verify_renewal_licence']

    def verify_renewal_licence(self, request, queryset):
        from wildlifecompliance.components.licences.services import (
            LicenceService,
        )
        for selected in queryset:
            LicenceService.verify_renewal_licence_for(selected.id, request)
        self.message_user(
            request, 'Selected licence renewal have been verified.')


@admin.register(models.LicencePurpose)
class LicencePurposeAdmin(admin.ModelAdmin):
    pass


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
        from wildlifecompliance.components.applications.services import (
            ApplicationService,
        )
        for selected in queryset:
            ApplicationService.verify_licence_specie_id(selected.specie_id)
        self.message_user(request, 'Selected species have been verified.')


@admin.register(models.WildlifeLicenceReceptionEmail)
class WildlifeLicenceReceptionEmailAdmin(admin.ModelAdmin):
    pass
