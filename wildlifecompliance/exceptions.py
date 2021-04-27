from rest_framework.exceptions import APIException, PermissionDenied


class ApplicationNotAuthorized(PermissionDenied):
    default_detail = 'You are not authorised to work on this application'
    default_code = 'application_not_authorized'


class ApplicationNotComplete(APIException):
    status_code = 400
    default_detail = 'The application is not complete'
    default_code = 'application_incoplete'


class ApplicationMissingFields(APIException):
    status_code = 400
    default_detail = 'The application has missing required fields'
    default_code = 'application_missing_fields'


class BindApplicationException(Exception):
    pass


class SecureBaseException(Exception):
    '''
    A specialised exception object for securebase errors allowing for logging
    and auditing purposes.
    '''
    pass


class ApplicationServiceException(Exception):
    '''
    A specialised exception object for Services errors allowing for logging
    and auditing purposes.
    '''
    pass


class ApplicationPaymentException(Exception):
    '''
    A specialised exception object for Application Payment errors allowing for
    logging and auditing purposes.
    '''
    pass


class LicenceServiceException(Exception):
    '''
    A specialised exception object for Services errors allowing for logging
    and auditing purposes.
    '''
    pass


class ReturnServiceException(Exception):
    '''
    A specialised exception object for Services errors allowing for logging
    and auditing purposes.
    '''
    pass


class ReturnPaymentException(Exception):
    '''
    A specialised exception object for Return Payment errors allowing for
    logging and auditing purposes.
    '''
    pass

