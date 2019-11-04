from django.contrib import admin

from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, SanctionOutcomeDueDateConfiguration


@admin.register(SanctionOutcome)
class SanctionOutcomeAdmin(admin.ModelAdmin):
    filter_horizontal = ('alleged_offences',)


@admin.register(SanctionOutcomeDueDateConfiguration)
class SanctionOutcomeDueDateConfigurationAdmin(admin.ModelAdmin):
    pass

