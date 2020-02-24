import datetime
import logging
from django.core.urlresolvers import reverse
from django.conf import settings
from wildlifecompliance.components.emails.emails import TemplateEmailBase
from wildlifecompliance.components.main.email import prepare_attachments, _extract_email_headers
from wildlifecompliance.components.sanction_outcome.pdf import create_infringement_notice_pdf_bytes
from wildlifecompliance.components.sanction_outcome.pdf_caution_notice import create_caution_notice_pdf_bytes
from wildlifecompliance.components.sanction_outcome.pdf_in_blue import create_in_pdf_bytes
# from wildlifecompliance.components.sanction_outcome.serializers import SanctionOutcomeCommsLogEntrySerializer
from wildlifecompliance.components.sanction_outcome.pdf_letter_of_advice import create_letter_of_advice_pdf_bytes
from wildlifecompliance.components.sanction_outcome.pdf_prosecution_notice import create_prosecution_notice_pdf_bytes
from wildlifecompliance.components.sanction_outcome.pdf_remediation_notice import create_remediation_notice_pdf_bytes

logger = logging.getLogger(__name__)

SYSTEM_NAME = 'Wildlife Licensing Automated Message'


class SanctionOutcomeIssueNotificationEmail(TemplateEmailBase):
    subject = 'Issued Sanction Outcome'
    html_template = 'wildlifecompliance/emails/issue_sanction_outcome_notification.html'
    txt_template = 'wildlifecompliance/emails/issue_sanction_outcome_notification.txt'


class InfringementNoticeIssuedOnPaperEmail(TemplateEmailBase):
    subject = 'Endorsed Issued Infringement Notice'
    html_template = 'wildlifecompliance/emails/infringement_notice_issued_on_paper.html'
    txt_template = 'wildlifecompliance/emails/infringement_notice_issued_on_paper.txt'


class InfringementNoticeEmail(TemplateEmailBase):
    subject = 'Infringement Notice Issued'
    html_template = 'wildlifecompliance/emails/infringement_notice.html'
    txt_template = 'wildlifecompliance/emails/infringement_notice.txt'


class SendToIncWithoutOffendersMail(TemplateEmailBase):
    subject = 'Parking Infringement without offenders Forwarded'
    html_template = 'wildlifecompliance/emails/send_to_inc_without_offenders.html'
    txt_template = 'wildlifecompliance/emails/send_to_inc_without_offenders.txt'


class RemediationNoticeIssuedOnPaperEmail(TemplateEmailBase):
    subject = 'Endorsed Remediation Notice Issued'
    html_template = 'wildlifecompliance/emails/remediation_notice_issued_on_paper.html'
    txt_template = 'wildlifecompliance/emails/remediation_notice_issued_on_paper.txt'


class RemediationNoticeEmail(TemplateEmailBase):
    subject = 'Remediation Notice Issued'
    html_template = 'wildlifecompliance/emails/remediation_notice.html'
    txt_template = 'wildlifecompliance/emails/remediation_notice.txt'


class RemediationActionSubmittedMail(TemplateEmailBase):
    subject = 'Remediation Action Submitted'
    html_template = 'wildlifecompliance/emails/remediation_action_submitted.html'
    txt_template = 'wildlifecompliance/emails/remediation_action_submitted.txt'


class RemediationActionAcceptedMail(TemplateEmailBase):
    subject = 'Remediation Action Accepted'
    html_template = 'wildlifecompliance/emails/remediation_action_accepted.html'
    txt_template = 'wildlifecompliance/emails/remediation_action_accepted.txt'


class RemediationActionRequestAmendmentMail(TemplateEmailBase):
    subject = 'Request Amendment for Remediation Action'
    html_template = 'wildlifecompliance/emails/remediation_action_request_amendment.html'
    txt_template = 'wildlifecompliance/emails/remediation_action_request_amendment.txt'


class NotificationCloseToDueRemediationAction(TemplateEmailBase):
    subject = 'Reminder: Due Date is in one week'
    html_template = 'wildlifecompliance/emails/notification_close_to_due_remediation_action.html'
    txt_template = 'wildlifecompliance/emails/notification_close_to_due_remediation_action.txt'


class NotificationOverdueRemediationAction(TemplateEmailBase):
    subject = 'Reminder: Overdue'
    html_template = 'wildlifecompliance/emails/notification_overdue_remediation_action.html'
    txt_template = 'wildlifecompliance/emails/notification_overdue_remediation_action.txt'


class CautionNoticeEmail(TemplateEmailBase):
    subject = 'Caution Notice Issued'
    html_template = 'wildlifecompliance/emails/caution_notice.html'
    txt_template = 'wildlifecompliance/emails/caution_notice.txt'


class LetterOfAdviceEmail(TemplateEmailBase):
    subject = 'Letter of Advice Issued'
    html_template = 'wildlifecompliance/emails/letter_of_advice.html'
    txt_template = 'wildlifecompliance/emails/letter_of_advice.txt'


