from django.contrib import admin
from ledger.accounts.models import EmailUser
from wildlifecompliance.components.licences import models
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
        'specie_id',
        'verify_date',
        'verify_id',
        'verify_token',
        'data']
