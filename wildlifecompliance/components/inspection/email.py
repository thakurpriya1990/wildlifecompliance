import logging

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.encoding import smart_text
from django.core.urlresolvers import reverse
from django.conf import settings
from ledger.payments.pdf import create_invoice_pdf_bytes
from ledger.payments.models import Invoice
from wildlifecompliance.components.main.utils import get_choice_value
from wildlifecompliance.components.emails.emails import TemplateEmailBase
from wildlifecompliance.components.main.email import prepare_attachments, _extract_email_headers
import os

logger = logging.getLogger(__name__)

SYSTEM_NAME = 'Wildlife Licensing Automated Message'


class InspectionForwardNotificationEmail(TemplateEmailBase):
    subject = 'Forwarded Inspection'
    html_template = 'wildlifecompliance/emails/send_inspection_forward_notification.html'
    txt_template = 'wildlifecompliance/emails/send_inspection_forward_notification.txt'

class InspectionSendToManagerNotificationEmail(TemplateEmailBase):
    subject = 'Inspection sent to manager'
    html_template = 'wildlifecompliance/emails/send_inspection_to_manager_notification.html'
    txt_template = 'wildlifecompliance/emails/send_inspection_to_manager_notification.txt'

class InspectionRequestAmendmentNotificationEmail(TemplateEmailBase):
    subject = 'Amendment Requested'
    html_template = 'wildlifecompliance/emails/request_amendment_notification.html'
    txt_template = 'wildlifecompliance/emails/request_amendment_notification.txt'

class InspectionEndorseNotificationEmail(TemplateEmailBase):
    subject = 'Inspection Endorsed and Closed'
    html_template = 'wildlifecompliance/emails/endorse_inspection_notification.html'
    txt_template = 'wildlifecompliance/emails/endorse_inspection_notification.txt'

class InspectionNotificationEmail(TemplateEmailBase):
    subject = 'Inspection performed soon'
    html_template = 'wildlifecompliance/emails/inspection_notification.html'
    txt_template = 'wildlifecompliance/emails/inspection_notification.txt'


def send_mail(select_group, inspection, workflow_entry, request=None, email_type=None):
    if email_type == 'send_to_manager':
        email = InspectionSendToManagerNotificationEmail()
    elif email_type == 'request_amendment':
        email = InspectionRequestAmendmentNotificationEmail()
    elif email_type == 'endorse':
        email = InspectionEndorseNotificationEmail()
    else:
        # default is Inspection forward notification
        email = InspectionForwardNotificationEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(
        reverse(
            'internal-inspection-detail',
            kwargs={
                'inspection_id': inspection.id
                }))
    context = {
        'url': url,
        'inspection': inspection,
        'workflow_entry_details': request.data.get('details'),
    }
    email_group = [item.email for item in select_group]
    msg = email.send(email_group, 
        context=context,
        attachments= 
        prepare_attachments(workflow_entry.documents)
        )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_notification_of_inspection_email(to_address, cc=None, bcc=None, attachments=[]):
    email = InspectionNotificationEmail()
    # if request.data.get('email_subject'):
    #     email.subject = request.data.get('email_subject')
    # url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={ 'sanction_outcome_id': sanction_outcome.id }))
    context = {
        # 'url': url,
        # 'sanction_outcome': sanction_outcome,
        'workflow_entry_details': 'This is unpaid infringements message body.',
    }
    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc)
    sender = settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)

    return email_data
