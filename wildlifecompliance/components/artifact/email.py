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


class ArtifactAwaitingDisposalNotificationEmail(TemplateEmailBase):
    subject = 'Object awaiting disposal'
    html_template = 'wildlifecompliance/emails/send_awaiting_disposal_notification.html'
    txt_template = 'wildlifecompliance/emails/send_awaiting_disposal_notification.txt'


def send_mail(select_group, artifact, request=None, recipient_address=None):
    email = ArtifactAwaitingDisposalNotificationEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(
        reverse(
            'internal-artifact-detail',
            kwargs={
                'artifact_id': artifact.id
                }))
    context = {
        'url': url,
        'artifact': artifact,
        #'workflow_entry_details': request.data.get('details'),
        'details': request.data.get('details'),
    }
    email_group = None
    if recipient_address:
        email_group = [recipient_address,]
    # if there is no recipient address (custodian), send the email to the request.user
    elif request and request.user and request.user.email:
        email_group = [request.user.email,]
    msg = email.send(email_group, 
        context=context,
        #attachments= 
        #prepare_attachments(workflow_entry.documents)
        )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data

