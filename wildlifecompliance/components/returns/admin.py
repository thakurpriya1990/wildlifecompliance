from django.contrib import admin
from wildlifecompliance.components.returns import models
from wildlifecompliance.components.returns.services import ReturnService
# Register your models here.


class RegulatedSpeciesInline(admin.TabularInline):
    extra = 0
    model = models.ReturnTypeRegulatedSpecies


@admin.register(models.ReturnType)
class ReturnTypeAdmin(admin.ModelAdmin):
    inlines = [
        RegulatedSpeciesInline,
    ]

    def get_inline_instances(self, request, obj=None):
        return [
            inline(self.model, self.admin_site) for inline in self.inlines
            if obj
            and obj.species_list == models.ReturnType.SPECIES_LIST_REGULATED
        ]


@admin.register(models.Return)
class ReturnAdmin(admin.ModelAdmin):
    actions = ['verify_due_returns']

    def verify_due_returns(self, request, queryset):
        '''
        Updates the processing status for selected returns.
        '''
        for selected in queryset:
            ReturnService.verify_due_return_id(selected.id)
        self.message_user(request, 'Selected returns have been verified.')


@admin.register(models.ReturnTable)
class ReturnTable(admin.ModelAdmin):
    pass


@admin.register(models.ReturnRow)
class ReturnRow(admin.ModelAdmin):
    pass


@admin.register(models.ReturnUserAction)
class ReturnUserActionAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ReturnLogEntry)
class ReturnLogEntryAdmin(admin.ModelAdmin):
    pass
