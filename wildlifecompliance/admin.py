from copy import deepcopy

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin
from ledger.accounts.models import EmailUser
from ledger.accounts import admin as ledger_admin


class WildlifeComplianceAdminSite(AdminSite):
    site_header = 'Wildlife Licensing System Administration'
    site_title = 'Wildlife Licensing System'


wildlifecompliance_admin_site = WildlifeComplianceAdminSite(name='wildlifecomplianceadmin')


admin.site.unregister(EmailUser)  # because this base classAdmin alsready registered in ledger.accounts.admin


@admin.register(EmailUser)
class EmailUserAdmin(ledger_admin.EmailUserAdmin):
    """
    Overriding the EmailUserAdmin from ledger.accounts.admin, to remove is_superuser checkbox field on Admin page
    """

    def get_fieldsets(self, request, obj=None):
        """ Remove the is_superuser checkbox from the Admin page, if user is NOT superuser """
        fieldsets = super(UserAdmin, self).get_fieldsets(request, obj)

        if request.user.is_superuser:
            return fieldsets

        # User is not a superuser, remove is_superuser checkbox
        fieldsets = deepcopy(fieldsets)
        for fieldset in fieldsets:
            if 'is_superuser' in fieldset[1]['fields']:
                if type(fieldset[1]['fields']) == tuple :
                    fieldset[1]['fields'] = list(fieldset[1]['fields'])
                fieldset[1]['fields'].remove('is_superuser')
                break

        return fieldsets