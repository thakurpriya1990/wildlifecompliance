import logging
import traceback
from io import BytesIO

from django.core.files import File
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.encoding import smart_text
from django.core.urlresolvers import reverse
from django.conf import settings

from ledger.accounts.models import EmailUser
from ledger.payments.pdf import create_invoice_pdf_bytes
from ledger.payments.models import Invoice
from wildlifecompliance.components.main.utils import get_choice_value
from wildlifecompliance.components.emails.emails import TemplateEmailBase
from wildlifecompliance.components.main.email import prepare_attachments, _extract_email_headers
import os

from wildlifecompliance.components.sanction_outcome.models import SanctionOutcomeCommsLogDocument
from wildlifecompliance.components.sanction_outcome.pdf import create_infringement_notice_pdf_bytes
from wildlifecompliance.components.users.models import CompliancePermissionGroup

logger = logging.getLogger(__name__)

SYSTEM_NAME = 'Wildlife Licensing Automated Message'


class SanctionOutcomeIssueNotificationEmail(TemplateEmailBase):
    subject = 'Issued Sanction Outcome'
    html_template = 'wildlifecompliance/emails/issue_sanction_outcome_notification.html'
    txt_template = 'wildlifecompliance/emails/issue_sanction_outcome_notification.txt'


class InfringementNoticeEmail(TemplateEmailBase):
    subject = 'Infringement Notice Issued'
    html_template = 'wildlifecompliance/emails/infringement_notice.html'
    txt_template = 'wildlifecompliance/emails/infringement_notice.txt'


class ReturnToOfficerEmail(TemplateEmailBase):
    subject = 'Return to Officer'
    html_template = 'wildlifecompliance/emails/return_to_officer.html'
    txt_template = 'wildlifecompliance/emails/return_to_officer.txt'


class SendToManagerEmail(TemplateEmailBase):
    subject = 'Send to Manager'
    html_template = 'wildlifecompliance/emails/send_to_manager.html'
    txt_template = 'wildlifecompliance/emails/send_to_manager.txt'


class InfringementNoticeDueDateExtendedEmail(TemplateEmailBase):
    subject = 'Infringement notice due date extended'
    html_template = 'wildlifecompliance/emails/due_date_extended_email.html'
    txt_template = 'wildlifecompliance/emails/due_date_extended_email.txt'


class SendEscalateForWithdrawalEmail(TemplateEmailBase):
    subject = 'Infringement notice escalated for withdrawal'
    html_template = 'wildlifecompliance/emails/escalated_for_withdrawal_email.html'
    txt_template = 'wildlifecompliance/emails/escalated_for_withdrawal_email.txt'


class SendWithdrawByManagerEmail(TemplateEmailBase):
    subject = 'Infringement notice withdrawn'
    html_template = 'wildlifecompliance/emails/withdrawn_email.html'
    txt_template = 'wildlifecompliance/emails/withdrawn_email.txt'


class SendReturnToInfringementNoticeCoordinatorEmail(TemplateEmailBase):
    subject = 'Return infringement notice'
    html_template = 'wildlifecompliance/emails/return_to_infringement_notice_coordinator.html'
    txt_template = 'wildlifecompliance/emails/return_to_infringement_notice_coordinator.txt'


class SendDeclineEmail(TemplateEmailBase):
    subject = 'Infringement notice declined'
    html_template = 'wildlifecompliance/emails/decline_infringement_notice.html'
    txt_template = 'wildlifecompliance/emails/decline_infringement_notice.txt'


class Remind1stPeriodOverdueMail(TemplateEmailBase):
    """
    This is the template for the email sent when overdue the 1st period
    """
    subject = 'Infringement Notice overdue and extended'
    html_template = 'wildlifecompliance/emails/remind_1st_period_overdue.html'
    txt_template = 'wildlifecompliance/emails/remind_1st_period_overdue.txt'


