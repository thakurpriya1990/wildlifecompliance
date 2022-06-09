import logging
import abc

from django.contrib import admin
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

@admin.register(models.CallEmailTriageGroup)
class CallEmailTriageGroupAdmin(admin.ModelAdmin):
    #list_display = ['name', 'region_name', 'district_name' ]
    filter_horizontal = ('members',)
    form = forms.CallEmailTriageGroupAdminForm

@admin.register(models.OfficerGroup)
class OfficerGroupAdmin(admin.ModelAdmin):
    #list_display = ['name', 'region_name', 'district_name' ]
    filter_horizontal = ('members',)
    form = forms.OfficerGroupAdminForm

@admin.register(models.ManagerGroup)
class ManagerGroupAdmin(admin.ModelAdmin):
    #list_display = ['name', 'region_name', 'district_name' ]
    filter_horizontal = ('members',)
    form = forms.ManagerGroupAdminForm


@admin.register(models.VolunteerGroup)
class VolunteerGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)
    actions = None

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            #kwargs["queryset"] = EmailUser.objects.filter(email__icontains='@dbca.wa.gov.au')
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
            kwargs["required"] = False
        return super(VolunteerGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return True if models.VolunteerGroup.objects.count() == 0 else False

    def has_delete_permission(self, request, obj=None):
        return False 


@admin.register(models.InfringementNoticeCoordinatorGroup)
class InfringementNoticeCoordinatorGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)
    actions = None

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            #kwargs["queryset"] = EmailUser.objects.filter(email__icontains='@dbca.wa.gov.au')
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
            kwargs["required"] = False
        return super(InfringementNoticeCoordinatorGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return True if models.InfringementNoticeCoordinatorGroup.objects.count() == 0 else False

    def has_delete_permission(self, request, obj=None):
        return False 

@admin.register(models.ProsecutionCoordinatorGroup)
class ProsecutionCoordinatorGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)
    actions = None

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            #kwargs["queryset"] = EmailUser.objects.filter(email__icontains='@dbca.wa.gov.au')
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
            kwargs["required"] = False
        return super(ProsecutionCoordinatorGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return True if models.ProsecutionCoordinatorGroup.objects.count() == 0 else False

    def has_delete_permission(self, request, obj=None):
        return False 

@admin.register(models.ProsecutionManagerGroup)
class ProsecutionManagerGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)
    actions = None

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            #kwargs["queryset"] = EmailUser.objects.filter(email__icontains='@dbca.wa.gov.au')
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
            kwargs["required"] = False
        return super(ProsecutionManagerGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return True if models.ProsecutionManagerGroup.objects.count() == 0 else False

    def has_delete_permission(self, request, obj=None):
        return False 

@admin.register(models.ProsecutionCouncilGroup)
class ProsecutionCouncilGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)
    actions = None

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            #kwargs["queryset"] = EmailUser.objects.filter(email__icontains='@dbca.wa.gov.au')
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
            kwargs["required"] = False
        return super(ProsecutionCouncilGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return True if models.ProsecutionCouncilGroup.objects.count() == 0 else False

    def has_delete_permission(self, request, obj=None):
        return False 

@admin.register(models.ComplianceManagementReadOnlyGroup)
class ComplianceManagementReadOnlyGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)
    actions = None

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            #kwargs["queryset"] = EmailUser.objects.filter(email__icontains='@dbca.wa.gov.au')
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
            kwargs["required"] = False
        return super(ComplianceManagementReadOnlyGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return True if models.ComplianceManagementReadOnlyGroup.objects.count() == 0 else False

    def has_delete_permission(self, request, obj=None):
        return False 

@admin.register(models.ComplianceManagementCallEmailReadOnlyGroup)
class ComplianceManagementCallEmailReadOnlyGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)
    actions = None

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            #kwargs["queryset"] = EmailUser.objects.filter(email__icontains='@dbca.wa.gov.au')
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
            kwargs["required"] = False
        return super(ComplianceManagementCallEmailReadOnlyGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return True if models.ComplianceManagementCallEmailReadOnlyGroup.objects.count() == 0 else False

    def has_delete_permission(self, request, obj=None):
        return False 

@admin.register(models.ComplianceManagementApprovedExternalUserGroup)
class ComplianceManagementApprovedExternalUserGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)
    actions = None

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            #kwargs["queryset"] = EmailUser.objects.filter(email__icontains='@dbca.wa.gov.au')
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
            kwargs["required"] = False
        return super(ComplianceManagementApprovedExternalUserGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return True if models.ComplianceManagementApprovedExternalUserGroup.objects.count() == 0 else False

    def has_delete_permission(self, request, obj=None):
        return False 


@admin.register(models.ComplianceAdminGroup)
class ComplianceAdminGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)
    actions = None

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            #kwargs["queryset"] = EmailUser.objects.filter(email__icontains='@dbca.wa.gov.au')
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
            kwargs["required"] = False
        return super(ComplianceAdminGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return True if models.ComplianceAdminGroup.objects.count() == 0 else False

    def has_delete_permission(self, request, obj=None):
        return False 


@admin.register(models.LicensingAdminGroup)
class LicensingGroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)
    actions = None

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            #kwargs["queryset"] = EmailUser.objects.filter(email__icontains='@dbca.wa.gov.au')
            kwargs["queryset"] = EmailUser.objects.filter(is_staff=True)
            kwargs["required"] = False
        return super(LicensingAdminGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def has_add_permission(self, request):
        return True if models.LicensingAdminGroup.objects.count() == 0 else False

    def has_delete_permission(self, request, obj=None):
        return False 


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
