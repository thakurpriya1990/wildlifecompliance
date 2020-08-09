import logging

from django.core.urlresolvers import reverse

from wildlifecompliance.components.main.utils import (
    remove_url_internal_request,
)

from wildlifecompliance.components.emails.emails import TemplateEmailBase

logger = logging.getLogger(__name__)

SYSTEM_NAME = 'Wildlife Licensing Automated Message'


class LicenceRenewalNotificationEmail(TemplateEmailBase):
    '''
    Email template for licence renewal notifications.
    '''
    subject = 'Your licence is due for renewal'
    html_template = \
        'wildlifecompliance/emails/send_licence_renewal_notification.html'
    txt_template = \
        'wildlifecompliance/emails/send_licence_renewal_notification.txt'


def send_licence_renewal_notification(licence, purposes, request=None):
    '''
    Sender function for licence renewal notification.
    '''
    email = LicenceRenewalNotificationEmail()
    # url = request.build_absolute_uri(reverse('external'))
    url = ''

    context = {
        'licence': licence,
        'purposes': purposes,
        'url': url
    }
    recipients = [licence.current_application.submitter.email]
    email.send(recipients, context=context)


class LicenceSurrenderNotificationEmail(TemplateEmailBase):
    '''
    Email template for licence surrender notifications.
    '''
    subject = 'Your licence has been surrendered.'
    html_template = \
        'wildlifecompliance/emails/send_licence_surrender_notification.html'
    txt_template = \
        'wildlifecompliance/emails/send_licence_surrender_notification.txt'


def send_licence_surrender_notification(licence, purposes, request=None):
    '''
    Sender function for licence surrender notification.
    '''
    email = LicenceSurrenderNotificationEmail()
    url = request.build_absolute_uri(reverse('external'))

    context = {
        'licence': licence,
        'purposes': purposes,
        'url': remove_url_internal_request(request, url)
    }
    recipients = [licence.current_application.submitter.email]
    email.send(recipients, context=context)


class LicenceCancelNotificationEmail(TemplateEmailBase):
    '''
    Email template for licence cancel notifications.
    '''
    subject = 'Your licence has been cancelled.'
    html_template = \
        'wildlifecompliance/emails/send_licence_cancel_notification.html'
    txt_template = \
        'wildlifecompliance/emails/send_licence_cancel_notification.txt'


def send_licence_cancel_notification(licence, purposes, request=None):
    '''
    Sender function for licence cancel notification.
    '''
    email = LicenceCancelNotificationEmail()
    url = request.build_absolute_uri(reverse('external'))

    context = {
        'licence': licence,
        'purposes': purposes,
        'url': remove_url_internal_request(request, url)
    }
    recipients = [licence.current_application.submitter.email]
    email.send(recipients, context=context)


class LicenceSuspendNotificationEmail(TemplateEmailBase):
    '''
    Email template for licence suspend notifications.
    '''
    subject = 'Your licence has been suspended.'
    html_template = \
        'wildlifecompliance/emails/send_licence_suspend_notification.html'
    txt_template = \
        'wildlifecompliance/emails/send_licence_suspend_notification.txt'


def send_licence_suspend_notification(licence, purposes, request=None):
    '''
    Sender function for licence suspend notification.
    '''
    email = LicenceSuspendNotificationEmail()
    url = request.build_absolute_uri(reverse('external'))

    context = {
        'licence': licence,
        'purposes': purposes,
        'url': remove_url_internal_request(request, url)
    }
    recipients = [licence.current_application.submitter.email]
    email.send(recipients, context=context)


class LicenceReinstateNotificationEmail(TemplateEmailBase):
    '''
    Email template for licence reinstate notifications.
    '''
    subject = 'Your licence has been reinstated.'
    html_template = \
        'wildlifecompliance/emails/send_licence_reinstate_notification.html'
    txt_template = \
        'wildlifecompliance/emails/send_licence_reinstate_notification.txt'


def send_licence_reinstate_notification(licence, purposes, request=None):
    '''
    Sender function for licence reinstate notification.
    '''
    email = LicenceReinstateNotificationEmail()
    url = request.build_absolute_uri(reverse('external'))

    context = {
        'licence': licence,
        'purposes': purposes,
        'url': remove_url_internal_request(request, url)
    }
    recipients = [licence.current_application.submitter.email]
    email.send(recipients, context=context)