class ReturnToOfficerEmail(TemplateEmailBase):
    subject = 'Infringement Notice Returned'
    html_template = 'wildlifecompliance/emails/return_to_officer.html'
    txt_template = 'wildlifecompliance/emails/return_to_officer.txt'


class SendToManagerEmail(TemplateEmailBase):
    subject = 'Infringement Notice Fowarded'
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


class SendDetailsToDotEmail(TemplateEmailBase):
    subject = 'Details of Parking Infringement'
    html_template = 'wildlifecompliance/emails/send_details_to_dot.html'
    txt_template = 'wildlifecompliance/emails/send_details_to_dot.txt'


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
    pdf_file_name = 'infringement_notice_{}_{}.pdf'.format(sanction_outcome.lodgement_number, datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    document = create_infringement_notice_pdf_bytes(pdf_file_name, sanction_outcome)

    # Attach files (files from the modal, and the PDF file generated above)
    attachments = prepare_attachments(workflow_entry.documents)
    attachments.append((pdf_file_name, document._file.path, 'application/pdf'))

    # Attach the pdf file created above to the communication log entry
    doc = workflow_entry.documents.create(name=document.name)
    doc._file = document._file
    doc.save()

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc)
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)

    return email_data


def send_remind_1st_period_overdue_mail(to_address, sanction_outcome, workflow_entry, cc=None, bcc=None):
    email = Remind1stPeriodOverdueMail()
    # if request.data.get('email_subject'):
    #     email.subject = request.data.get('email_subject')
    # url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={ 'sanction_outcome_id': sanction_outcome.id }))
    context = {
        # 'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': 'This is message body.',
    }
    pdf_file_name = 'infringement_notice_{}_{}.pdf'.format(sanction_outcome.lodgement_number, datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    document = create_infringement_notice_pdf_bytes(pdf_file_name, sanction_outcome)

    attachments = []
    attachments.append((pdf_file_name, document._file.path, 'application/pdf'))

    # Attach the pdf file created above to the communication log entry
    doc = workflow_entry.documents.create(name=document.name)
    doc._file = document._file
    doc.save()

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc)
    sender = settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)

    return email_data


def send_unpaid_infringements_file(to_address, cc=None, bcc=None, attachments=[]):
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
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc)
    sender = settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)

    return email_data


def send_notification_overdue_remediation_action(to_address, sanction_outcome, cc=None, bcc=None, attachments=[]):
    email = NotificationOverdueRemediationAction()
    # if request.data.get('email_subject'):
    #     email.subject = request.data.get('email_subject')
    # url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={ 'sanction_outcome_id': sanction_outcome.id }))
    context = {
        # 'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': 'Remediation action is overdue.',
    }
    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc)
    sender = settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)

    return email_data


def send_notification_close_to_due_remediation_action(to_address, sanction_outcome, workflow_entry, cc=None, bcc=None, attachments=[]):
    email = NotificationCloseToDueRemediationAction()
    # if request.data.get('email_subject'):
    #     email.subject = request.data.get('email_subject')
    # url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={ 'sanction_outcome_id': sanction_outcome.id }))
    context = {
        # 'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': 'This is notification mail for the remediation notice.  Due date is in one week.',
    }
    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc)
    sender = settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)

    return email_data


def send_remediation_notice(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = RemediationNoticeEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('external'))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }

    pdf_file_name = 'remediation_notice_{}_{}.pdf'.format(sanction_outcome.lodgement_number, datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    document = create_infringement_notice_pdf_bytes(pdf_file_name, sanction_outcome)

    # Attach files (files from the modal, and the PDF file generated above)
    attachments = prepare_attachments(workflow_entry.documents)
    attachments.append((pdf_file_name, document._file.path, 'application/pdf'))

    # Attach the pdf file created above to the communication log entry
    doc = workflow_entry.documents.create(name=document.name)
    doc._file = document._file
    doc.save()

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_caution_notice(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = CautionNoticeEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('external'))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }

    pdf_file_name = 'caution_notice_{}_{}.pdf'.format(sanction_outcome.lodgement_number, datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    document = create_infringement_notice_pdf_bytes(pdf_file_name, sanction_outcome)

    # Attach files (files from the modal, and the PDF file generated above)
    attachments = prepare_attachments(workflow_entry.documents)
    attachments.append((pdf_file_name, document._file.path, 'application/pdf'))

    # Attach the pdf file created above to the communication log entry
    doc = workflow_entry.documents.create(name=document.name)
    doc._file = document._file
    doc.save()

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_letter_of_advice(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = LetterOfAdviceEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('external'))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }

    pdf_file_name = 'letter_of_advice_{}_{}.pdf'.format(sanction_outcome.lodgement_number, datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    document = create_infringement_notice_pdf_bytes(pdf_file_name, sanction_outcome)

    # Attach files (files from the modal, and the PDF file generated above)
    attachments = prepare_attachments(workflow_entry.documents)
    attachments.append((pdf_file_name, document._file.path, 'application/pdf'))

    # Attach the pdf file created above to the communication log entry
    doc = workflow_entry.documents.create(name=document.name)
    doc._file = document._file
    doc.save()

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_parking_infringement_without_offenders(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = SendToIncWithoutOffendersMail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={'sanction_outcome_id': sanction_outcome.id}))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }
    msg = email.send(to_address,
                     context=context,
                     attachments=prepare_attachments(workflow_entry.documents),
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_remediation_action_request_amendment_mail(to_address, remediation_action, request, cc=None, bcc=None):
    email = RemediationActionRequestAmendmentMail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('external'))
    context = {
        'url': url,
        'remediation_action': remediation_action,
        'amendment_requests': remediation_action.amendment_requests,
    }

    # Attach files (files from the modal, and the PDF file generated above)
    # attachments = prepare_attachments(remediation_action.documents)

    msg = email.send(to_address,
                     context=context,
                     attachments=[],
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_remediation_action_accepted_notice(to_address, remediation_action, request, cc=None, bcc=None):
    email = RemediationActionAcceptedMail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('external'))
    context = {
        'url': url,
        'remediation_action': remediation_action,
        'action_taken': remediation_action.action_taken,
    }

    # Attach files (files from the modal, and the PDF file generated above)
    # attachments = prepare_attachments(remediation_action.documents)

    msg = email.send(to_address,
                     context=context,
                     attachments=[],
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_remediation_action_submitted_notice(to_address, remediation_action, request, cc=None, bcc=None):
    email = RemediationActionSubmittedMail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('external'))
    context = {
        'url': url,
        'remediation_action': remediation_action,
        'action_taken': remediation_action.action_taken,
    }

    # Attach files (files from the modal, and the PDF file generated above)
    attachments = prepare_attachments(remediation_action.documents)

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data

