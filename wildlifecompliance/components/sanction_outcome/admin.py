from django.contrib import admin

from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome
from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDateConfiguration


@admin.register(SanctionOutcome)
class SanctionOutcomeAdmin(admin.ModelAdmin):
    filter_horizontal = ('alleged_offences',)


@admin.register(SanctionOutcomeDueDateConfiguration)
class SanctionOutcomeDueDateConfigurationAdmin(admin.ModelAdmin):
    pass

