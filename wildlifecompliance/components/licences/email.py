import logging
import mimetypes

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.encoding import smart_text
from django.core.urlresolvers import reverse
from django.conf import settings
from ledger.payments.pdf import create_invoice_pdf_bytes
from ledger.payments.models import Invoice
from wildlifecompliance.components.main.utils import get_choice_value
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
    url = request.build_absolute_uri(reverse('external'))

    context = {
        'licence': licence,
        'purposes': purposes,
        'url': url
    }
    recipients = [licence.current_application.submitter.email]
    email.send(recipients, context=context)