def send_infringement_notice_issued_on_paper(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = InfringementNoticeIssuedOnPaperEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('external'))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }

    # Attach files (files from the modal, and the PDF file generated above)
    attachments = prepare_attachments(workflow_entry.documents)

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_remediation_notice_issued_on_paper(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = RemediationNoticeIssuedOnPaperEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('external'))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }

    # Attach files (files from the modal, and the PDF file generated above)
    attachments = prepare_attachments(workflow_entry.documents)

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
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

    pdf_file_name = 'infringement_notice_{}_{}.pdf'.format(sanction_outcome.lodgement_number, datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    # document = create_infringement_notice_pdf_bytes(pdf_file_name, sanction_outcome)
    # document = create_in_pdf_bytes(pdf_file_name, sanction_outcome)
    # document = create_prosecution_notice_pdf_bytes(pdf_file_name, sanction_outcome)
    # document = create_caution_notice_pdf_bytes(pdf_file_name, sanction_outcome)
    # document = create_remediation_notice_pdf_bytes(pdf_file_name, sanction_outcome)
    document = create_letter_of_advice_pdf_bytes(pdf_file_name, sanction_outcome)

    # Attach files (files from the modal, and the PDF file generated above)
    attachments = prepare_attachments(workflow_entry.documents)
    attachments.append((pdf_file_name, document._file.path, 'application/pdf'))

    # Attach the pdf file created above to the communication log entry
    doc = workflow_entry.documents.create(name=document.name)
    doc._file = document._file
    doc.save()

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def send_return_to_officer_email(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = ReturnToOfficerEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={'sanction_outcome_id': sanction_outcome.id}))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }

    # Attach files (files from the modal, and the PDF file generated above)
    attachments = prepare_attachments(workflow_entry.documents)

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data


def email_detais_to_department_of_transport(to_address, attachments, cc=None, bcc=None):
    email = SendDetailsToDotEmail()
    context = {
        # 'url': url,
        'workflow_entry_details': 'This is body for dot mail.',
    }
    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc,
                     )
    sender = settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)

    return email_data


def send_to_manager_email(to_address, sanction_outcome, workflow_entry, request, cc=None, bcc=None):
    email = SendToManagerEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={'sanction_outcome_id': sanction_outcome.id}))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }

    # Attach files (files from the modal, and the PDF file generated above)
    attachments = prepare_attachments(workflow_entry.documents)

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
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

    # Attach files (files from the modal, and the PDF file generated above)
    attachments = prepare_attachments(workflow_entry.documents)

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
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

    # Attach files (files from the modal, and the PDF file generated above)
    attachments = prepare_attachments(workflow_entry.documents)

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
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

    # Attach files (files from the modal, and the PDF file generated above)
    attachments = prepare_attachments(workflow_entry.documents)

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
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
    url = request.build_absolute_uri(reverse('internal-sanction-outcome-detail', kwargs={'sanction_outcome_id': sanction_outcome.id }))
    context = {
        'url': url,
        'sanction_outcome': sanction_outcome,
        'workflow_entry_details': request.data.get('details'),
    }

    # Attach files (files from the modal, and the PDF file generated above)
    attachments = prepare_attachments(workflow_entry.documents)

    msg = email.send(to_address,
                     context=context,
                     attachments=attachments,
                     cc=cc,
                     bcc=bcc,
                     )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data
