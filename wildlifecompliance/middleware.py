import logging

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.http import urlquote_plus

from wildlifecompliance.management.securebase_manager import (
    SecureBaseUtils,
    SecureAuthorisationEnforcer,
)
from wildlifecompliance.components.users.models import ComplianceManagementUserPreferences, CompliancePermissionGroup
from wildlifecompliance.helpers import (
        is_compliance_management_callemail_readonly_user, 
        is_compliance_management_approved_external_user,
        is_compliance_management_volunteer,
        )

logger = logging.getLogger(__name__)
# logger = logging


class FirstTimeNagScreenMiddleware(object):
    '''
    Generic FirstTimeNagScreenMiddleware.
    '''
    def process_request(self, request):
        if request.method == 'GET' and request.user.is_authenticated(
        ) and 'api' not in request.path and 'admin' not in request.path:
            # add CM Approved External users to CallEmail RO and volunteer groups
            if is_compliance_management_approved_external_user(request):
                if not is_compliance_management_callemail_readonly_user(request):
                    compliance_group = CompliancePermissionGroup.objects.get(permissions__codename='compliance_management_callemail_readonly')
                    compliance_group.user_set.add(request.user)
                if not is_compliance_management_volunteer(request):
                    compliance_group = CompliancePermissionGroup.objects.get(permissions__codename='volunteer')
                    compliance_group.user_set.add(request.user)
            # Ensure CallEmail RO group users have prefer_compliance_management=True
            preference, created = ComplianceManagementUserPreferences.objects.get_or_create(email_user=request.user)
            if is_compliance_management_callemail_readonly_user(request) and not preference.prefer_compliance_management:
                preference.prefer_compliance_management = True
                preference.save()

        if SecureBaseUtils.is_wildlifelicensing_request(request):
            # Apply WildifeLicensing first-time checks.
            first_time_nag = SecureAuthorisationEnforcer(request)

        else:
            first_time_nag = FirstTimeDefaultNag()

        return first_time_nag.process_request(request)


class FirstTimeDefaultNag(object):
    '''
    A specialised FirstTimeNagScreenMiddleware for non WildlifeLicensing.
    '''
    def process_request(self, request):
        if request.method == 'GET' and request.user.is_authenticated(
        ) and 'api' not in request.path and 'admin' not in request.path:

            if (not request.user.first_name) or \
                    (not request.user.last_name) or \
                    (not request.user.dob) or \
                    (not request.user.residential_address) or \
                    (not (
                        request.user.phone_number or request.user.mobile_number
                    )):
                path_ft = reverse('first_time')
                path_logout = reverse('accounts:logout')
                request.session['new_to_wildlifecompliance'] = True
                if request.path not in (path_ft, path_logout):
                    return redirect(
                        reverse('first_time') +
                        "?next=" +
                        urlquote_plus(
                            request.get_full_path()))


class CacheControlMiddleware(object):
    def process_response(self, request, response):
        if request.path[:5] == '/api/' or request.path == '/':
            response['Cache-Control'] = 'private, no-store'
        elif request.path[:8] == '/static/':
            response['Cache-Control'] = 'public, max-age=86400'
        return response

