from django.contrib import admin
from wildlifecompliance.components.returns import models
from wildlifecompliance.components.returns.services import ReturnService
# Register your models here.


@admin.register(models.ReturnType)
class ReturnTypeAdmin(admin.ModelAdmin):
    pass


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
