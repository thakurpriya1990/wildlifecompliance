import logging
import os

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.http import urlquote_plus
from django.conf import settings

from wildlifecompliance.management.securebase_manager import (
    SecureAuthorisationEnforcer
)

logger = logging.getLogger(__name__)
# logger = logging

class FirstTimeNagScreenMiddleware(object):
    '''
    Generic FirstTimeNagScreenMiddleware.
    '''
    def process_request(self, request):
        from wildlifecompliance.management.securebase_manager import (
            SecureBaseUtils
        )
        first_time_nag = FirstTimeDefaultNag()

        if SecureBaseUtils.is_wildlifelicensing_request(request):
            # Apply WildifeLicensing first-time checks.
            first_time_name = SecureAuthorisationEnforcer(request)

        return first_time_nag.process_request(request)


class FirstTimeDefaultNag(object):
    '''
    A specialised FirstTimeNagScreenMiddleware for non WildlifeLicensing.
    '''
    def process_request(self, request):
        if request.user.is_authenticated(
        ) and request.method == 'GET' and 'api' not in request.path and 'admin' not in request.path:
            #print('DEBUG: {}: {} == {}, {} == {}, {} == {}'.format(request.user, request.user.first_name, (not request.user.first_name), request.user.last_name, (not request.user.last_name), request.user.dob, (not request.user.dob) ))
            if (not request.user.first_name) or \
                    (not request.user.last_name) or \
                    (not request.user.dob) or \
                    (not request.user.residential_address) or \
                    (not (request.user.phone_number or request.user.mobile_number)):
                path_ft = reverse('first_time')
                path_logout = reverse('accounts:logout')
                request.session['new_to_wildlifecompliance'] = True
                if request.path not in (path_ft, path_logout):
                    return redirect(
                        reverse('first_time') +
                        "?next=" +
                        urlquote_plus(
                            request.get_full_path()))

