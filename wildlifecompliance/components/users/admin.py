from django.contrib import admin
from wildlifecompliance.components.users import models
from wildlifecompliance.components.users import forms
from reversion.admin import VersionAdmin


#@admin.register(models.CompliancePermissionGroup)
#class CompliancePermissionGroupAdmin(admin.ModelAdmin):
#    list_display = ['name', 'display_name']
#    #filter_horizontal = ('region_district',)
#    form = forms.CompliancePermissionGroupAdminForm
#    readonly_fields = ('region', 'district')
#
#    def has_delete_permission(self, request, obj=None):
#        #return super(
#        #    CompliancePermissionGroupAdmin,
#        #    self).has_delete_permission(
#        #    request,
#        #    obj)
#
#        # disable delete
#        return False
#
#    def has_add_permission(self, request):
#        # disable add
#        return False
#
#    def get_actions(self, request):
#        actions = super().get_actions(request)
#        if 'delete_selected' in actions:
#            del actions['delete_selected']
#        return actions


@admin.register(models.ComplianceManagementUserPreferences)
class ComplianceManagementUserPreferencesAdmin(admin.ModelAdmin):
    pass