class UnpaidInfringementsFileMail(TemplateEmailBase):
    subject = 'Unpaid Infringements File'
    html_template = 'wildlifecompliance/emails/unpaid_infringements_file.html'
    txt_template = 'wildlifecompliance/emails/unpaid_infringements_file.txt'


def send_due_date_extended_mail(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = InfringementNoticeDueDateExtendedEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={ 'sanction_outcome_id': sanction_outcome.id }))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }
    msg = email.send(to_address,
                     context=context,
                     attachments=prepare_attachments(workflow_entry.documents),
                     cc=cc,
                     bcc=bcc)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_remind_1st_period_overdue_mail(to_address, sanction_outcome, cc=None, bcc=None):
    email = Remind1stPeriodOverdueMail()
    # if request.data.get('email_subject'):
    #     email.subject = request.data.get('email_subject')
    # url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={ 'sanction_outcome_id': sanction_outcome.id }))
    context = {
        # 'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': 'This is message body.',
    }
    msg = email.send(to_address,
                     context=context,
                     cc=cc,
                     bcc=bcc)
    sender = settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_unpaid_infringements_file(to_address, cc=None, bcc=None, attachements=[]):
    email = UnpaidInfringementsFileMail()
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
                     # attachments=[('infringement_notice.pdf', pdf, 'application/pdf')],
                     attachments=attachements,
                     cc=cc,
                     bcc=bcc)
    sender = settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)


    return email_data


def send_infringement_notice(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = InfringementNoticeEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('external'))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }
    pdf_file_name = 'infringement_notice_{}.pdf'.format(sanction_outcome.lodgement_number)

    pdf = create_infringement_notice_pdf_bytes(pdf_file_name, sanction_outcome)
    msg = email.send(to_address,
                     context=context,
                     # attachments=prepare_attachments(workflow_entry.documents),
                     attachments=[('infringement_notice.pdf', pdf, 'application/pdf')],
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)

    # Create SanctionOutcomeCommsLogDocument object
    # so that the link to the infringement notice file can be created in the comms log
    temp = SanctionOutcomeCommsLogDocument(log_entry=workflow_entry, _file=File(BytesIO()), name=pdf_file_name)
    temp.save()

    return email_data


def send_return_to_officer_email(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = ReturnToOfficerEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={ 'sanction_outcome_id': sanction_outcome.id }))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }
    msg = email.send(to_address,
                     context=context,
                     attachments= prepare_attachments(workflow_entry.documents),
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def email_detais_to_department_of_transport(sanction_outcome):
    # TODO
    pass


def send_to_manager_email(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = SendToManagerEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={ 'sanction_outcome_id': sanction_outcome.id }))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }
    msg = email.send(to_address,
                     context=context,
                     attachments= prepare_attachments(workflow_entry.documents),
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_escalate_for_withdrawal_email(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = SendEscalateForWithdrawalEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={ 'sanction_outcome_id': sanction_outcome.id }))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }
    msg = email.send(to_address,
                     context=context,
                     attachments= prepare_attachments(workflow_entry.documents),
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_withdraw_by_manager_email(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = SendWithdrawByManagerEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={ 'sanction_outcome_id': sanction_outcome.id }))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }
    msg = email.send(to_address,
                     context=context,
                     attachments= prepare_attachments(workflow_entry.documents),
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_withdraw_by_branch_manager_email(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    return send_withdraw_by_manager_email(to_address, sanction_outcome, workflow_entry, request, cc, bcc)


def send_return_to_infringement_notice_coordinator_email(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = SendReturnToInfringementNoticeCoordinatorEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={ 'sanction_outcome_id': sanction_outcome.id }))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }
    msg = email.send(to_address,
                     context=context,
                     attachments= prepare_attachments(workflow_entry.documents),
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_decline_email(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = SendDeclineEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={ 'sanction_outcome_id': sanction_outcome.id }))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }
    msg = email.send(to_address,
                     context=context,
                     attachments= prepare_attachments(workflow_entry.documents),
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data
