import logging

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.http import urlquote_plus

from wildlifecompliance.management.securebase_manager import (
    SecureBaseUtils,
    SecureAuthorisationEnforcer,
)

logger = logging.getLogger(__name__)
# logger = logging


class FirstTimeNagScreenMiddleware(object):
    '''
    Generic FirstTimeNagScreenMiddleware.
    '''
    def process_request(self, request):

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
