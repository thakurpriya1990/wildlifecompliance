import abc
import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.http import urlquote_plus

from wildlifecompliance.exceptions import SecureBaseException

logger = logging.getLogger('securebase_manager')
# logger = logging


class SecureBase(object):
    '''
    An abstract base class to coordinate security components and to provide a 
    client request with a central access point for administering security 
    related functionality.
    '''
    request = None                              # composite client request.
    allow_request = False                       # privileged request flag.

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def validate_request(self):
        '''
        Method responsible for validating the client request checking for known
        vulnerabilities.
        '''

    @abc.abstractmethod
    def log_request(self, meesage):
        '''
        Method to securely log events and related data for auditing and for
        forensic purposes.

        :param: message string to be logged.
        '''


class SecureAuthorisationEnforcer(SecureBase):
    '''
    A SecureBase object to generically (interception) enforce an authorisation
    policy onto a client request.
    '''
    def __init__(self, a_request):
        super(SecureBase, self).__init__()
        self.request = a_request    

    def __str__(self):
        return 'SecureAuthrorisationEnforcer - user: {0}'.format(
            self.request.user.email
        )

    def validate_request(self):
        '''
        super.validate_request(self)
        '''
        pass

    def log_request(self, message):
        '''
        super.log_request(self, message)
        '''
        pass

    def process_request(self):
        '''
        Process a privileged request.
        '''
        from wildlifecompliance.helpers import is_new_to_wildlifelicensing

        if self.request.method == 'GET' and 'api' not in self.request.path \
        and 'admin' not in self.request.path \
        and self.request.user.is_authenticated():

            if is_new_to_wildlifelicensing(self.request):
                path_ft = reverse('first_time')
                path_logout = reverse('accounts:logout')
                self.request.session['new_to_wildlifecompliance'] = True
                if self.request.path not in (path_ft, path_logout):
                    return redirect(
                        reverse('first_time') +
                        "?next=" +
                        urlquote_plus(
                            self.request.get_full_path()))


class SecurePipe(SecureBase):
    '''
    A SecureBase object to provide a simple and standardised way to protect
    data sent across a network from a client request.
    '''
    def __init__(self, a_request):
        super(SecureBase, self).__init__()
        self.request = a_request

    def __str__(self):
        return 'LoginID: {0}'.format(self.request.user.email)

    def validate_request(self):
        '''
        super.validate_request(self)
        '''
        from wildlifecompliance.helpers import is_wildlifelicensing_request

        self.allow_request = True

        '''
        0. Check request is from an authenticated user.
        '''
        if not self.request.user.is_authenticated():
            self.allow_request = False
            message = '{0} - {1} Not Authenticated.'.format(
                self,
                'SecurePipe.validate_request()',
            )
            raise SecureBaseException(message)


    def validate_request_for_wildlifelicence(self, licence):
        '''
        Method responsible for validating the client request for wildife
        licensing checking for known vulnerabilities.
        '''
        from wildlifecompliance.helpers import is_customer

        self.allow_request = True
        apps = licence.current_application
        user = self.request.user

        '''
        1. Check request user has permission for licence.
        '''
        if is_customer(self.request):

            customer_is_org_applicant = True \
            if apps.org_applicant and apps.org_applicant == user else False

            customer_is_proxy_applicant = True \
            if apps.proxy_applicant and apps.proxy_applicant == user else False 

            customer_is_submitter = True \
            if apps.submitter and apps.submitter == user else False 

            if not customer_is_proxy_applicant and not customer_is_submitter \
            and not customer_is_org_applicant:

                self.allow_request = False
                message = '{0} - {1} {2} No Permission.'.format(
                    self,
                    'SecurePipe.validate_request_for_wildlifelicence(licence)',
                    licence.licence_number,
                )
                raise SecureBaseException(message)

    def log_request(self, message):
        '''
        super.log_request(self, message)
        '''
        logger.info(message)

    def get_http_response(self):
        '''
        Gets a http response for a client request that has been allowed.

        :return: HttpResponse for a client request.
        '''
        from wildlifecompliance.helpers import is_wildlifelicensing_request

        response = HttpResponse()

        try:
            self.validate_request()

            if is_wildlifelicensing_request(self.request):
                response = self.get_http_response_for_wildlifelicensing()

        except SecureBaseException as e:
            self.log_request(e)

        except Exception as e:
            raise

        return response

    def get_http_response_for_wildlifelicensing(self):
        '''
        Gets a http response specifically for a wildlife licensing request that
        has been allowed.

        :return: HttpResponse for a client request.
        '''
        import mimetypes
        from wildlifecompliance.components.applications.models import (
            Application,
        )
        from wildlifecompliance.components.licences.models import (
            WildlifeLicence,
        )
        logger.debug('SecurePipe.get_http_response_for_wlc() - start')

        response = HttpResponse()
        request_user_id = self.request.POST.get('user_id', None)
        request_licence_id = self.request.POST.get('licence_id', None)

        try:
            if request_user_id:
                document = self.request.user.identification
                mime = mimetypes.guess_type(document.filename)[0]

                response = HttpResponse(content_type=mime)
                response.write(document.file.read())

            elif request_licence_id:
                licence = WildlifeLicence.objects.get(
                    id=int(request_licence_id)
                )

                self.validate_request_for_wildlifelicence(licence)
                document = licence.licence_document
                mime = mimetypes.guess_type(document._file.name)[0]

                response = HttpResponse(content_type=mime)
                response.write(document._file.read())

        except SecureBaseException as e:
            raise

        except Exception as e:
            logger.error('{0} : {1}'.format(
               'securebase_manager.SecurePipe.get_http_response_for_wlc()',
                e
            ))
            raise

        logger.debug('SecurePipe.get_http_response_for_wlc() - end')
        return response
