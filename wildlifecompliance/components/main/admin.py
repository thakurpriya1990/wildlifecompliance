import logging
import abc

from django.contrib import admin
from django import forms as django_forms
from django.conf import settings
from wildlifecompliance.components.main import models, forms
from wildlifecompliance.components.main.models import SanctionOutcomeWordTemplate
from wildlifecompliance.components.main.utils import to_local_tz
#from reversion.admin import VersionAdmin
from ledger.accounts.models import EmailUser

logger = logging.getLogger(__name__)


class AdministrationAction(object):
    '''
    An abstract class for Adminstration Actions allowing for actions to be
    applied to a single object which can be accessed from either the change
    list view or the change form view.

    '''
    logger_title = 'AdministrationAction()'    # logger.
    request = None                              # property for client request.

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def do_action(self, row_ids=None) -> bool:
        '''
        Method to execute an Action from Administration on selected rows.
        '''
        pass

    @abc.abstractmethod
    def log_action(self) -> bool:
        '''
        Method to log this command action.
        '''
        pass


@admin.register(models.Region)
class RegionAdmin(admin.ModelAdmin):
    readonly_fields = ('head_office',)

    def has_delete_permission(self, request, obj=None):
        if obj and not obj.head_office:
            return True

@admin.register(models.District)
class DistrictAdmin(admin.ModelAdmin):
    pass


class ComplianceManagementGroupAdminFormTemplate(django_forms.ModelForm):

    class Meta:
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['region'].widget.can_add_related=False
            self.fields['region'].widget.can_change_related=False
            self.fields['region'].widget.can_delete_related=False
            self.fields['region'].required=False
            self.fields['district'].widget.can_add_related=False
            self.fields['district'].widget.can_change_related=False
            self.fields['district'].widget.can_delete_related=False
            self.fields['district'].required=False
            if self.instance.name in [
                settings.GROUP_VOLUNTEER,
                settings.GROUP_INFRINGEMENT_NOTICE_COORDINATOR,
                settings.GROUP_PROSECUTION_COORDINATOR,
                settings.GROUP_PROSECUTION_MANAGER,
                settings.GROUP_PROSECUTION_COUNCIL,
                settings.GROUP_COMPLIANCE_MANAGEMENT_READ_ONLY,
                settings.GROUP_COMPLIANCE_MANAGEMENT_CALL_EMAIL_READ_ONLY,
                settings.GROUP_COMPLIANCE_MANAGEMENT_APPROVED_EXTERNAL_USER,
                settings.GROUP_COMPLIANCE_ADMIN
                ]:
                self.fields['region'].disabled=True
                self.fields['district'].disabled=True


def ComplianceManagementPermissionTemplate(model_instance):
    class ComplianceManagementSystemGroupPermissionInline(admin.TabularInline):
        model = models.ComplianceManagementSystemGroupPermission
        extra = 0
        raw_id_fields = ('emailuser',)
        model_instance = None

        def __init__(self, *args, **kwargs):
            super(ComplianceManagementSystemGroupPermissionInline, self).__init__(*args, **kwargs)
            self.model_instance = model_instance

        #def formfield_for_foreignkey(self, db_field, request, **kwargs):
        #    if self.model_instance.name == settings.GROUP_COMPLIANCE_MANAGEMENT_APPROVED_EXTERNAL_USER and db_field.name == "emailuser":
        #        print("external")
        #        print(EmailUser.objects.filter(is_staff=False).count())
        #        kwargs["queryset"] = EmailUser.objects.filter(is_staff=False)
        #    elif db_field.name == "emailuser":
        #        print("internal")
        #        print(EmailUser.objects.filter(is_staff=True).count())
        #        kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
        #    return super(ComplianceManagementSystemGroupPermissionInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    return ComplianceManagementSystemGroupPermissionInline


@admin.register(models.ComplianceManagementSystemGroup)
class ComplianceManagementSystemGroupAdmin(admin.ModelAdmin):
    list_display = ('id','name','region', 'district')
    #inlines = [ComplianceManagementPermissionTemplate(self)]
    #inlines = [ComplianceManagementAdminTemplate("what what")]
    form = ComplianceManagementGroupAdminFormTemplate

    def get_inline_instances(self, request, obj=None):
        return [
                ComplianceManagementPermissionTemplate(obj)(self.model, self.admin_site),
                ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "district":
            kwargs["required"] = False
        if db_field.name == "region":
            kwargs["required"] = False
        return super(ComplianceManagementSystemGroupAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(models.GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']
    ordering = ('key',)


@admin.register(models.SystemMaintenance)
class SystemMaintenanceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'description', 'start_date', 'end_date', 'duration'
    ]
    ordering = ('start_date',)
    readonly_fields = ('duration',)
    form = forms.SystemMaintenanceAdminForm


@admin.register(SanctionOutcomeWordTemplate)
class SanctionOutcomeWordTemplateAdmin(admin.ModelAdmin):
    list_display = ('Version', '_file', 'sanction_outcome_type', 'act', 'description', 'Date', 'Time')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['_file', 'description', 'Date', 'Time']
        else:
            return []

    def Version(self, obj):
        return obj.id

    def Date(self, obj):
        local_date = to_local_tz(obj.uploaded_date)
        return local_date.strftime('%d/%m/%Y')

    def Time(self, obj):
        local_date = to_local_tz(obj.uploaded_date)
        return local_date.strftime('%H:%M')
