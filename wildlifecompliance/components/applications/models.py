from __future__ import unicode_literals

import datetime
import logging
import mimetypes
import six
import re
from decimal import Decimal
from django.conf import settings
from django.db import models, transaction
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.db.models.query import QuerySet
from django.dispatch import receiver
from django.contrib.postgres.fields.jsonb import JSONField
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from smart_selects.db_fields import ChainedForeignKey

from ledger.accounts.models import EmailUser, RevisionedMixin
from ledger.payments.invoice.models import Invoice
from ledger.checkout.utils import calculate_excl_gst
from wildlifecompliance.components.main.utils import (
    checkout, set_session_application,
    delete_session_application,
    flush_checkout_session
)

from wildlifecompliance.components.inspection.models import Inspection

from wildlifecompliance.components.organisations.models import Organisation
from wildlifecompliance.components.organisations.emails import (
    send_org_id_update_request_notification
)
from wildlifecompliance.components.main.models import (
    CommunicationsLogEntry,
    UserAction,
    Document
)
from wildlifecompliance.components.main.process_document import (
    save_issuance_document_obj,
)
from wildlifecompliance.components.applications.email import (
    send_application_submitter_email_notification,
    send_application_submit_email_notification,
    send_assessment_email_notification,
    send_assessment_reminder_email,
    send_assessment_completed_email,
    send_amendment_submit_email_notification,
    send_application_issue_notification,
    send_application_decline_notification,
    send_id_update_request_notification,
    send_application_return_to_officer_conditions_notification,
    send_activity_invoice_email_notification,
    send_activity_invoice_issue_notification,
    send_amendment_refund_email_notification,
    send_activity_propose_issue_notification,
)
from wildlifecompliance.components.main.utils import get_choice_value
from wildlifecompliance.ordered_model import OrderedModel
from wildlifecompliance.components.licences.models import (
    LicenceCategory,
    LicenceActivity,
    LicencePurpose,
    LicenceDocument,
    WildlifeLicence,
)
from wildlifecompliance.components.main.models import (
    TemporaryDocumentCollection
)
logger = logging.getLogger(__name__)


def get_app_label():
    try:
        return settings.SYSTEM_APP_LABEL
    except AttributeError:
        return ''


def update_application_doc_filename(instance, filename):
    return 'wildlifecompliance/applications/{}/documents/{}'.format(
        instance.application.id, filename)


def update_pdf_licence_filename(instance, filename):
    return 'wildlifecompliance/applications/{}/wildlife_compliance_licence/{}'.format(instance.id, filename)


def update_assessment_inspection_report_filename(instance, filename):
    return 'wildlifecompliance/assessments/{}/inspection_report/{}'.format(instance.id, filename)


def replace_special_chars(input_str, new_char='_'):
    return re.sub('[^A-Za-z0-9]+', new_char, input_str).strip('_').lower()


def update_application_comms_log_filename(instance, filename):
    return 'wildlifecompliance/applications/{}/communications/{}/{}'.format(
        instance.log_entry.application.id, instance.id, filename)


def get_temporary_document_collection(collection_id):
    """
    Utility function to retrieve stored documents from temporary storage.
    """

    temp_doc_collection = None
    temp_doc_collection, created = \
        TemporaryDocumentCollection.objects.get_or_create(
            id=collection_id.get('temp_doc_id'))

    # if temp_doc_collection:
    #    for doc in temp_doc_collection.documents.all():
    #       save_comms_log_document_obj(instance, workflow_entry, doc)
    #    temp_doc_collection.delete()

    return temp_doc_collection


class ActivityPermissionGroup(Group):
    licence_activities = models.ManyToManyField(
        'wildlifecompliance.LicenceActivity',
        blank=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'Activity permission group'
        verbose_name_plural = 'Activity permission groups'

    def __str__(self):
        return '{} ({} members)'.format(
            self.name,
            EmailUser.objects.filter(groups__name=self.name).count()
        )

    @property
    def display_name(self):
        return self.__str__

    @property
    def members(self):
        return EmailUser.objects.filter(
            groups__id=self.id
        ).distinct()

    @staticmethod
    def get_groups_for_activities(activities, codename):
        """
        Find matching ActivityPermissionGroups for a list of activities, activity ID or a LicenceActivity instance.
        :return: ActivityPermissionGroup QuerySet
        """
        from wildlifecompliance.components.licences.models import LicenceActivity

        if isinstance(activities, LicenceActivity):
            activities = [activities.id]

        groups = ActivityPermissionGroup.objects.filter(
            licence_activities__id__in=activities if isinstance(
                activities, (list, QuerySet)) else [activities]
        )
        if isinstance(codename, list):
            groups = groups.filter(permissions__codename__in=codename)
        else:
            groups = groups.filter(permissions__codename=codename)
        return groups.distinct()


class ApplicationDocument(Document):
    application = models.ForeignKey('Application', related_name='documents')
    _file = models.FileField(upload_to=update_application_doc_filename)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    # after initial submit prevent document from being deleted
    can_delete = models.BooleanField(default=True)

    def delete(self):
        if self.can_delete:
            return super(ApplicationDocument, self).delete()
        logger.info(
            'Cannot delete existing document object after application has been\
            submitted (including document submitted before\
            application pushback to status Draft): {}'.format(
                self.name)
        )

    class Meta:
        app_label = 'wildlifecompliance'


class Application(RevisionedMixin):

    APPLICANT_TYPE_ORGANISATION = 'ORG'
    APPLICANT_TYPE_PROXY = 'PRX'
    APPLICANT_TYPE_SUBMITTER = 'SUB'

    CUSTOMER_STATUS_DRAFT = 'draft'
    CUSTOMER_STATUS_UNDER_REVIEW = 'under_review'
    CUSTOMER_STATUS_AWAITING_PAYMENT = 'awaiting_payment'
    CUSTOMER_STATUS_AMENDMENT_REQUIRED = 'amendment_required'
    CUSTOMER_STATUS_ACCEPTED = 'accepted'
    CUSTOMER_STATUS_PARTIALLY_APPROVED = 'partially_approved'
    CUSTOMER_STATUS_DECLINED = 'declined'
    CUSTOMER_STATUS_CHOICES = (
        (CUSTOMER_STATUS_DRAFT, 'Draft'),
        (CUSTOMER_STATUS_AWAITING_PAYMENT, 'Awaiting Payment'),
        (CUSTOMER_STATUS_UNDER_REVIEW, 'Under Review'),
        (CUSTOMER_STATUS_AMENDMENT_REQUIRED, 'Amendment Required'),
        (CUSTOMER_STATUS_ACCEPTED, 'Accepted'),
        (CUSTOMER_STATUS_PARTIALLY_APPROVED, 'Partially Approved'),
        (CUSTOMER_STATUS_DECLINED, 'Declined'),
    )

    # List of statuses from above that allow a customer to edit an application.
    CUSTOMER_EDITABLE_STATE = [
        CUSTOMER_STATUS_DRAFT,
        CUSTOMER_STATUS_AWAITING_PAYMENT,
        CUSTOMER_STATUS_AMENDMENT_REQUIRED,
    ]

    # List of statuses from above that allow a customer to view an application
    # (read-only)
    CUSTOMER_VIEWABLE_STATE = [
        CUSTOMER_STATUS_UNDER_REVIEW,
        CUSTOMER_STATUS_ACCEPTED,
        CUSTOMER_STATUS_PARTIALLY_APPROVED,
        CUSTOMER_STATUS_DECLINED,
    ]

    PROCESSING_STATUS_DRAFT = 'draft'
    PROCESSING_STATUS_AWAITING_APPLICANT_RESPONSE = 'awaiting_applicant_response'
    PROCESSING_STATUS_APPROVED = 'approved'
    PROCESSING_STATUS_PARTIALLY_APPROVED = 'partially_approved'
    PROCESSING_STATUS_DECLINED = 'declined'
    PROCESSING_STATUS_DISCARDED = 'discarded'
    PROCESSING_STATUS_UNDER_REVIEW = 'under_review'
    PROCESSING_STATUS_AWAITING_PAYMENT = 'awaiting_payment'
    PROCESSING_STATUS_CHOICES = (
        (PROCESSING_STATUS_DRAFT, 'Draft'),
        (PROCESSING_STATUS_AWAITING_APPLICANT_RESPONSE, 'Awaiting Applicant Response'),
        (PROCESSING_STATUS_APPROVED, 'Approved'),
        (PROCESSING_STATUS_PARTIALLY_APPROVED, 'Partially Approved'),
        (PROCESSING_STATUS_DECLINED, 'Declined'),
        (PROCESSING_STATUS_DISCARDED, 'Discarded'),
        (PROCESSING_STATUS_UNDER_REVIEW, 'Under Review'),
        (PROCESSING_STATUS_AWAITING_PAYMENT, 'Awaiting Payment'),        
    )

    ID_CHECK_STATUS_NOT_CHECKED = 'not_checked'
    ID_CHECK_STATUS_AWAITING_UPDATE = 'awaiting_update'
    ID_CHECK_STATUS_UPDATED = 'updated'
    ID_CHECK_STATUS_ACCEPTED = 'accepted'
    ID_CHECK_STATUS_CHOICES = (
        (ID_CHECK_STATUS_NOT_CHECKED, 'Not Checked'),
        (ID_CHECK_STATUS_AWAITING_UPDATE, 'Awaiting Update'),
        (ID_CHECK_STATUS_UPDATED, 'Updated'),
        (ID_CHECK_STATUS_ACCEPTED, 'Accepted')
    )

    RETURN_CHECK_STATUS_NOT_CHECKED = 'not_checked'
    RETURN_CHECK_STATUS_AWAITING_RETURNS = 'awaiting_returns'
    RETURN_CHECK_STATUS_COMPLETED = 'completed'
    RETURN_CHECK_STATUS_ACCEPTED = 'accepted'
    RETURN_CHECK_STATUS_CHOICES = (
        (RETURN_CHECK_STATUS_NOT_CHECKED, 'Not Checked'),
        (RETURN_CHECK_STATUS_AWAITING_RETURNS, 'Awaiting Returns'),
        (RETURN_CHECK_STATUS_COMPLETED, 'Completed'),
        (RETURN_CHECK_STATUS_ACCEPTED, 'Accepted')
    )

    CHARACTER_CHECK_STATUS_NOT_CHECKED = 'not_checked'
    CHARACTER_CHECK_STATUS_ACCEPTED = 'accepted'
    CHARACTER_CHECK_STATUS_CHOICES = (
        (CHARACTER_CHECK_STATUS_NOT_CHECKED, 'Not Checked'),
        (CHARACTER_CHECK_STATUS_ACCEPTED, 'Accepted')
    )

    REVIEW_STATUS_NOT_REVIEWED = 'not_reviewed'
    REVIEW_STATUS_AWAITING_AMENDMENTS = 'awaiting_amendments'
    REVIEW_STATUS_AMENDED = 'amended'
    REVIEW_STATUS_ACCEPTED = 'accepted'
    REVIEW_STATUS_CHOICES = (
        (REVIEW_STATUS_NOT_REVIEWED, 'Not Reviewed'),
        (REVIEW_STATUS_AWAITING_AMENDMENTS, 'Awaiting Amendments'),
        (REVIEW_STATUS_AMENDED, 'Amended'),
        (REVIEW_STATUS_ACCEPTED, 'Accepted')
    )

    APPLICATION_TYPE_NEW_LICENCE = 'new_licence'
    APPLICATION_TYPE_ACTIVITY = 'new_activity'
    APPLICATION_TYPE_AMENDMENT = 'amend_activity'
    APPLICATION_TYPE_RENEWAL = 'renew_activity'
    APPLICATION_TYPE_SYSTEM_GENERATED = 'system_generated'
    APPLICATION_TYPE_REISSUE = 'reissue_activity'
    APPLICATION_TYPE_CHOICES = (
        (APPLICATION_TYPE_NEW_LICENCE, 'New'),
        (APPLICATION_TYPE_ACTIVITY, 'New Activity'),
        (APPLICATION_TYPE_AMENDMENT, 'Amendment'),
        (APPLICATION_TYPE_RENEWAL, 'Renewal'),
        (APPLICATION_TYPE_SYSTEM_GENERATED, 'System Generated'),
        (APPLICATION_TYPE_REISSUE, 'Reissue'),
    )

    application_type = models.CharField(
        'Application Type',
        max_length=40,
        choices=APPLICATION_TYPE_CHOICES,
        default=APPLICATION_TYPE_NEW_LICENCE)
    comment_data = JSONField(blank=True, null=True)
    licence_purposes = models.ManyToManyField(
        'wildlifecompliance.LicencePurpose',
        blank=True
    )
    customer_status = models.CharField(
        'Customer Status',
        max_length=40,
        choices=CUSTOMER_STATUS_CHOICES,
        default=CUSTOMER_STATUS_DRAFT)
    lodgement_number = models.CharField(max_length=9, blank=True, default='')
    lodgement_date = models.DateTimeField(blank=True, null=True)
    org_applicant = models.ForeignKey(
        Organisation,
        blank=True,
        null=True,
        related_name='org_applications')
    proxy_applicant = models.ForeignKey(
        EmailUser,
        blank=True,
        null=True,
        related_name='wildlifecompliance_proxy')
    submitter = models.ForeignKey(
        EmailUser,
        blank=True,
        null=True,
        related_name='wildlifecompliance_applications')
    id_check_status = models.CharField(
        'Identification Check Status',
        max_length=30,
        choices=ID_CHECK_STATUS_CHOICES,
        default=ID_CHECK_STATUS_NOT_CHECKED)
    return_check_status = models.CharField(
        'Return Check Status',
        max_length=30,
        choices=RETURN_CHECK_STATUS_CHOICES,
        default=RETURN_CHECK_STATUS_NOT_CHECKED)
    character_check_status = models.CharField(
        'Character Check Status',
        max_length=30,
        choices=CHARACTER_CHECK_STATUS_CHOICES,
        default=CHARACTER_CHECK_STATUS_NOT_CHECKED)
    review_status = models.CharField(
        'Review Status',
        max_length=30,
        choices=REVIEW_STATUS_CHOICES,
        default=REVIEW_STATUS_NOT_REVIEWED)
    licence = models.ForeignKey(
        'wildlifecompliance.WildlifeLicence',
        null=True,
        blank=True)
    # generated licence for the application.
    licence_document = models.ForeignKey(
        LicenceDocument,
        blank=True,
        null=True)
    previous_application = models.ForeignKey(
        'self', on_delete=models.PROTECT, blank=True, null=True, related_name='parents')
    application_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default='0')

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return str(self.id)

    # Append 'A' to Application id to generate Lodgement number. Lodgement
    # number and lodgement sequence are used to generate Reference.
    def save(self, *args, **kwargs):
        super(Application, self).save(*args, **kwargs)
        if self.lodgement_number == '':
            new_lodgement_id = 'A{0:06d}'.format(self.pk)
            self.lodgement_number = new_lodgement_id
            self.save()

    @property
    def applicant(self):
        if self.org_applicant:
            return self.org_applicant.organisation.name
        elif self.proxy_applicant:
            return "{} {}".format(
                self.proxy_applicant.first_name,
                self.proxy_applicant.last_name)
        else:
            return "{} {}".format(
                self.submitter.first_name,
                self.submitter.last_name)

    @property
    def applicant_details(self):
        if self.org_applicant:
            return '{} \n{}'.format(
                self.org_applicant.organisation.name,
                self.org_applicant.address)
        elif self.proxy_applicant:
            return "{} {}\n{}".format(
                self.proxy_applicant.first_name,
                self.proxy_applicant.last_name,
                self.proxy_applicant.addresses.all().first())
        else:
            return "{} {}\n{}".format(
                self.submitter.first_name,
                self.submitter.last_name,
                self.submitter.addresses.all().first())

    @property
    def applicant_id(self):
        if self.org_applicant:
            return self.org_applicant.id
        elif self.proxy_applicant:
            return self.proxy_applicant.id
        else:
            return self.submitter.id

    @property
    def applicant_type(self):
        if self.org_applicant:
            return self.APPLICANT_TYPE_ORGANISATION
        elif self.proxy_applicant:
            return self.APPLICANT_TYPE_PROXY
        else:
            return self.APPLICANT_TYPE_SUBMITTER

    @property
    def processing_status(self):
        selected_activities = self.selected_activities.all()
        activity_statuses = [activity.processing_status for activity in selected_activities]
        # not yet submitted
        if activity_statuses.count(ApplicationSelectedActivity.PROCESSING_STATUS_DRAFT) == len(activity_statuses):
            return self.PROCESSING_STATUS_DRAFT
        # awaiting payment
        if activity_statuses.count(ApplicationSelectedActivity.PROCESSING_STATUS_AWAITING_LICENCE_FEE_PAYMENT) == len(activity_statuses):
            return self.PROCESSING_STATUS_AWAITING_PAYMENT
        # application discarded
        elif activity_statuses.count(ApplicationSelectedActivity.PROCESSING_STATUS_DISCARDED) == len(activity_statuses):
            return self.PROCESSING_STATUS_DISCARDED
        # amendment request sent to user and outstanding
        elif self.active_amendment_requests.filter(status=AmendmentRequest.AMENDMENT_REQUEST_STATUS_REQUESTED).count() > 0:
            return self.PROCESSING_STATUS_AWAITING_APPLICANT_RESPONSE
        # all activities approved
        elif activity_statuses.count(ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED) == len(activity_statuses):
            return self.PROCESSING_STATUS_APPROVED
        # one or more (but not all) activities approved
        elif 0 < activity_statuses.count(ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED) < \
                len(activity_statuses):
            return self.PROCESSING_STATUS_PARTIALLY_APPROVED
        # all activities declined
        elif activity_statuses.count(ApplicationSelectedActivity.PROCESSING_STATUS_DECLINED) == len(activity_statuses):
            return self.PROCESSING_STATUS_DECLINED
        else:
            return self.PROCESSING_STATUS_UNDER_REVIEW

    @property
    def has_amendment(self):
        return self.active_amendment_requests.filter(status=AmendmentRequest.AMENDMENT_REQUEST_STATUS_REQUESTED).exists()

    @property
    def is_assigned(self):
        """
        A check for any licence activities on this application has been
        allocated to an internal officer.
        """
        assigned = ApplicationSelectedActivity.objects.filter(
            application_id=self.id
        ).exclude(assigned_officer__isnull=True).first()

        return True if assigned else False

    @property
    def can_user_edit(self):
        """
        :return: True if the application is in one of the editable status.
        """
        return self.customer_status in self.CUSTOMER_EDITABLE_STATE

    @property
    def can_user_view(self):
        """
        :return: True if the application is in one of the approved status.
        """
        return self.customer_status in self.CUSTOMER_VIEWABLE_STATE

    @property
    def is_discardable(self):
        """
        An application can be discarded by a customer if:
        1 - It is a draft or a draft awaiting payment
        2- or if the application has been pushed back to the user
        TODO: need to confirm regarding (2) here related to ApplicationSelectedActivity
        """
        return self.customer_status in [
            Application.CUSTOMER_STATUS_DRAFT,
            Application.CUSTOMER_STATUS_AWAITING_PAYMENT,
        ] or self.processing_status == Application.PROCESSING_STATUS_AWAITING_APPLICANT_RESPONSE

    @property
    def is_deletable(self):
        """
        An application can be deleted only if it is a draft and it hasn't been lodged yet
        :return:
        """
        return self.customer_status in [
            Application.CUSTOMER_STATUS_DRAFT,
            Application.CUSTOMER_STATUS_AWAITING_PAYMENT,
        ] and not self.lodgement_number

    @property
    def application_fee_paid(self):
        return self.payment_status in [
            ApplicationInvoice.PAYMENT_STATUS_NOT_REQUIRED,
            ApplicationInvoice.PAYMENT_STATUS_PAID,
            ApplicationInvoice.PAYMENT_STATUS_OVERPAID,
        ]

    @property
    def payment_status(self):
        # TODO: needs more work, underpaid/overpaid statuses to be added,
        # refactor to key/name like processing_status
        if self.application_fee == 0 and self.total_paid_amount < 1:
            return ApplicationInvoice.PAYMENT_STATUS_NOT_REQUIRED
        else:
            if self.requires_refund:
                return ApplicationInvoice.PAYMENT_STATUS_OVERPAID
            if self.invoices.count() == 0:
                return ApplicationInvoice.PAYMENT_STATUS_UNPAID
            else:
                try:
                    latest_invoice = Invoice.objects.get(
                        reference=self.invoices.latest('id').invoice_reference)
                except Invoice.DoesNotExist:
                    return ApplicationInvoice.PAYMENT_STATUS_UNPAID
                return latest_invoice.payment_status

    @property
    def latest_invoice(self):
        """
        Property defining the latest invoice for the Application.
        """
        latest_invoice = None
        if self.invoices.count() > 0:
            try:
                latest_invoice = Invoice.objects.get(
                    reference=self.invoices.latest('id').invoice_reference)
            except Invoice.DoesNotExist:
                return None

        return latest_invoice

    @property
    def total_paid_amount(self):
        """
        Property defining the total amount already paid for the Application.
        """
        amount = 0
        if self.invoices.count() > 0:
            invoices = ApplicationInvoice.objects.filter(
                application_id=self.id)
            for invoice in invoices:
                detail = Invoice.objects.get(
                    reference=invoice.invoice_reference)
                # payment_amount includes refund payment adjustments.
                amount += detail.payment_amount

        return amount

    @property
    def regions_list(self):
        return self.region.split(',') if self.region else []

    @property
    def permit(self):
        return self.licence_document if self.licence_document else None

    @property
    def licence_officers(self):
        """
        Authorised licensing officers for this Application.
        """
        groups = self.get_permission_groups('licensing_officer').values_list('id', flat=True)
        return EmailUser.objects.filter(
            groups__id__in=groups
        ).distinct()

    @property
    def licence_approvers(self):
        groups = self.get_permission_groups('issuing_officer')\
            .values_list('id', flat=True)

        return EmailUser.objects.filter(groups__id__in=groups).distinct()

    @property
    def officers_and_assessors(self):
        groups = self.get_permission_groups(
            ['licensing_officer',
             'assessor',
             'issuing_officer']
        ).values_list('id', flat=True)
        return EmailUser.objects.filter(
            groups__id__in=groups
        ).distinct()

    @property
    def licence_type_short_name(self):
        return self.licence_category

    @property
    def licence_type_data(self):
        '''
        Get valid licence categories and associated activities associated with
        thie application.

        Used in the presentation for authorised selected licence activities.
        '''
        from wildlifecompliance.components.licences.serializers import (
            LicenceCategorySerializer
        )

        serializer = LicenceCategorySerializer(
            self.licence_purposes.first().licence_category,
            context={
                'purpose_records': self.licence_purposes
            }
        )
        licence_data = serializer.data
        for activity in licence_data['activity']:
            selected_activity = self.get_selected_activity(activity['id'])
            activity['processing_status'] = {
                'id': selected_activity.processing_status,
                'name': get_choice_value(
                    selected_activity.processing_status,
                    ApplicationSelectedActivity.PROCESSING_STATUS_CHOICES
                )
            }
            # although these fields are retrieved it is not applied for the
            # authorisation.
            activity['start_date'] = selected_activity.get_start_date()
            activity['expiry_date'] = selected_activity.get_expiry_date()
        return licence_data

    @property
    def licence_category_name(self):
        first_activity = self.licence_purposes.first()
        try:
            activity_category = first_activity.licence_category.short_name
        except AttributeError:
            activity_category = ''
        return activity_category

    @property
    def licence_activity_names(self):
        return list(self.licence_purposes.all().values_list(
            'licence_activity__short_name', flat=True
        ).distinct())

    @property
    def licence_purpose_names(self):
        return ', '.join([purpose.short_name
                          for purpose in self.licence_purposes.all().order_by('licence_activity','short_name')])

    @property
    def licence_type_name(self):
        from wildlifecompliance.components.licences.models import LicenceActivity
        licence_category = self.licence_category_name
        licence_activity_purposes = []
        activity_id_list = self.licence_purposes.all().order_by('licence_activity_id').values_list('licence_activity_id', flat=True).distinct()
        for activity_id in activity_id_list:
            try:
                activity_short_name = LicenceActivity.objects.get(id=activity_id).short_name
            except AttributeError:
                activity_short_name = ''
            purpose_list = ', '.join(self.licence_purposes.filter(licence_activity_id=activity_id).values_list('short_name', flat=True))
            licence_activity_purposes.append('{} ({})'.format(activity_short_name, purpose_list))
        licence_activity_purposes_string = ', '.join(licence_activity_purposes)
        return ' {licence_category}{activities_purposes}'.format(
            licence_category="{} - ".format(licence_category) if licence_category else "",
            activities_purposes="{}".format(licence_activity_purposes_string) if licence_activity_purposes_string else ''
        )

    @property
    def licence_category_id(self):
        try:
            return self.licence_purposes.first().licence_category.id
        except AttributeError:
            return ''

    @property
    def licence_category(self):
        try:
            return self.licence_purposes.first().licence_category.display_name
        except AttributeError:
            return ''

    def set_activity_processing_status(self, activity_id, processing_status):
        if not activity_id:
            logger.error("Application: %s cannot update processing status (%s) for an empty activity_id!" %
                         (self.id, processing_status))
            return
        if processing_status not in dict(ApplicationSelectedActivity.PROCESSING_STATUS_CHOICES):
            logger.error("Application: %s cannot update processing status (%s) for invalid processing status!" %
                         (self.id, processing_status))
            return
        selected_activity = self.get_selected_activity(activity_id)
        selected_activity.processing_status = processing_status
        selected_activity.save()
        logger.info("Application: %s Activity ID: %s changed processing status to: %s" % (self.id, activity_id, processing_status))

    def set_activity_activity_status(self, activity_id, activity_status):
        if not activity_id:
            logger.error("Application: %s cannot update activity status (%s) for an empty activity_id!" %
                         (self.id, activity_status))
            return
        if activity_status not in dict(ApplicationSelectedActivity.ACTIVITY_STATUS_CHOICES):
            logger.error("Application: %s cannot update activity status (%s) for invalid activity status!" %
                         (self.id, activity_status))
            return
        selected_activity = self.get_selected_activity(activity_id)
        selected_activity.activity_status = activity_status
        selected_activity.save()
        logger.info("Application: %s Activity ID: %s changed activity status to: %s" % (self.id, activity_id, activity_status))

    def set_activity_approver(self, activity_id, licence_approver):
        '''
        Sets an allocated Approver for an Application Selected Activity.

        :param activity_id is an unique identifier for ASA.
        :param licence_approver is an EmailUser to be allocated to ASA.
        '''
        if not activity_id:
            logger.error("Application: %s cannot update activity approver (%s) \
                no activity_id provided." % (self.id, licence_approver))
            return
        selected_activity = self.get_selected_activity(activity_id)
        selected_activity.assigned_approver = licence_approver
        selected_activity.save()
        logger.info("Application: %s Activity ID: %s changed activity approver \
            to: %s" % (self.id, activity_id, licence_approver))

    def get_selected_activity(self, activity_id):
        '''
        :param activity_id: LicenceActivity ID, used to filter ApplicationSelectedActivity (ASA)
        :return: first ApplicationSelectedActivity record filtered by application id and ASA id

        If ASA not found, create one and set application and ASA id fields
        '''
        if activity_id is None:
            return ApplicationSelectedActivity.objects.none()

        selected_activity = ApplicationSelectedActivity.objects.filter(
            application_id=self.id,
            licence_activity_id=activity_id
        ).first()
        if not selected_activity:
            selected_activity = ApplicationSelectedActivity.objects.create(
                application_id=self.id,
                licence_activity_id=activity_id
            )
        return selected_activity

    def get_licence_category(self):
        first_activity = self.licence_purposes.first()
        try:
            return first_activity.licence_category
        except AttributeError:
            return LicenceCategory.objects.none()

    def get_permission_groups(self, codename):
        """
        :return: queryset of ActivityPermissionGroups matching the current application by activity IDs
        """
        selected_activity_ids = ApplicationSelectedActivity.objects.filter(
            application_id=self.id,
            licence_activity__isnull=False
        ).values_list('licence_activity__id', flat=True)
        if not selected_activity_ids:
            return ActivityPermissionGroup.objects.none()

        return ActivityPermissionGroup.get_groups_for_activities(selected_activity_ids, codename)

    def log_user_action(self, action, request):
        return ApplicationUserAction.log_action(self, action, request.user)

    def copy_application_purposes_for_status(
            self, purpose_ids_list, new_activity_status):
        '''
        Creates a copy of the Application and associated records
        for the specified purposes and activity status.

        TODO:AYN Activity consist of proposed_purposes with effective dates and
        status. These need to be copied and handled appropriately with Replace.
        '''
        # Get the ID of the original application
        original_app_id = self.id

        # Validate purpose_ids_list against LicencePurpose records for the
        # application.
        if purpose_ids_list:
            try:
                for licence_purpose_id in purpose_ids_list:
                    LicencePurpose.objects.get(
                        id=licence_purpose_id, application__id=original_app_id)
            except BaseException:
                raise ValidationError(
                    'One or more IDs in the purpose list are not valid')
        else:
            raise ValidationError('Purpose list is empty')

        # Confirm all purposes are of the same LicenceActivity type and then
        # set licence_activity_id.
        if LicencePurpose.objects.filter(id__in=purpose_ids_list) \
                .values_list(
                    'licence_activity_id', flat=True).distinct().count() > 1:
            raise ValidationError(
              'Purpose list contains purposes of different licence activities')
        else:
            licence_activity_id = LicencePurpose.objects.filter(
                id__in=purpose_ids_list).first().licence_activity_id

        # Only continue if valid and current licence exists and original
        # application is part of the chain.
        try:
            parent_licence, created = self.get_parent_licence(
                auto_create=False)
            application_chain =\
                parent_licence.current_application.get_application_children()
            if self in application_chain:
                pass
            else:
                raise ValidationError('Application you are trying to copy is'
                                      ' not associated with a valid current'
                                      ' licence')
        except BaseException:
            raise ValidationError('Application you are trying to copy is not'
                                  ' associated with a valid current licence')

        with transaction.atomic():

            # Create new application as a clone of the original application.
            # NOTE: System Generated Applications cannot be processed by staff
            # and so processing status for activity needs to be accepted.
            new_app = Application.objects.get(id=original_app_id)
            new_app.id = None
            new_app.application_type =\
                Application.APPLICATION_TYPE_SYSTEM_GENERATED
            new_app.lodgement_number = ''
            new_app.application_fee = Decimal('0.00')
            # Use parent_licence.current_application to always retrieve the
            # latest application in the chain.
            new_app.previous_application = parent_licence.current_application
            new_app.licence = parent_licence
            new_app.save()

            # Set the associated licence's current_application to the new
            # application.
            parent_licence.current_application = new_app
            parent_licence.save()

            # Create ApplicationSelectedActivity record for the new application
            selected_activity = Application.objects.get(id=original_app_id)\
                .selected_activities.get(
                    licence_activity_id=licence_activity_id)
            # TODO:AYN Replace needs to be set at the purpose level.
            # REP code below did NOT process.
            selected_activity.activity_status =\
                ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED
            selected_activity.save()
            new_activity = selected_activity
            new_activity.id = None
            new_activity.licence_fee = Decimal('0.00')
            new_activity.application = new_app
            new_activity.activity_status = new_activity_status
            new_activity.save()

            # Link the target LicencePurpose IDs to the new application
            # Copy ApplicationFormDataRecord rows from old application,
            # licence_activity and licence_purpose.
            for licence_purpose_id in purpose_ids_list:
                self.copy_application_purpose_to_target_application(
                    new_app, licence_purpose_id)

                self.copy_activity_purpose_to_target_for_status(
                    licence_purpose_id,
                    selected_activity,
                    new_activity,
                )

            # REP = ApplicationSelectedActivityPurpose.PROCESSING_STATUS_REPLACED
            # for purpose in selected_activity.proposed_purposes.all():
            #     # FIXME: does not set correctly on a licence amendment.
            #     purpose.processing_status = REP
            #     purpose.save()

        return new_app

    def copy_activity_purpose_to_target_for_status(self, p_id, old, new):
        '''
        Copies the Selected Activity Purposes from the selected to the target.
        To ensure effective dates are carried over to new (target) activity.

        TODO:AYN copy status dates across and mark selected as being REPLACED.
        '''
        # update Application Selected Activity Purposes
        SELECT = ApplicationSelectedActivityPurpose.PROCESSING_STATUS_SELECTED
        REPLACE = ApplicationSelectedActivityPurpose.PROCESSING_STATUS_REPLACED

        lp = LicencePurpose.objects.get(id=p_id)
        issued = old.proposed_purposes.filter(
            purpose=lp
        ).first()

        purpose, c = ApplicationSelectedActivityPurpose.objects.get_or_create(
            purpose=lp,
            selected_activity=new,
        )
        purpose.processing_status = SELECT
        purpose.start_date = issued.start_date
        purpose.expiry_date = issued.expiry_date
        purpose.original_issue_date = issued.original_issue_date
        purpose.issue_date = issued.issue_date
        purpose.save()

        issued.processing_status = REPLACE
        issued.save()

    def copy_application_purpose_to_target_application(
            self, target_application=None, licence_purpose_id=None):
        '''
        Copies the licence purpose identifier associated with this application
        to another application (renewal, admendment, reissue) and copies
        associated Form Data for the purpose to the target.

        TODO:AYN copy activity purpose date to the target.
        '''
        if not target_application or not licence_purpose_id:
            raise ValidationError(
                'Target application and licence_purpose_id must be specified')
        try:
            LicencePurpose.objects.get(id=licence_purpose_id, application=self)
        except BaseException:
            raise ValidationError(
                'The licence purpose ID is not valid for this application')

        with transaction.atomic():
            # Link the target LicencePurpose ID to the target_application
            target_application.licence_purposes.add(licence_purpose_id)

            # Copy ApplicationFormDataRecord rows from application (self) for
            # selected licence_activity and licence_purpose to
            # target_application.
            licence_activity_id = LicencePurpose.objects.get(
                    id=licence_purpose_id).licence_activity_id
            for data_row in ApplicationFormDataRecord.objects.filter(
                    application_id=self,
                    licence_activity_id=licence_activity_id,
                    licence_purpose_id=licence_purpose_id):
                data_row.id = None
                data_row.application_id = target_application.id

                # species list is saved and needs to be rebuilt.
                TYPE = ApplicationFormDataRecord.COMPONENT_TYPE_SELECT_SPECIES
                if data_row.component_type == TYPE:
                    data_row.component_attribute = None

                data_row.save()

    def submit(self, request):
        from wildlifecompliance.components.licences.models import LicenceActivity
        with transaction.atomic():
            if self.can_user_edit:
                if not self.application_fee_paid and not self.requires_refund:
                    self.customer_status = Application.CUSTOMER_STATUS_AWAITING_PAYMENT
                    self.save()
                    return
                self.customer_status = Application.CUSTOMER_STATUS_UNDER_REVIEW
                self.submitter = request.user
                self.lodgement_date = timezone.now()
                # if amendment is submitted change the status of only particular activity
                # else if the new application is submitted change the status of
                # all the activities
                if (self.amendment_requests):
                    qs = self.amendment_requests.filter(status=AmendmentRequest.AMENDMENT_REQUEST_STATUS_REQUESTED)
                    if (qs):
                        for q in qs:
                            q.status = AmendmentRequest.AMENDMENT_REQUEST_STATUS_AMENDED
                            self.set_activity_processing_status(
                                q.licence_activity.id, ApplicationSelectedActivity.PROCESSING_STATUS_WITH_OFFICER)
                            q.save()
                else:
                    for activity in self.licence_type_data['activity']:
                        if activity["processing_status"]["id"] != ApplicationSelectedActivity.PROCESSING_STATUS_DRAFT:
                            continue

                        if self.application_type \
                                == Application.APPLICATION_TYPE_REISSUE:
                            latest_activity =\
                                self.get_latest_current_activity(activity["id"])
                            if not latest_activity:
                                raise Exception("Active licence not found for activity ID: %s" % activity["id"])
                            self.set_activity_processing_status(
                                activity["id"], ApplicationSelectedActivity.PROCESSING_STATUS_OFFICER_FINALISATION)
                            selected_activity = \
                                self.get_selected_activity(activity["id"])
                            selected_activity.proposed_action =\
                                ApplicationSelectedActivity.PROPOSED_ACTION_ISSUE
                            selected_activity.proposed_start_date =\
                                latest_activity.start_date
                            selected_activity.proposed_end_date =\
                                latest_activity.expiry_date
                            selected_activity.save()
                        else:
                            self.set_activity_processing_status(
                                activity["id"], ApplicationSelectedActivity.PROCESSING_STATUS_WITH_OFFICER)
                        '''
                        Process Default Conditions for an Application.
                        '''
                        conditions = DefaultCondition.objects.filter(
                            licence_activity=activity["id"]
                            )

                        for d in conditions:
                            sc = ApplicationStandardCondition.objects.get(
                                id=d.standard_condition_id
                                )

                            ac, c = ApplicationCondition.objects.get_or_create(
                                is_default=True,
                                standard=True,
                                standard_condition=sc,
                                application=self
                            )
                            ac.licence_activity = d.licence_activity
                            ac.licence_purpose = d.licence_purpose
                            ac.return_type = sc.return_type
                            ac.save()

                self.save()
                officer_groups = ActivityPermissionGroup.objects.filter(
                    permissions__codename='licensing_officer',
                    licence_activities__purpose__licence_category__id=self.licence_type_data["id"]
                )
                group_users = EmailUser.objects.filter(
                    groups__id__in=officer_groups.values_list('id', flat=True)
                ).distinct()

                if self.amendment_requests:
                    self.log_user_action(
                        ApplicationUserAction.ACTION_ID_REQUEST_AMENDMENTS_SUBMIT.format(
                            self.id), request)
                    if self.requires_refund:
                        self.alert_for_refund(request)
                    else:
                        send_amendment_submit_email_notification(
                            group_users, self, request)

                else:
                    # Create a log entry for the application
                    self.log_user_action(
                        ApplicationUserAction.ACTION_LODGE_APPLICATION.format(
                            self.id), request)
                    # Create a log entry for the applicant (submitter,
                    # organisation or proxy)
                    if self.org_applicant:
                        self.org_applicant.log_user_action(
                            ApplicationUserAction.ACTION_LODGE_APPLICATION.format(
                                self.id), request)
                    elif self.proxy_applicant:
                        self.proxy_applicant.log_user_action(
                            ApplicationUserAction.ACTION_LODGE_APPLICATION.format(
                                self.id), request)
                    else:
                        self.submitter.log_user_action(
                            ApplicationUserAction.ACTION_LODGE_APPLICATION.format(
                                self.id), request)

                    # notify linked officer groups of submission.
                    if self.requires_refund:  
                        self.alert_for_refund(request)
                    else:
                        send_application_submit_email_notification(
                            group_users, self, request)

                    self.documents.all().update(can_delete=False)

            else:
                raise ValidationError(
                    'You can\'t edit this application at this moment')

    def accept_id_check(self, request):
        self.id_check_status = Application.ID_CHECK_STATUS_ACCEPTED
        self.save()
        # Create a log entry for the application
        self.log_user_action(
            ApplicationUserAction.ACTION_ACCEPT_ID.format(
                self.id), request)
        # Create a log entry for the applicant (submitter, organisation or
        # proxy)
        if self.org_applicant:
            self.org_applicant.log_user_action(
                ApplicationUserAction.ACTION_ACCEPT_ID.format(
                    self.id), request)
        elif self.proxy_applicant:
            self.proxy_applicant.log_user_action(
                ApplicationUserAction.ACTION_ACCEPT_ID.format(
                    self.id), request)
        else:
            self.submitter.log_user_action(
                ApplicationUserAction.ACTION_ACCEPT_ID.format(
                    self.id), request)

    def reset_id_check(self, request):
        self.id_check_status = Application.ID_CHECK_STATUS_NOT_CHECKED
        self.save()
        # Create a log entry for the application
        self.log_user_action(
            ApplicationUserAction.ACTION_RESET_ID.format(
                self.id), request)
        # Create a log entry for the applicant (submitter, organisation or
        # proxy)
        if self.org_applicant:
            self.org_applicant.log_user_action(
                ApplicationUserAction.ACTION_RESET_ID.format(
                    self.id), request)
        elif self.proxy_applicant:
            self.proxy_applicant.log_user_action(
                ApplicationUserAction.ACTION_RESET_ID.format(
                    self.id), request)
        else:
            self.submitter.log_user_action(
                ApplicationUserAction.ACTION_RESET_ID.format(
                    self.id), request)

    def request_id_check(self, request):
        self.id_check_status = Application.ID_CHECK_STATUS_AWAITING_UPDATE
        self.save()
        # Create a log entry for the application
        self.log_user_action(
            ApplicationUserAction.ACTION_ID_REQUEST_UPDATE.format(
                self.id), request)
        # Create a log entry for the applicant (submitter or organisation only)
        if self.org_applicant:
            self.org_applicant.log_user_action(
                ApplicationUserAction.ACTION_ID_REQUEST_UPDATE.format(
                    self.id), request)
        elif self.proxy_applicant:
            # do nothing if proxy_applicant
            pass
        else:
            self.submitter.log_user_action(
                ApplicationUserAction.ACTION_ID_REQUEST_UPDATE.format(
                    self.id), request)
        # send email to submitter or org_applicant admins
        if self.org_applicant:
            send_org_id_update_request_notification(self, request)
        elif self.proxy_applicant:
            # do nothing if proxy_applicant
            pass
        else:
            # send to submitter
            send_id_update_request_notification(self, request)

    def accept_character_check(self, request):
        self.character_check_status = Application.CHARACTER_CHECK_STATUS_ACCEPTED
        self.save()
        # Create a log entry for the application
        self.log_user_action(
            ApplicationUserAction.ACTION_ACCEPT_CHARACTER.format(
                self.id), request)
        # Create a log entry for the applicant (submitter, organisation or
        # proxy)
        if self.org_applicant:
            self.org_applicant.log_user_action(
                ApplicationUserAction.ACTION_ACCEPT_CHARACTER.format(
                    self.id), request)
        elif self.proxy_applicant:
            self.proxy_applicant.log_user_action(
                ApplicationUserAction.ACTION_ACCEPT_CHARACTER.format(
                    self.id), request)
        else:
            self.submitter.log_user_action(
                ApplicationUserAction.ACTION_ACCEPT_CHARACTER.format(
                    self.id), request)

    def assign_officer(self, request, officer):
        """
        Method to allocate an officer to an application licence activity.
        :param request contains activity_id
        :param officer is EmailUser details.
        """
        activity_id = request.data.get('activity_id', None)
        selected_activity = self.get_selected_activity(activity_id)
        with transaction.atomic():
            try:
                if officer != selected_activity.assigned_officer:
                    selected_activity.assigned_officer = officer
                    selected_activity.save()
                    # Create a log entry for the application
                    self.log_user_action(
                        ApplicationUserAction.ACTION_ASSIGN_TO_OFFICER.format(
                            self.id, '{}({})'.format(
                                officer.get_full_name(),
                                officer.email)
                        ), request)
            except BaseException:
                raise

    def unassign_officer(self, request):
        """
        Method to remove an officer from an application licence activity.
        :param request contains activity_id.
        """
        activity_id = request.data.get('activity_id', None)
        selected_activity = self.get_selected_activity(activity_id)
        with transaction.atomic():
            try:
                if selected_activity.assigned_officer:
                    selected_activity.assigned_officer = None
                    selected_activity.save()
                    # Create a log entry for the application
                    self.log_user_action(
                        ApplicationUserAction.ACTION_UNASSIGN_OFFICER.format(
                            self.id), request)
            except BaseException:
                raise

    def return_to_officer_conditions(self, request, activity_id):
        selected_activity = self.get_selected_activity(activity_id)
        text = request.data.get('text', '')
        if selected_activity.assigned_officer:
            email_list = [selected_activity.assigned_officer.email]
        else:
            officer_groups = ActivityPermissionGroup.objects.filter(
                permissions__codename='licensing_officer',
                licence_activities__id=activity_id
            )
            group_users = EmailUser.objects.filter(
                groups__id__in=officer_groups.values_list('id', flat=True)
            ).distinct()
            email_list = [user.email for user in group_users]

        self.set_activity_processing_status(
            activity_id,
            ApplicationSelectedActivity.PROCESSING_STATUS_OFFICER_CONDITIONS
        )
        send_application_return_to_officer_conditions_notification(
            email_list=email_list,
            application=self,
            text=text,
            request=request
        )

    def get_assessor_permission_group(
                    self, user, activity_id=None, first=True):
        app_label = get_app_label()
        qs = user.groups.filter(
            permissions__codename='assessor'
        )
        if activity_id is not None:
           qs = qs.filter(
                activitypermissiongroup__licence_activities__id__in=activity_id if isinstance(
                    activity_id, (list, models.query.QuerySet)
                ) else [activity_id]
           )
        if app_label:
            qs = qs.filter(permissions__content_type__app_label=app_label)
        return qs.first() if first else qs

    def assign_application_assessment(self, request):
        with transaction.atomic():
            try:
                assessment_id = request.data.get('assessment_id')
                assessor_id = request.data.get('assessor_id')

                assessment = Assessment.objects.filter(
                    id=assessment_id,
                    application=self
                ).first()

                if not assessment:
                    raise Exception("Assessment record ID %s \
                    does not exist!" % (assessment_id))

                assessor_group = self \
                    .get_assessor_permission_group(
                        request.user,
                        activity_id=assessment.licence_activity_id,
                        first=True
                    )
                if not assessor_group:
                    raise Exception("Missing assessor permissions for Activity \
                        ID: %s" % (assessment.licence_activity_id))

                # Set the actioner and assessor for the action.
                assessor = EmailUser.objects \
                    .get(id=assessor_id) if assessor_id else assessor_id
                assessment.actioned_by = request.user
                assessment.assigned_assessor = assessor
                assessment.save()
                # Log application action
                if (assessor):
                    self.log_user_action(
                        ApplicationUserAction.ACTION_ASSESSMENT_ASSIGNED
                        .format(assessment.assessor_group,
                                assessor.get_full_name()),
                        request)
                else:
                    self.log_user_action(
                        ApplicationUserAction.ACTION_ASSESSMENT_UNASSIGNED
                        .format(assessment.assessor_group), request)

            except BaseException:
                raise

    def complete_application_assessments_by_user(self, request):
        '''
        Method to complete all assessments which are assigned to the current
        user within the current users permissions group.
        '''
        with transaction.atomic():
            try:
                activity_id = request.data.get('activity_id', None)
                final_comment = request.data.get('final_comment', None)
                assessments = Assessment.objects.filter(
                    status=Assessment.STATUS_AWAITING_ASSESSMENT,
                    application=self,
                    licence_activity_id__in=activity_id
                )

                # select each assessment on application.
                for assessment in assessments:

                    # check user has assessor permission
                    assessor_group = \
                        self.get_assessor_permission_group(
                            request.user,
                            activity_id=assessment.licence_activity_id,
                            first=True
                        )
                    if not assessor_group:
                        continue

                    assessment.final_comment = final_comment
                    assessment.status = Assessment.STATUS_COMPLETED
                    assessment.actioned_by = request.user
                    assessment.assigned_assessor = None
                    assessment.save()

                    # send email notification
                    select_group = self.licence_officers.all()
                    send_assessment_completed_email(
                        select_group,
                        assessment,
                        request)

                    # Log application action
                    self.log_user_action(
                        ApplicationUserAction.ACTION_ASSESSMENT_COMPLETE
                        .format(assessor_group), request)

                    # Log entry for organisation
                    if self.org_applicant:
                        self.org_applicant.log_user_action(
                            ApplicationUserAction.ACTION_ASSESSMENT_COMPLETE
                            .format(assessor_group), request)

                    elif self.proxy_applicant:
                        self.proxy_applicant.log_user_action(
                            ApplicationUserAction.ACTION_ASSESSMENT_COMPLETE
                            .format(assessor_group), request)

                    else:
                        self.submitter.log_user_action(
                            ApplicationUserAction.ACTION_ASSESSMENT_COMPLETE
                            .format(assessor_group), request)

                    self.check_assessment_complete(
                        assessment.licence_activity_id)
            except BaseException:
                raise

    def complete_assessment(self, request):
        with transaction.atomic():
            try:
                assessment_id = request.data.get('assessment_id')
                activity_id = int(request.data.get('selected_assessment_tab', 0))

                assessment = Assessment.objects.filter(
                    id=assessment_id,
                    licence_activity_id=activity_id,
                    status=Assessment.STATUS_AWAITING_ASSESSMENT,
                    application=self
                ).first()

                if not assessment:
                    raise Exception("Assessment record ID %s (activity: %s) does not exist!" % (
                        assessment_id, activity_id))

                assessor_group = self.get_assessor_permission_group(
                    request.user,
                    activity_id=assessment.licence_activity_id,
                    first=True
                )
                if not assessor_group:
                    raise Exception("Missing assessor permissions for Activity ID: %s" % (
                        assessment.licence_activity_id))

                assessment.status = Assessment.STATUS_COMPLETED
                assessment.actioned_by = request.user
                assessment.save()

                # Send email notification
                select_group = self.licence_officers.all()
                send_assessment_completed_email(
                    select_group, assessment, request)

                # Log application action
                self.log_user_action(
                    ApplicationUserAction.ACTION_ASSESSMENT_COMPLETE.format(assessor_group), request)
                # Log entry for organisation
                if self.org_applicant:
                    self.org_applicant.log_user_action(
                        ApplicationUserAction.ACTION_ASSESSMENT_COMPLETE.format(assessor_group), request)
                elif self.proxy_applicant:
                    self.proxy_applicant.log_user_action(
                        ApplicationUserAction.ACTION_ASSESSMENT_COMPLETE.format(assessor_group), request)
                else:
                    self.submitter.log_user_action(
                        ApplicationUserAction.ACTION_ASSESSMENT_COMPLETE.format(assessor_group), request)

                self.check_assessment_complete(activity_id)
            except BaseException:
                raise

    def check_assessment_complete(self, activity_id):
        # check if this is the last assessment for current
        # application, Change the processing status only if it is the
        # last assessment
        if not Assessment.objects.filter(
                application=self,
                licence_activity=activity_id,
                status=Assessment.STATUS_AWAITING_ASSESSMENT).exists():
            for activity in self.licence_type_data['activity']:
                if activity_id == activity["id"]:
                    self.set_activity_processing_status(
                        activity["id"], ApplicationSelectedActivity.PROCESSING_STATUS_OFFICER_CONDITIONS)

    def proposed_decline(self, request, details):
        with transaction.atomic():
            try:
                activity_list = details.get('activity')
                incorrect_statuses = ApplicationSelectedActivity.objects.filter(
                    application_id=self.id,
                    licence_activity_id__in=activity_list
                ).exclude(
                    processing_status=ApplicationSelectedActivity.PROCESSING_STATUS_OFFICER_CONDITIONS
                ).first()

                if incorrect_statuses:
                    raise ValidationError(
                        'You cannot propose for licence if it is not with officer for conditions')

                ApplicationSelectedActivity.objects.filter(
                    application_id=self.id,
                    licence_activity_id__in=activity_list
                ).update(
                    updated_by=request.user,
                    proposed_action=ApplicationSelectedActivity.PROPOSED_ACTION_DECLINE,
                    processing_status=ApplicationSelectedActivity.PROCESSING_STATUS_OFFICER_FINALISATION,
                    reason=details.get('reason'),
                    cc_email=details.get('cc_email', None),
                )

                # Log application action
                self.log_user_action(
                    ApplicationUserAction.ACTION_PROPOSED_DECLINE.format(
                        self.id), request)
                # Log entry for organisation
                if self.org_applicant:
                    self.org_applicant.log_user_action(
                        ApplicationUserAction.ACTION_PROPOSED_DECLINE.format(
                            self.id), request)
                elif self.proxy_applicant:
                    self.proxy_applicant.log_user_action(
                        ApplicationUserAction.ACTION_PROPOSED_DECLINE.format(
                            self.id), request)
                else:
                    self.submitter.log_user_action(
                        ApplicationUserAction.ACTION_PROPOSED_DECLINE.format(
                            self.id), request)
            except BaseException:
                raise

    def send_to_assessor(self, request):
        with transaction.atomic():
            try:
                Assessment.objects.update_or_create(
                    application=self,
                    officer=request.user,
                    reason=request.data.get('reason'),
                )

                # Log application action
                self.log_user_action(
                    ApplicationUserAction.ACTION_SEND_FOR_ASSESSMENT_TO_.format(
                        self.id), request)
            except BaseException:
                raise

    @property
    def amendment_requests(self):
        return AmendmentRequest.objects.filter(application=self)

    @property
    def active_amendment_requests(self):
        activity_ids = self.activities.values_list('licence_activity_id', flat=True)
        return self.amendment_requests.filter(licence_activity_id__in=activity_ids)

    @property
    def has_amended_fees(self):
        """
        Check on previous invoice amounts for difference in application fee.
        (on serializer)
        TODO: Redundant.
        """
        # fees_amended = False
        # # Application amendments requires a new submission and applies the
        # # previous paid for adjustments.
        # paid = self.total_paid_amount + self.previous_paid_amount
        # if paid > 0 and paid < self.application_fee:
        #     fees_amended = True

        return False

    @property
    def has_adjusted_fees(self):
        '''
        Check for adjustments to the application form causing a change to the
        application fee.
        '''
        adjusted_fees = [
            a.id for a in self.activities if a.has_adjusted_application_fee]

        return True if adjusted_fees.__len__ > 0 else False

    @property
    def has_additional_fees(self):
        """
        Check for additional costs manually included by officer at proposal.
        """
        additional_fees = [a.id for a in self.activities if a.additional_fee>0]

        return True if additional_fees.__len__ > 0 else False

    @property
    def additional_fees(self):
        """
        Total additional costs manually included by officer at proposal.
        """
        fees = 0
        for a in self.activities:
            fees = fees + a.additional_fee

        return Decimal(fees)

    # @property
    # def amended_activities(self):
    #     """
    #     Sets the application fee for each activity with a new amended amount
    #     based on the difference already paid.

    #     TODO: Redundant.
    #     """
    #     def on_licence_amend():
    #         """
    #         Determines amended amount from already paid on previous
    #         """
    #         amended = []
    #         previous = self.previous_application
    #         if not previous.latest_invoice:
    #             return amended
    #         latest_inv = previous.latest_invoice
    #         app_inv = ApplicationInvoice.objects.filter(
    #             invoice_reference=latest_inv.reference).first()
    #         for activity in self.selected_activities.all():
    #             invoice_line = ApplicationInvoiceLine.objects.filter(
    #                 invoice=app_inv,
    #                 licence_activity=activity.licence_activity).first()
    #             inv_amount = previous.activity_invoice_amount(activity)

    #             if activity.application_fee != inv_amount:
    #                 activity.application_fee = activity.application_fee \
    #                     + activity.base_fees['application']

    #             if (invoice_line and activity.application_fee > inv_amount):
    #                 difference = activity.application_fee - inv_amount
    #                 activity.application_fee = difference
    #                 amended.append(activity)

    #         return amended

    #     def on_request_amend():
    #         """
    #         Determines amended amount from already paid on current application.
    #         """
    #         amended = []
    #         if not self.latest_invoice:
    #             return amended
    #         latest_inv = self.latest_invoice
    #         app_inv = ApplicationInvoice.objects.filter(
    #             invoice_reference=latest_inv.reference).first()

    #         for activity in self.selected_activities.all():
    #             invoice_line = ApplicationInvoiceLine.objects.filter(
    #                 invoice=app_inv,
    #                 licence_activity=activity.licence_activity).first()
    #             inv_amount = self.activity_invoice_amount(activity)

    #             if activity.application_fee != inv_amount:
    #                 activity.application_fee = activity.application_fee \
    #                     + activity.base_fees['application']

    #             if (invoice_line and activity.application_fee > inv_amount):
    #                 difference = activity.application_fee - inv_amount
    #                 activity.application_fee = difference
    #                 amended.append(activity)             

    #         return amended

    #     amended = []
    #     # check for Customer licence amendment.
    #     if self.application_type == Application.APPLICATION_TYPE_AMENDMENT:
    #         amended = on_licence_amend()
    #     else:
    #         amended = on_request_amend()
    #     return amended

    # @property
    # def activity_invoice_amount(self, activity):
    #     """
    #     Gets the total amount paid for an activity across multiple invoices.

    #     TODO: Redundant.
    #     """
    #     amount = 0
    #     invoices = ApplicationInvoice.objects.filter(application_id=self.id)
    #     for invoice in invoices:
    #         line = ApplicationInvoiceLine.objects.filter(
    #             invoice=invoice,
    #             licence_activity=activity.licence_activity).first()
    #         amount += line.amount if line else 0

    #     return amount

    @property
    def requires_refund(self):
        """
        Check on the previously paid invoice amount against application fee.
        Refund is required when application fee is more than what has been
        paid. Application fee amount can be adjusted more or less than base.

        FIXME: The previous paid amount now excludes the licence fee.
        """
        ignore = [
            Application.CUSTOMER_STATUS_ACCEPTED,
            Application.CUSTOMER_STATUS_AWAITING_PAYMENT,
            Application.CUSTOMER_STATUS_DRAFT,
            Application.CUSTOMER_STATUS_AMENDMENT_REQUIRED,
        ]

        if self.customer_status in ignore or self.application_fee > -1:
            return False

        over_paid = self.get_refund_amount()

        return True if over_paid > 0 else False

    def get_refund_amount(self):
        """
        Get refund amount for this application.
        """
        paid = self.total_paid_amount
        fees_app_tot = 0
        fees_lic_tot = 0
        for activity in self.activities:
            fees_app = 0
            fees_adj = 0
            fees_lic = 0
            for p in activity.proposed_purposes.all():
                fees_adj += p.adjusted_fee
                fees_app += p.application_fee
                fees_lic += p.licence_fee
                has_purpose = True
            fees_app = fees_app + fees_adj
            fees_app_tot += fees_app
            fees_lic_tot += fees_lic

        over_paid = paid - fees_app_tot - fees_lic_tot

        return over_paid if over_paid > 0 else 0

    def alert_for_refund(self, request):
        """
        Send notification if refund exists.
        """
        if self.requires_refund:           
            officer_groups = ActivityPermissionGroup.objects.filter(
                permissions__codename='licensing_officer',
                licence_activities__purpose__licence_category__id=self.licence_type_data["id"]
            )
            group_users = EmailUser.objects.filter(
                groups__id__in=officer_groups.values_list('id', flat=True)
            ).distinct()
            send_amendment_refund_email_notification(group_users, self, request)

    @property
    def previous_paid_amount(self):
        """
        Gets the paid amount from the previous application for application
        amendments which require a new submission.

        NOTE: New application fee is required for ammendments.
        """
        def previous_paid_under_review(previous_paid):
            """
            Under Review an Application Ammendment cannot get a refund amount
            triggered by internal officers change to Application. Previous
            paid will be zero.
            """
            if self.processing_status ==\
                Application.PROCESSING_STATUS_UNDER_REVIEW:
                # apply the total_paid_amount as application fee is paid.
                if not previous_paid > self.application_fee:
                    previous_paid = self.application_fee - previous_paid
                else:
                    previous_paid = 0
                
            return previous_paid

        previous_paid = 0
        for activity in self.selected_activities.all():
            previous_paid += activity.previous_paid_amount
            # check for Customer licence amendment.
            if self.application_type == Application.APPLICATION_TYPE_AMENDMENT:
                # ignore refunds triggered by internal officers change.
                # previous_paid = previous_paid_under_review(previous_paid)
                pass

        return previous_paid

    @property
    def assessments(self):
        qs = Assessment.objects.filter(application=self)
        return qs

    @property
    def licences(self):
        from wildlifecompliance.components.licences.models import WildlifeLicence
        try:
            return WildlifeLicence.objects.filter(current_application=self)
        except WildlifeLicence.DoesNotExist:
            return WildlifeLicence.objects.none()

    @property
    def required_fields(self):
        return {key: data for key, data in self.schema_fields.items() if 'isRequired' in data and data['isRequired']}

    @property
    def schema_fields(self):
        return self.get_schema_fields(self.schema)

    @property
    def schema(self):
        return self.get_schema_for_purposes(
            self.licence_purposes.values_list('id', flat=True)
        )

    @property
    def data(self):
        """ returns a queryset of form data records attached to application (shortcut to ApplicationFormDataRecord related_name). """
        return self.form_data_records.all()

    @property
    def activities(self):
        """ returns a queryset of activities attached to application (shortcut to ApplicationSelectedActivity related_name). """
        return self.selected_activities.exclude(processing_status=ApplicationSelectedActivity.PROCESSING_STATUS_DISCARDED)

    def get_activity_chain(self, **activity_filters):
        activity_chain = self.selected_activities.filter(**activity_filters)
        return activity_chain | self.previous_application.get_activity_chain(
            **activity_filters
        ) if self.previous_application and self.previous_application != self else activity_chain

    def get_current_activity_chain(self, **activity_filters):
        '''
        Get chain of current activities by the expiry date.
        '''
        a_chain = self.selected_activities.filter(**activity_filters)
        # TODO:AYN may only want to chain active activities.
        # if a_chain.count() > 0:
        #     a_chain = [a for a in a_chain if a.is_current]
        a_chain = a_chain | self.previous_application.get_activity_chain(
            **activity_filters
        ) if self.previous_application and self.previous_application != self\
            else a_chain

        if self.licence_id:
            apps = Application.objects.filter(licence_id=self.licence_id)
            a_chain = self.selected_activities.filter(**activity_filters)
            for app in apps:
                a_chain = a_chain | app.selected_activities.filter(
                    **activity_filters)

        return a_chain

    def get_application_children(self):
        application_self_queryset = Application.objects.filter(id=self.id)
        return application_self_queryset | self.previous_application.get_application_children()\
            if self.previous_application and self.previous_application != self\
            else application_self_queryset

    def get_latest_current_activity_ordered(self, activity_id):
        '''
        Get the last issued activity from all previous applications associated
        with this selected application by ordering on Issue Date.

        NOTE: Issue date is for Activity Purpose and not Activity. The result
        may be incorrect.
        '''
        return self.get_activity_chain(
            licence_activity_id=activity_id,
            activity_status=ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT
        ).order_by(
            '-issue_date'
        ).first()

    def get_latest_current_activity(self, activity_id):
        '''
        Get the last issued activity from all previous applications with
        current activities associated with this selected application purpose.
        '''
        latest_activity = None
        a_chain = self.get_current_activity_chain(
            licence_activity_id=activity_id,
            activity_status=ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT
        )
        # Check each licence purpose on the chain to find the last issued
        # Licence Activity Purpose.
        issue_date = datetime.datetime.strptime('1901-01-01', '%Y-%m-%d')
        self_activity = [
            a for a in self.activities if a.licence_activity_id == activity_id]

        for self_p in self_activity[0].purposes:
            for a in a_chain:
                issued_p = [
                    p for p in a.proposed_purposes.all() if p.purpose == self_p
                ]

                if len(issued_p) > 0:
                    try:
                        i_itime = datetime.datetime.strptime(
                            issue_date.strftime('%Y-%m-%d'), 
                            '%Y-%m-%d'
                        )
                        a_issue_date = issued_p[0].issue_date
                        a_itime = datetime.datetime.strptime(
                            a_issue_date.strftime('%Y-%m-%d'),
                            '%Y-%m-%d'
                        )
                        latest_activity = \
                            a if a_itime > i_itime else latest_activity
                        issue_date = issued_p[0].issue_date

                    except BaseException as e:
                        logger.info(
                            'get_latest_current_activity: {0}'.format(e))

        return latest_activity

    def get_schema_fields_for_purposes(self, purpose_id_list):
        return self.get_schema_fields(
            self.get_schema_for_purposes(purpose_id_list)
        )

    def get_schema_for_purposes(self, purpose_id_list):
        from wildlifecompliance.components.applications.utils \
            import ActivitySchemaUtil
        util = ActivitySchemaUtil(self)
        return util.get_activity_schema(purpose_id_list)

    def get_schema_fields(self, schema_json):
        fields = {}

        def iterate_children(schema_group, fields, parent={}, parent_type='', condition={}, activity_id=None, purpose_id=None):
            children_keys = [
                'children',
                'header',
                'expander',
                'conditions',
            ]
            container = {
                i: schema_group[i] for i in range(len(schema_group))
            } if isinstance(schema_group, list) else schema_group

            for key, item in container.items():

                try:
                    activity_id = item['id']
                except BaseException:
                    pass

                try:
                    purpose_id = item['purpose_id']
                except BaseException:
                    pass

                if isinstance(item, list):
                    if parent_type == 'conditions':
                        condition[parent['name']] = key
                    iterate_children(item, fields, parent, parent_type, condition, activity_id, purpose_id)
                    continue

                name = item['name']
                fields[name] = {}
                fields[name].update(item)
                fields[name]['condition'] = {}
                fields[name]['condition'].update(condition)
                fields[name]['licence_activity_id'] = activity_id
                fields[name]['licence_purpose_id'] = purpose_id

                for children_key in children_keys:
                    if children_key in fields[name]:
                        del fields[name][children_key]
                        iterate_children(item[children_key], fields, fields[name], children_key, condition, activity_id, purpose_id)
                condition = {}

        iterate_children(schema_json, fields)

        return fields

    def get_visible_form_data_tree(self, form_data_records=None):
        data_tree = {}
        schema_fields = self.schema_fields

        if form_data_records is None:
            form_data_records = [(record.field_name, {
                'schema_name': record.schema_name,
                'instance_name': record.instance_name,
                'value': record.value,
            }) for record in self.form_data_records.all()]

        for field_name, item in form_data_records:
            instance = item['instance_name']
            schema_name = item['schema_name']

            if instance not in data_tree:
                data_tree[instance] = {}
            data_tree[instance][schema_name] = item['value']

        for instance, schemas in data_tree.items():
            for schema_name, item in schemas.items():
                if schema_name not in schema_fields:
                    continue
                schema_data = schema_fields[schema_name]
                for condition_field, condition_value in schema_data['condition'].items():
                    if condition_field in schemas and schemas[condition_field] != condition_value:
                        try:
                            del data_tree[instance][schema_name]
                        except KeyError:
                            continue

        return data_tree

    def get_licences_by_status(self, status):
        return self.licences.filter(current_application__selected_activities__activity_status=status).distinct()

    def get_proposed_decisions(self, request):
        with transaction.atomic():
            try:
                proposed_states = [ApplicationSelectedActivity.PROPOSED_ACTION_DECLINE,
                                   ApplicationSelectedActivity.PROPOSED_ACTION_ISSUE
                                   ]
                qs = ApplicationSelectedActivity.objects.filter(
                    application=self, proposed_action__in=proposed_states)
                for q in qs:
                    if ApplicationSelectedActivity.objects.filter(
                            application=self,
                            licence_activity=q.licence_activity,
                            decision_action__isnull=False).exists():
                        qs.exclude(id=q.id)
                return qs
            except BaseException:
                raise

    def proposed_licence(self, request, details):
        with transaction.atomic():
            try:
                activity_list = []
                purpose_list = request.data.get('purposes')
                for p in purpose_list:
                    # build activity_id list from purposes.
                    purpose = LicencePurpose.objects.get(id=p['id'])
                    activity_list.append(purpose.licence_activity_id)
                activity_list = list(set(activity_list)) # unique ids

                # Correct processing status if no assessments were required.
                for activity in activity_list:
                    self.check_assessment_complete(activity)

                incorrect_statuses = ApplicationSelectedActivity.objects.filter(
                    application_id=self.id,
                    licence_activity_id__in=activity_list
                ).exclude(
                    processing_status=ApplicationSelectedActivity.PROCESSING_STATUS_OFFICER_CONDITIONS
                ).first()

                if incorrect_statuses:
                    raise ValidationError(
                        'You cannot propose for licence if it is not with officer for conditions')

                if self.application_type == Application.APPLICATION_TYPE_AMENDMENT:
                    # Pre-populate proposed issue dates with dates from the currently active licence.
                    for activity_id in activity_list:
                        latest_activity = self.get_latest_current_activity(activity_id)
                        if not latest_activity:
                            raise Exception("Active licence not found for activity ID: %s" % activity_id)

                        activity = self.activities.get(
                            licence_activity_id=activity_id
                        )
                        activity.updated_by = request.user
                        activity.proposed_action = ApplicationSelectedActivity.PROPOSED_ACTION_ISSUE
                        activity.processing_status = ApplicationSelectedActivity.PROCESSING_STATUS_OFFICER_FINALISATION
                        activity.reason = details.get('reason')
                        activity.cc_email = details.get('cc_email', None)

                        # TODO:AYN Update ActivityPurposes with dates for 
                        # activity then propsed start date can be start date 
                        # for the activity instead of latest_activity.
                        for p in purpose_list:
                            # update Application Selected Activity Purposes
                            lp = LicencePurpose.objects.get(id=p['id'])
                            issued = latest_activity.proposed_purposes.filter(
                                purpose=lp
                            ).first()
                            status = 'issue' if p['isProposed'] else 'decline'

                            purpose, c = ApplicationSelectedActivityPurpose.objects.get_or_create(
                                purpose=issued.purpose,
                                selected_activity=activity,
                            )
                            purpose.processing_status = status
                            purpose.start_date = issued.start_date
                            purpose.expiry_date = issued.expiry_date
                            purpose.original_issue_date = \
                                issued.original_issue_date
                            purpose.issue_date = issued.issue_date
                            purpose.save()

                        prev_start_date = activity.get_start_date()
                        prev_expiry_date = activity.get_expiry_date()
                        activity.proposed_start_date = prev_start_date
                        activity.proposed_end_date = prev_expiry_date

                        # update Additional fees for selected proposed 
                        # activities.
                        proposed_activities = request.data.get('activities')
                        proposed = [a for a in proposed_activities if a[
                            'id'] == activity.id]

                        if proposed[0]:
                            activity.additional_fee=proposed[0][
                                'additional_fee'] if proposed[0][
                                    'additional_fee'] else 0
                            activity.additional_fee_text=proposed[0][
                                'additional_fee_text'] if proposed[0][
                                    'additional_fee'] > 0 else None

                        activity.save()
                                 
                else:
                    ApplicationSelectedActivity.objects.filter(
                        application_id=self.id,
                        licence_activity_id__in=activity_list
                    ).update(
                        updated_by=request.user,
                        proposed_action=ApplicationSelectedActivity.PROPOSED_ACTION_ISSUE,
                        processing_status=ApplicationSelectedActivity.PROCESSING_STATUS_OFFICER_FINALISATION,
                        reason=details.get('reason'),
                        cc_email=details.get('cc_email', None),
                        proposed_start_date=details.get('start_date', None),
                        proposed_end_date=details.get('expiry_date', None),
                    )
                    # update Additional fees for selected proposed activities.
                    proposed_activities = request.data.get('activities')
                    for p_activity in proposed_activities:
                        activity = self.activities.get(id=p_activity['id'])
                        activity.additional_fee=p_activity[
                            'additional_fee'] if p_activity[
                                'additional_fee'] else 0
                        activity.additional_fee_text=p_activity[
                            'additional_fee_text'] if p_activity[
                                'additional_fee'] > 0 else None
                        activity.save()

                    # update Application Selected Activity Purposes
                    for p in purpose_list:
                        purpose = LicencePurpose.objects.get(id=p['id'])
                        activity = self.activities.get(
                            licence_activity_id = purpose.licence_activity_id
                        )
                        status = 'issue' if p['isProposed'] else 'decline'
                        activity_purpose = ApplicationSelectedActivityPurpose.objects.get_or_create(
                            purpose=purpose,
                            selected_activity=activity,
                        )
                        activity_purpose[0].processing_status = status
                        activity_purpose[0].save()

                # Email licence approver group of proposed action.
                attachments_id = request.data.get('email_attachments_id')
                documents = []
                attachments = None
                if attachments_id:
                    attachments = \
                        get_temporary_document_collection(attachments_id)
                    for document in attachments.documents.all():
                        content = document._file.read()
                        mime = mimetypes.guess_type(document.name)[0]
                        documents.append((document.name, content, mime))                        

                email_text=str(details.get('approver_detail'))
                send_activity_propose_issue_notification(
                   request, self, email_text, documents
                )
                if attachments:
                    attachments.delete()

                # save temporary documents to all ApplicationSelectedActivity 
                # instances checked in the modal
                issuance_documents_id = request.data.get('issuance_documents_id', {}).get('temp_doc_id')
                application_selected_activities = request.data.get('activity')
                asa = [activity for activity in self.activities if activity.id in application_selected_activities]
                if issuance_documents_id:
                        issuance_documents_collection, created = TemporaryDocumentCollection.objects.get_or_create(
                                id=issuance_documents_id)
                        if issuance_documents_collection:
                            for doc in issuance_documents_collection.documents.all():
                                #save_comms_log_document_obj(instance, workflow_entry, doc)
                                for application_selected_activity in asa:
                                    save_issuance_document_obj(application_selected_activity, doc)
                            issuance_documents_collection.delete()
                
                # log proposing officers comments and documents.

                # Log application action
                self.log_user_action(
                    ApplicationUserAction.ACTION_PROPOSED_LICENCE.format(
                        self.id), request)
                # Log entry for organisation
                if self.org_applicant:
                    self.org_applicant.log_user_action(
                        ApplicationUserAction.ACTION_PROPOSED_LICENCE.format(
                            self.id), request)
                elif self.proxy_applicant:
                    self.proxy_applicant.log_user_action(
                        ApplicationUserAction.ACTION_PROPOSED_LICENCE.format(
                            self.id), request)
                else:
                    self.submitter.log_user_action(
                        ApplicationUserAction.ACTION_PROPOSED_LICENCE.format(
                            self.id), request)
            except BaseException:
                raise

    def get_parent_licence(self, auto_create=True):
        from wildlifecompliance.components.licences.models import WildlifeLicence
        current_date = timezone.now().date()
        try:
            existing_licence = WildlifeLicence.objects.filter(
                Q(licence_category=self.get_licence_category()),
                Q(current_application__org_applicant_id=self.org_applicant_id) if self.org_applicant_id else (
                    Q(current_application__submitter_id=self.proxy_applicant_id,
                      current_application__org_applicant_id=None
                      ) | Q(current_application__proxy_applicant_id=self.proxy_applicant_id,
                            current_application__org_applicant_id=None)
                ) if self.proxy_applicant_id else Q(current_application__submitter_id=self.submitter_id,
                                                    current_application__org_applicant_id=None,
                                                    current_application__proxy_applicant_id=None)
            ).order_by('-id').distinct().first()
            if existing_licence:
                # Only load licence if any associated activities are still current or suspended.
                # TODO: get current activities in chain.
                # get_current_activity_chain()
                if not existing_licence.current_application.get_current_activity_chain(
                    activity_status__in=[
                        ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT,
                        ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED,
                    ]
                ).first():
                    raise WildlifeLicence.DoesNotExist
            else:
                raise WildlifeLicence.DoesNotExist
            return existing_licence, False
        except WildlifeLicence.DoesNotExist:
            if auto_create:
                return WildlifeLicence.objects.create(
                    current_application=self,
                    licence_category=self.get_licence_category()
                ), True
            else:
                return WildlifeLicence.objects.none(), False

    def reissue_activity(
        self, request, selected_activity, 
        parent_licence=None, generate_licence=False):
        """
        Process to allow a previously issued Activity to be updated and then
        Re-issued.
        1. Set Activity processing status to With Approver.
        2. Set Activity status to Current.
        3. Set Activity decision action to Re-issue.
        4. Set Application process status to Under Review.

        NOTE: Cannot reissue activity for a system generated application. These
        application cannot be processed by staff.
        """
        if not selected_activity.licence_fee_paid: # shouldn't occur if issued.
            raise Exception(
            "Cannot Reissue activity: licence fee has not been paid!")

        with transaction.atomic():
            try:
                selected_activity.processing_status = \
                    ApplicationSelectedActivity.PROCESSING_STATUS_OFFICER_FINALISATION

                if self.application_type == \
                   self.APPLICATION_TYPE_SYSTEM_GENERATED:
                   # System generated applications cannot be processed by staff
                   # therefore set as accepted.
                    selected_activity.processing_status = \
                        ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED                    

                selected_activity.activity_status = \
                    ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT
                selected_activity.decision_action = \
                    ApplicationSelectedActivity.DECISION_ACTION_REISSUE
                selected_activity.updated_by = request.user
                # Log application action
                self.log_user_action(
                    ApplicationUserAction.ACTION_REISSUE_LICENCE_.format(
                        selected_activity.licence_activity.name), request)
                # Log entry for organisation
                if self.org_applicant:
                    self.org_applicant.log_user_action(
                        ApplicationUserAction.ACTION_REISSUE_LICENCE_.format(
                            selected_activity.licence_activity.name), request)
                elif self.proxy_applicant:
                    self.proxy_applicant.log_user_action(
                        ApplicationUserAction.ACTION_REISSUE_LICENCE_.format(
                            selected_activity.licence_activity.name), request)
                else:
                    self.submitter.log_user_action(
                        ApplicationUserAction.ACTION_REISSUE_LICENCE_.format(
                            selected_activity.licence_activity.name), request)

                selected_activity.save()

            except BaseException:
                print(Exception)
                raise

    def issue_activity(self, request, selected_activity, parent_licence=None, generate_licence=False):

        if not selected_activity.licence_fee_paid:
            raise Exception("Cannot issue activity: licence fee has not been paid!")

        if parent_licence is None:
            parent_licence, created = self.get_parent_licence(auto_create=True)

        if not parent_licence:
            raise Exception("Cannot issue activity: licence not found!")

        latest_application_in_function = self
        application_selected_purpose_ids = self.licence_purposes.all().values_list('id', flat=True)
        licence_latest_activities_for_licence_activity_id = parent_licence.latest_activities.filter(
            licence_activity_id=selected_activity.licence_activity_id)

        with transaction.atomic():
            try:
                for existing_activity in licence_latest_activities_for_licence_activity_id:
                    # compare each activity's purposes and find the difference from
                    # the selected_purposes of the new application
                    issued_activity_purposes = application_selected_purpose_ids.filter(
                        licence_activity_id=selected_activity.licence_activity_id)
                    existing_activity_purposes = existing_activity.purposes.values_list('id', flat=True)
                    common_purpose_ids = list(set(existing_activity_purposes) & set(issued_activity_purposes))
                    remaining_purpose_ids_list = list(set(existing_activity_purposes) - set(issued_activity_purposes))

                    # No relevant purposes were selected for action for this existing activity, do nothing
                    if not common_purpose_ids:
                        pass

                    # If there are no remaining purposes in the existing_activity
                    # (i.e. this issued activity replaces them all),
                    # mark activity and purposes as replaced.
                    elif not remaining_purpose_ids_list:
                        existing_activity.updated_by = request.user
                        for p_id in common_purpose_ids:
                            existing_activity.mark_selected_purpose_as_replaced(
                                p_id
                            )
                        existing_activity.activity_status = ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED
                        existing_activity.save()

                    # If only a subset of the existing_activity's purposes are 
                    # to be actioned, create new_activity for remaining 
                    # purposes. New system generated application is created.
                    # TODO:AYN check system generated app created correctly.
                    elif remaining_purpose_ids_list:
                        existing_application = existing_activity.application
                        existing_activity_status = existing_activity.activity_status
                        new_copied_application = existing_application.copy_application_purposes_for_status(
                                                remaining_purpose_ids_list, existing_activity_status)

                        # for each new application created, set its previous_application to latest_application_in_function,
                        # then update latest_application_in_function to the new_copied_application
                        new_copied_application.previous_application = latest_application_in_function
                        new_copied_application.save()
                        latest_application_in_function = new_copied_application

                        # Mark existing_activity as replaced
                        existing_activity.updated_by = request.user
                        for p_id in common_purpose_ids:
                            existing_activity.mark_selected_purpose_as_replaced(
                                p_id
                            )
                        existing_activity.activity_status = ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED
                        existing_activity.save()

                selected_activity.processing_status = ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED
                selected_activity.activity_status = ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT

                self.generate_returns(parent_licence, selected_activity, request)
                # Log application action
                self.log_user_action(
                    ApplicationUserAction.ACTION_ISSUE_LICENCE_.format(
                        selected_activity.licence_activity.name), request)
                # Log entry for organisation
                if self.org_applicant:
                    self.org_applicant.log_user_action(
                        ApplicationUserAction.ACTION_ISSUE_LICENCE_.format(
                            selected_activity.licence_activity.name), request)
                elif self.proxy_applicant:
                    self.proxy_applicant.log_user_action(
                        ApplicationUserAction.ACTION_ISSUE_LICENCE_.format(
                            selected_activity.licence_activity.name), request)
                else:
                    self.submitter.log_user_action(
                        ApplicationUserAction.ACTION_ISSUE_LICENCE_.format(
                            selected_activity.licence_activity.name), request)

                selected_activity.save()

                # update the status of the application.
                self.update_customer_approval_status()

                parent_licence.current_application = latest_application_in_function
                parent_licence.save()

                if generate_licence:
                    # Re-generate PDF document using all finalised activities
                    parent_licence.generate_doc()
                    send_application_issue_notification(
                        activities=[selected_activity],
                        application=self,
                        request=request,
                        licence=parent_licence
                    )
                    # Attach the re-generated licence to latest application.
                    latest_application_in_function.licence_document \
                        = parent_licence.licence_document
                    latest_application_in_function.save()

            except BaseException:
                print(Exception)
                raise

    def final_decision(self, request):
        """
        Carry out the Final Issue/Decline decision for the Application (self)
        """
        failed_payment_activities = []

        with transaction.atomic():
            try:
                parent_licence, created = self.get_parent_licence(auto_create=True)
                issued_activities = []
                declined_activities = []

                # perform issue for each licence activity id in request.data.get('activity')
                for item in request.data.get('activity'):
                    licence_activity_id = item['id']
                    # use .get here as it should not be possible to have more than one activity per licence_activity_id
                    # per application
                    selected_activity = self.activities.get(licence_activity__id=licence_activity_id)
                    if not selected_activity:
                        raise Exception("Licence activity %s is missing from Application ID %s!" % (
                            licence_activity_id, self.id))

                    if selected_activity.processing_status not in [
                        ApplicationSelectedActivity.PROCESSING_STATUS_OFFICER_FINALISATION,
                        ApplicationSelectedActivity.PROCESSING_STATUS_AWAITING_LICENCE_FEE_PAYMENT,
                    ]:
                        raise Exception("Activity \"%s\" has an invalid processing status: %s" % (
                            selected_activity.licence_activity.name, selected_activity.processing_status))

                    # skip over activities already issued and awaiting payment.
                    if selected_activity.processing_status in [
                        ApplicationSelectedActivity.PROCESSING_STATUS_AWAITING_LICENCE_FEE_PAYMENT,
                    ]:
                        continue

                    if item['final_status'] == ApplicationSelectedActivity.DECISION_ACTION_ISSUED:
                        # TODO: set period dates for issuance on the Purpose
                        # for the selected Activity.

                        original_issue_date = start_date = item.get('start_date')
                        expiry_date = item.get('end_date')

                        if self.application_type in [
                            Application.APPLICATION_TYPE_AMENDMENT,
                            Application.APPLICATION_TYPE_REISSUE,
                        ]:
                            latest_activity = self.get_latest_current_activity(licence_activity_id)
                            if not latest_activity:
                                raise Exception("Active licence not found for activity ID: %s" % licence_activity_id)

                            if self.application_type ==\
                                Application.APPLICATION_TYPE_AMENDMENT:
                                # Populate start and expiry dates from the
                                # latest issued activity record.
                                # TODO: Set from the purpose dates
                                original_issue_date = \
                                    latest_activity.get_original_issue_date()
                                start_date = latest_activity.get_start_date()
                                expiry_date = latest_activity.get_expiry_date()

                        # Additional Fees need to be set before processing fee.
                        # Fee amount may change by the issuer making decision.
                        if item['additional_fee']:
                            selected_activity.additional_fee = \
                                Decimal(item['additional_fee'])
                            selected_activity.additional_fee_text = item[
                                'additional_fee_text']

                        # If there is an outstanding licence fee payment - attempt to charge the stored card.
                        payment_successful = selected_activity.process_licence_fee_payment(request, self)
                        if not payment_successful:
                            failed_payment_activities.append(selected_activity)
                        else:
                            issued_activities.append(selected_activity)
                            self.issue_activity(
                                request, selected_activity, 
                                parent_licence, generate_licence=False)

                        # Populate fields below even if the token payment has
                        # failed. They will be reused after a successful
                        # payment by the applicant.
                        selected_activity.assigned_approver = None
                        selected_activity.decision_action =\
                            ApplicationSelectedActivity.DECISION_ACTION_ISSUED
                        selected_activity.updated_by = request.user
                        selected_activity.cc_email = item['cc_email']
                        selected_activity.reason = item['reason']

                        selected_activity.set_original_issue_date(
                            original_issue_date)
                        selected_activity.set_issue_date(timezone.now())
                        selected_activity.set_start_date(start_date)
                        selected_activity.set_expiry_date(expiry_date)

                        proposed_purposes =\
                            selected_activity.proposed_purposes.all()
                        ISSUE = ApplicationSelectedActivityPurpose.PROCESSING_STATUS_ISSUED
                        DECLINE = ApplicationSelectedActivityPurpose.PROCESSING_STATUS_DECLINED
                        for proposed_purpose in proposed_purposes:
                            purpose =\
                                ApplicationSelectedActivityPurpose.objects.get(
                                    id=proposed_purpose.id
                                )
                            if proposed_purpose.purpose_id in item['purposes']:
                                purpose.processing_status = ISSUE
                                purpose.issue_date = timezone.now()
                            else:
                                purpose.processing_status = DECLINE
                            purpose.original_issue_date = original_issue_date
                            purpose.start_date = start_date
                            purpose.expiry_date = expiry_date
                            
                            purpose.save()

                        selected_activity.save()

                    elif item['final_status'] == ApplicationSelectedActivity.DECISION_ACTION_DECLINED:
                        selected_activity.assigned_approver = None
                        selected_activity.updated_by = request.user
                        selected_activity.processing_status = ApplicationSelectedActivity.PROCESSING_STATUS_DECLINED
                        selected_activity.decision_action = ApplicationSelectedActivity.DECISION_ACTION_ISSUED
                        selected_activity.cc_email = item['cc_email']
                        selected_activity.reason = item['reason']

                        proposed_purposes = selected_activity.proposed_purposes.all()
                        for proposed_purpose in proposed_purposes:
                            purpose = ApplicationSelectedActivityPurpose.objects.get(id=proposed_purpose.id)    
                            purpose.processing_status = ApplicationSelectedActivityPurpose.PROCESSING_STATUS_DECLINED
                            purpose.save()

                        selected_activity.save()
                        declined_activities.append(selected_activity)
                        # Log entry for application
                        self.log_user_action(
                            ApplicationUserAction.ACTION_DECLINE_LICENCE_.format(
                                item['name']), request)
                        # Log entry for org_applicant
                        if self.org_applicant:
                            self.org_applicant.log_user_action(
                                ApplicationUserAction.ACTION_DECLINE_LICENCE_.format(
                                    item['name']), request)
                        # Log entry for proxy_applicant
                        elif self.proxy_applicant:
                            self.proxy_applicant.log_user_action(
                                ApplicationUserAction.ACTION_DECLINE_LICENCE_.format(
                                    item['name']), request)
                        # Log entry for submitter
                        else:
                            self.submitter.log_user_action(
                                ApplicationUserAction.ACTION_DECLINE_LICENCE_.format(
                                    item['name']), request)

                if (issued_activities or failed_payment_activities) and not created:
                    parent_licence.licence_sequence += 1
                    parent_licence.save()

                if issued_activities:
                    # Re-generate PDF document using all finalised activities
                    parent_licence.generate_doc()
                    send_application_issue_notification(
                        activities=issued_activities,
                        application=self,
                        request=request,
                        licence=parent_licence
                    )
                    self.licence_document = parent_licence.licence_document
                    self.licence = parent_licence
                    self.save()
                # If there are no issued_activities in this application and the parent_licence was
                # created as part of this application (i.e. it was not a pre-existing one), delete it
                elif not issued_activities and created:
                    parent_licence.delete()

                if declined_activities:
                    send_application_decline_notification(
                        declined_activities, self, request)

            except BaseException:
                raise

        if failed_payment_activities:
            for activity in failed_payment_activities:
                activity.processing_status = ApplicationSelectedActivity.PROCESSING_STATUS_AWAITING_LICENCE_FEE_PAYMENT
                activity.save()
                # Notify customer of failed payment and set Application status for customer.
                self.customer_status = Application.CUSTOMER_STATUS_AWAITING_PAYMENT
                self.save()
                send_activity_invoice_issue_notification(self, activity, request)

        self.update_customer_approval_status()

    def update_customer_approval_status(self):
        # Update application customer approval status depending on count of 
        # approved/declined/unpaid activities.
        PAY = ApplicationSelectedActivity.PROCESSING_STATUS_AWAITING_LICENCE_FEE_PAYMENT
        ACCEPTED = ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED
        DECLINED = ApplicationSelectedActivity.PROCESSING_STATUS_DECLINED
        PARTIALLY_APPROVED = Application.CUSTOMER_STATUS_PARTIALLY_APPROVED
        AMEND = Application.CUSTOMER_STATUS_AMENDMENT_REQUIRED

        total_activity_count = self.selected_activities.count()

        approved_activity_count = self.selected_activities.filter(
            processing_status=ACCEPTED).count()

        declined_activity_count = self.selected_activities.filter(
            processing_status=DECLINED).count()

        unpaid_activity_count = self.selected_activities.filter(
            processing_status=PAY).count()

        request_amend_activity_count = self.active_amendment_requests.filter(
            status=AmendmentRequest.AMENDMENT_REQUEST_STATUS_REQUESTED).count()

        if 0 < approved_activity_count < total_activity_count:
            self.customer_status = PARTIALLY_APPROVED
        elif request_amend_activity_count > 0:
            self.customer_status = AMEND
        elif approved_activity_count == total_activity_count:
            self.customer_status = Application.CUSTOMER_STATUS_ACCEPTED
        elif declined_activity_count == total_activity_count:
            self.customer_status = Application.CUSTOMER_STATUS_DECLINED

        # override decision status if payment is pending.
        if unpaid_activity_count > 0:
            self.customer_status = Application.CUSTOMER_STATUS_AWAITING_PAYMENT

        self.save()

    def generate_returns(self, licence, selected_activity, request):

        # TODO: Delete any previously existing returns with default status
        # which may occur if this activity is being reissued or amended.
        from wildlifecompliance.components.returns.models import Return
        # licence_expiry = selected_activity.expiry_date
        # Returns are generated at issuing; expiry_date may not be set yet.
        licence_expiry = selected_activity.proposed_end_date
        licence_expiry = datetime.datetime.strptime(
            licence_expiry, "%Y-%m-%d"
        ).date() if isinstance(licence_expiry, six.string_types) else licence_expiry
        today = timezone.now().date()
        timedelta = datetime.timedelta
        for condition in self.conditions.all():
            try:
                if condition.return_type and condition.due_date and condition.due_date >= today:
                    current_date = condition.due_date
                    # create a first Return
                    try:
                        Return.objects.get(
                            condition=condition, due_date=current_date)
                    except Return.DoesNotExist:
                        Return.objects.create(
                            application=self,
                            due_date=current_date,
                            processing_status=Return.RETURN_PROCESSING_STATUS_FUTURE,
                            licence=licence,
                            condition=condition,
                            return_type=condition.return_type,
                            submitter=request.user
                        )
                        # compliance.log_user_action(ComplianceUserAction.ACTION_CREATE.format(compliance.id),request)
                    if condition.recurrence:
                        while current_date < licence_expiry:
                            for x in range(condition.recurrence_schedule):
                                # Weekly
                                if condition.recurrence_pattern == ApplicationCondition\
                                        .APPLICATION_CONDITION_RECURRENCE_WEEKLY:
                                            current_date += timedelta(weeks=1)
                            # Monthly
                                elif condition.recurrence_pattern == ApplicationCondition\
                                        .APPLICATION_CONDITION_RECURRENCE_MONTHLY:
                                            current_date += timedelta(weeks=4)
                                            pass
                            # Yearly
                                elif condition.recurrence_pattern == ApplicationCondition\
                                        .APPLICATION_CONDITION_RECURRENCE_YEARLY:
                                            current_date += timedelta(days=365)
                            # Create the Return
                            if current_date <= licence_expiry:
                                try:
                                    Return.objects.get(
                                        condition=condition, due_date=current_date)
                                except Return.DoesNotExist:
                                    Return.objects.create(
                                        application=self,
                                        due_date=current_date,
                                        processing_status=Return.RETURN_PROCESSING_STATUS_FUTURE,
                                        licence=licence,
                                        condition=condition,
                                        return_type=condition.return_type
                                    )
            except BaseException:
                raise

    @staticmethod
    def calculate_base_fees(selected_purpose_ids):
        from wildlifecompliance.components.licences.models import LicencePurpose

        base_fees = {
            'application': Decimal(0.0),
            'licence': Decimal(0.0),
        }

        for purpose in LicencePurpose.objects.filter(id__in=selected_purpose_ids):
            base_fees['application'] += purpose.base_application_fee
            base_fees['licence'] += purpose.base_licence_fee

        return base_fees

    @staticmethod
    def get_activity_date_filter(for_application_type, prefix=''):
        current_date = timezone.now().date()
        date_filter = {
            '{}expiry_date__isnull'.format(prefix): False,
            '{}expiry_date__gte'.format(prefix): current_date
        }
        if for_application_type == Application.APPLICATION_TYPE_RENEWAL:
            expires_at = current_date + datetime.timedelta(days=settings.RENEWAL_PERIOD_DAYS)
            date_filter = {
                '{}expiry_date__isnull'.format(prefix): False,
                '{}expiry_date__gte'.format(prefix): current_date,
                '{}expiry_date__lte'.format(prefix): expires_at,
            }
        return date_filter

    @staticmethod
    def get_active_licence_activities(request, for_application_type=APPLICATION_TYPE_NEW_LICENCE):
        applications = Application.get_active_licence_applications(request, for_application_type)
        return ApplicationSelectedActivity.get_current_activities_for_application_type(
            for_application_type,
            applications=applications
        )

    @staticmethod
    def get_active_licence_applications(
            request, for_application_type=APPLICATION_TYPE_NEW_LICENCE):
        '''
        Returns a filtered list of applications for the user/proxy/org
        applicant where application's selected activities are CURRENT OR
        SUSPENDED.

        NOTE: used when creating new application to check applicant for 
        open applications. 
        '''
        date_filter = Application.get_activity_date_filter(
            for_application_type)

        activities = None
        # TODO: date_filter applies expiry_date
        applications = Application.get_request_user_applications(request).filter(
            selected_activities__activity_status__in=[
                ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT,
                ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED,
            ],
            # **date_filter
        ).distinct()

        activities = applications.filter().values_list('selected_activities__id', flat=True)
        a_ids = ApplicationSelectedActivityPurpose.objects.filter(
            # Apply the date filtering on the Purposes.
            selected_activity_id__in=activities,
            **date_filter
        ).values_list('selected_activity_id', flat=True)
        applications = applications.filter(
            selected_activities__id__in=a_ids
        )

        return applications

    @staticmethod
    def get_open_applications(request):
        return Application.get_request_user_applications(request).exclude(
            selected_activities__processing_status__in=[
                ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED,
                ApplicationSelectedActivity.PROCESSING_STATUS_DECLINED,
                ApplicationSelectedActivity.PROCESSING_STATUS_DISCARDED
            ]
        ).distinct()

    @staticmethod
    def get_request_user_proxy_details(request):
        proxy_id = request.data.get(
            "proxy_id",
            request.GET.get("proxy_id")
        )
        organisation_id = request.data.get(
            "organisation_id",
            request.GET.get("organisation_id")
        )
        return Application.validate_request_user_proxy_details(request, proxy_id, organisation_id)

    @staticmethod
    def get_request_user_permission_group(request, permission_codename, activity_id=None, first=True):
        try:
            app_label = settings.SYSTEM_APP_LABEL
        except AttributeError:
            app_label = ''
        qs = request.user.groups.filter(
            permissions__codename=permission_codename
        )
        if activity_id is not None:
            qs = qs.filter(
                activitypermissiongroup__licence_activities__id__in=activity_id if isinstance(
                    activity_id, (list, models.query.QuerySet)
                ) else [activity_id]
            )
        if app_label:
            qs = qs.filter(permissions__content_type__app_label=app_label)
        return qs.first() if first else qs

    @staticmethod
    def validate_request_user_proxy_details(request, proxy_id, organisation_id):
        proxy_details = {
            'proxy_id': proxy_id,
            'organisation_id': organisation_id,
        }

        if not proxy_id and not organisation_id:
            return proxy_details

        # Only licensing officers can apply as a proxy
        if not Application.get_request_user_permission_group(
            permission_codename='licensing_officer',
            first=True
        ):
            proxy_details['proxy_id'] = None

        user = EmailUser.objects.get(pk=proxy_id) if proxy_details['proxy_id'] else request.user
        if organisation_id and not user.wildlifecompliance_organisations.filter(pk=organisation_id):
            proxy_details['organisation_id'] = None

        return proxy_details

    @staticmethod
    def get_request_user_applications(request):
        proxy_details = Application.get_request_user_proxy_details(request)
        proxy_id = proxy_details.get('proxy_id')
        organisation_id = proxy_details.get('organisation_id')
        return Application.objects.filter(
            Q(org_applicant_id=organisation_id) if organisation_id
            else (
                Q(submitter=proxy_id) | Q(proxy_applicant=proxy_id)
            ) if proxy_id
            else Q(submitter=request.user, proxy_applicant=None, org_applicant=None)
        )


class ApplicationInvoice(models.Model):
    PAYMENT_STATUS_NOT_REQUIRED = 'payment_not_required'
    PAYMENT_STATUS_UNPAID = 'unpaid'
    PAYMENT_STATUS_PARTIALLY_PAID = 'partially_paid'
    PAYMENT_STATUS_PAID = 'paid'
    PAYMENT_STATUS_OVERPAID = 'over_paid'

    application = models.ForeignKey(Application, related_name='invoices')
    invoice_reference = models.CharField(
        max_length=50, null=True, blank=True, default='')
    invoice_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return 'Application {} : Invoice #{}'.format(
            self.application_id, self.invoice_reference)

    # Properties
    # ==================
    @property
    def active(self):
        try:
            invoice = Invoice.objects.get(reference=self.invoice_reference)
            return False if invoice.voided else True
        except Invoice.DoesNotExist:
            pass
        return False

class ApplicationInvoiceLine(models.Model):
    invoice = models.ForeignKey(
        ApplicationInvoice, related_name='application_activity_lines')
    licence_activity = models.ForeignKey(
        'wildlifecompliance.LicenceActivity', null=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2, default='0')

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return 'Invoice #{} - Activity {} : Amount {}'.format(
            self.invoice, self.licence_activity, self.amount)

class ApplicationLogDocument(Document):
    log_entry = models.ForeignKey(
        'ApplicationLogEntry',
        related_name='documents')
    _file = models.FileField(upload_to=update_application_comms_log_filename)

    class Meta:
        app_label = 'wildlifecompliance'


class ApplicationLogEntry(CommunicationsLogEntry):
    application = models.ForeignKey(Application, related_name='comms_logs')

    class Meta:
        app_label = 'wildlifecompliance'

    def save(self, **kwargs):
        # save the application reference if the reference not provided
        if not self.reference:
            self.reference = self.application.lodgement_number
        super(ApplicationLogEntry, self).save(**kwargs)

    def __str__(self):
        return 'Comms Log: {} Type: {} From: {}'.format(
            self.subject, self.log_type, self.fromm)

class ApplicationRequest(models.Model):
    application = models.ForeignKey(Application)
    subject = models.CharField(max_length=200, blank=True)
    text = models.TextField(blank=True)
    officer = models.ForeignKey(EmailUser, null=True)

    class Meta:
        app_label = 'wildlifecompliance'


class ReturnRequest(ApplicationRequest):
    RETURN_REQUEST_REASON_OUTSTANDING = 'outstanding'
    RETURN_REQUEST_REASON_OTHER = 'other'
    REASON_CHOICES = (
        (RETURN_REQUEST_REASON_OUTSTANDING, 'There are currently outstanding returns for the previous licence'),
        (RETURN_REQUEST_REASON_OTHER, 'Other')
    )
    reason = models.CharField(
        'Reason',
        max_length=30,
        choices=REASON_CHOICES,
        default=RETURN_REQUEST_REASON_OUTSTANDING)

    class Meta:
        app_label = 'wildlifecompliance'


class AmendmentRequest(ApplicationRequest):
    AMENDMENT_REQUEST_STATUS_REQUESTED = 'requested'
    AMENDMENT_REQUEST_STATUS_AMENDED = 'amended'
    STATUS_CHOICES = (
        (AMENDMENT_REQUEST_STATUS_REQUESTED, 'Requested'),
        (AMENDMENT_REQUEST_STATUS_AMENDED, 'Amended')
    )
    AMENDMENT_REQUEST_REASON_INSUFFICIENT_DETAIL = 'insufficient_detail'
    AMENDMENT_REQUEST_REASON_MISSING_INFO = 'missing_information'
    AMENDMENT_REQUEST_REASON_OTHER = 'other'
    REASON_CHOICES = (
        (AMENDMENT_REQUEST_REASON_INSUFFICIENT_DETAIL, 'The information provided was insufficient'),
        (AMENDMENT_REQUEST_REASON_MISSING_INFO, 'There was missing information'),
        (AMENDMENT_REQUEST_REASON_OTHER, 'Other')
    )
    status = models.CharField(
        'Status',
        max_length=30,
        choices=STATUS_CHOICES,
        default=AMENDMENT_REQUEST_STATUS_REQUESTED)
    reason = models.CharField(
        'Reason',
        max_length=30,
        choices=REASON_CHOICES,
        default=AMENDMENT_REQUEST_REASON_INSUFFICIENT_DETAIL)
    licence_activity = models.ForeignKey(
        'wildlifecompliance.LicenceActivity', null=True)

    class Meta:
        app_label = 'wildlifecompliance'

    def generate_amendment(self, request):
        with transaction.atomic():
            try:
                # This is to change the status of licence activity
                self.application.set_activity_processing_status(
                    self.licence_activity.id, ApplicationSelectedActivity.PROCESSING_STATUS_DRAFT)
                self.application.customer_status = Application.CUSTOMER_STATUS_AMENDMENT_REQUIRED
                self.application.save()

                # Create a log entry for the application
                self.application.log_user_action(
                    ApplicationUserAction.ACTION_ID_REQUEST_AMENDMENTS, request)
                self.save()
            except BaseException:
                raise


class Assessment(ApplicationRequest):
    STATUS_AWAITING_ASSESSMENT = 'awaiting_assessment'
    STATUS_ASSESSED = 'assessed'
    STATUS_COMPLETED = 'completed'
    STATUS_RECALLED = 'recalled'
    STATUS_CHOICES = (
        (STATUS_AWAITING_ASSESSMENT, 'Awaiting Assessment'),
        (STATUS_ASSESSED, 'Assessed'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_RECALLED, 'Recalled')
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_AWAITING_ASSESSMENT)
    date_last_reminded = models.DateField(null=True, blank=True)
    assessor_group = models.ForeignKey(
        ActivityPermissionGroup, null=False, default=1)
    licence_activity = models.ForeignKey(
        'wildlifecompliance.LicenceActivity', null=True)
    final_comment = models.TextField(blank=True)
    purpose = models.TextField(blank=True)
    actioned_by = models.ForeignKey(EmailUser, null=True)
    assigned_assessor = models.ForeignKey(
        EmailUser,
        blank=True,
        null=True,
        related_name='wildlifecompliance_assessor')

    class Meta:
        app_label = 'wildlifecompliance'

    def generate_assessment(self, request):
        with transaction.atomic():
            try:
                # This is to change the status of licence activity
                self.application.set_activity_processing_status(
                    request.data.get('licence_activity'), ApplicationSelectedActivity.PROCESSING_STATUS_WITH_ASSESSOR)
                self.officer = request.user
                self.date_last_reminded = datetime.datetime.strptime(
                    timezone.now().strftime('%Y-%m-%d'), '%Y-%m-%d').date()
                self.save()

                select_group = self.assessor_group.members.all()

                # Create a log entry for the application
                self.application.log_user_action(
                    ApplicationUserAction.ACTION_SEND_FOR_ASSESSMENT_TO_.format(
                        self.assessor_group.name), request)
                # send email
                send_assessment_email_notification(select_group, self, request)
            except BaseException:
                raise

    def remind_assessment(self, request):
        with transaction.atomic():
            try:
                select_group = self.assessor_group.members.all()
                # send email
                send_assessment_reminder_email(select_group, self, request)
                self.date_last_reminded = datetime.datetime.strptime(
                    timezone.now().strftime('%Y-%m-%d'), '%Y-%m-%d').date()
                self.save()
                # Create a log entry for the application
                self.application.log_user_action(
                    ApplicationUserAction.ACTION_SEND_ASSESSMENT_REMINDER_TO_.format(
                        self.assessor_group.name), request)
            except BaseException:
                raise

    def recall_assessment(self, request):
        with transaction.atomic():
            try:
                self.status = Assessment.STATUS_RECALLED
                self.actioned_by = request.user
                self.save()

                if not Assessment.objects.filter(
                    application_id=self.application_id,
                    licence_activity=self.licence_activity_id,
                    status=Assessment.STATUS_AWAITING_ASSESSMENT
                ).exists():
                    # Create a log entry for the application
                    self.application.log_user_action(
                        ApplicationUserAction.ACTION_ASSESSMENT_RECALLED.format(
                            self.assessor_group), request)

                    last_complete_assessment = Assessment.objects.filter(
                        application_id=self.application_id,
                        licence_activity=self.licence_activity_id,
                        status=Assessment.STATUS_COMPLETED,
                        actioned_by__isnull=False
                    ).order_by('-id').first()
                    if last_complete_assessment:
                        last_complete_assessment.application.check_assessment_complete(self.licence_activity_id)
                    else:
                        self.application.set_activity_processing_status(
                            self.licence_activity_id,
                            ApplicationSelectedActivity.PROCESSING_STATUS_WITH_OFFICER
                        )

            except BaseException:
                raise

    def resend_assessment(self, request):
        with transaction.atomic():
            try:
                self.status = Assessment.STATUS_AWAITING_ASSESSMENT
                self.application.set_activity_processing_status(
                    self.licence_activity_id, ApplicationSelectedActivity.PROCESSING_STATUS_WITH_ASSESSOR)
                self.save()
                # Create a log entry for the application
                self.application.log_user_action(
                    ApplicationUserAction.ACTION_ASSESSMENT_RESENT.format(
                        self.assessor_group), request)
            except BaseException:
                raise

    def add_inspection(self, request):
        """
        Attaches an Inspection to an Assessment.
        """
        with transaction.atomic():
            try:
                inspection = Inspection.objects.get(
                    id=request.data.get('inspection_id'))

                assessment_inspection, created = \
                    AssessmentInspection.objects.get_or_create(
                        assessment=self,
                        inspection=inspection
                    )
                assessment_inspection.save()

                # Create a log entry for the inspection
                self.application.log_user_action(
                    ApplicationUserAction.ACTION_ASSESSMENT_INSPECTION_REQUEST.format(
                        inspection.number, self.licence_activity), request)

            except Inspection.DoesNotExist:
                raise Exception('Inspection was not created')
            except BaseException:
                raise

    @property
    def selected_activity(self):
        return ApplicationSelectedActivity.objects.filter(
            application_id=self.application_id,
            licence_activity_id=self.licence_activity_id
        ).first()

    @property
    def is_inspection_required(self):
        return self.selected_activity.is_inspection_required

    @property
    def has_inspection_opened(self):
        """
        Property indicating an inspection is created and opened.
        """
        inspection_exists = False

        inspections = AssessmentInspection.objects.filter(
            assessment=self
        )
        is_active = [i.is_active for i in inspections if i.is_active]
        inspection_exists = is_active[0] if is_active else False

        return inspection_exists

    def assessors(self):
        return self.assessor_group.members.all()


class AssessmentInspection(models.Model):
    """
    A model represention of an Inspection for an Assessment.
    """
    assessment = models.ForeignKey(
        Assessment, related_name='inspections')
    inspection = models.ForeignKey(
        Inspection, related_name='wildlifecompliance_inspection')
    request_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return 'Assessment {0} : Inspection #{1}'.format(
            self.assessment_id, self.inspection.number)

    @property
    def is_active(self):
        '''
        An attribute to indicate that this assessment inspection is currently
        progressing.
        '''
        is_active = False

        if self.inspection.status in [
            Inspection.STATUS_OPEN,
            Inspection.STATUS_AWAIT_ENDORSEMENT,
        ]:
            is_active = True

        return is_active


class ApplicationSelectedActivity(models.Model):
    PROPOSED_ACTION_DEFAULT = 'default'
    PROPOSED_ACTION_DECLINE = 'propose_decline'
    PROPOSED_ACTION_ISSUE = 'propose_issue'
    PROPOSED_ACTION_CHOICES = (
        (PROPOSED_ACTION_DEFAULT, 'Default'),
        (PROPOSED_ACTION_DECLINE, 'Propose Decline'),
        (PROPOSED_ACTION_ISSUE, 'Propose Issue')
    )

    DECISION_ACTION_DEFAULT = 'default'
    DECISION_ACTION_DECLINED = 'declined'
    DECISION_ACTION_ISSUED = 'issued'
    DECISION_ACTION_REISSUE = 'reissue'
    DECISION_ACTION_CHOICES = (
        (DECISION_ACTION_DEFAULT, 'Default'),
        (DECISION_ACTION_DECLINED, 'Declined'),
        (DECISION_ACTION_ISSUED, 'Issued'),
        (DECISION_ACTION_REISSUE, 'Re-issue'),
    )

    ACTIVITY_STATUS_DEFAULT = 'default'
    ACTIVITY_STATUS_CURRENT = 'current'
    ACTIVITY_STATUS_EXPIRED = 'expired'
    ACTIVITY_STATUS_CANCELLED = 'cancelled'
    ACTIVITY_STATUS_SURRENDERED = 'surrendered'
    ACTIVITY_STATUS_SUSPENDED = 'suspended'
    ACTIVITY_STATUS_REPLACED = 'replaced'
    ACTIVITY_STATUS_CHOICES = (
        (ACTIVITY_STATUS_DEFAULT, 'Default'),
        (ACTIVITY_STATUS_CURRENT, 'Current'),
        (ACTIVITY_STATUS_EXPIRED, 'Expired'),
        (ACTIVITY_STATUS_CANCELLED, 'Cancelled'),
        (ACTIVITY_STATUS_SURRENDERED, 'Surrendered'),
        (ACTIVITY_STATUS_SUSPENDED, 'Suspended'),
        (ACTIVITY_STATUS_REPLACED, 'Replaced')
    )

    PROCESSING_STATUS_DRAFT = 'draft'
    PROCESSING_STATUS_WITH_OFFICER = 'with_officer'
    PROCESSING_STATUS_WITH_ASSESSOR = 'with_assessor'
    PROCESSING_STATUS_OFFICER_CONDITIONS = 'with_officer_conditions'
    PROCESSING_STATUS_OFFICER_FINALISATION = 'with_officer_finalisation'
    PROCESSING_STATUS_AWAITING_LICENCE_FEE_PAYMENT = 'awaiting_licence_fee_payment'
    PROCESSING_STATUS_ACCEPTED = 'accepted'
    PROCESSING_STATUS_DECLINED = 'declined'
    PROCESSING_STATUS_DISCARDED = 'discarded'
    PROCESSING_STATUS_CHOICES = (
        (PROCESSING_STATUS_DRAFT, 'Draft'),
        (PROCESSING_STATUS_WITH_OFFICER, 'With Officer'),
        (PROCESSING_STATUS_WITH_ASSESSOR, 'With Assessor'),
        (PROCESSING_STATUS_OFFICER_CONDITIONS, 'With Officer-Conditions'),
        (PROCESSING_STATUS_OFFICER_FINALISATION, 'With Approver'),
        (PROCESSING_STATUS_AWAITING_LICENCE_FEE_PAYMENT, 'Awaiting Licence Fee Payment'),
        (PROCESSING_STATUS_ACCEPTED, 'Accepted'),
        (PROCESSING_STATUS_DECLINED, 'Declined'),
        (PROCESSING_STATUS_DISCARDED, 'Discarded'),
    )
    proposed_action = models.CharField(
        'Action',
        max_length=20,
        choices=PROPOSED_ACTION_CHOICES,
        default=PROPOSED_ACTION_DEFAULT)
    decision_action = models.CharField(
        'Action',
        max_length=20,
        choices=DECISION_ACTION_CHOICES,
        default=DECISION_ACTION_DEFAULT)
    processing_status = models.CharField(
        'Processing Status',
        max_length=30,
        choices=PROCESSING_STATUS_CHOICES,
        default=PROCESSING_STATUS_DRAFT)
    activity_status = models.CharField(
        max_length=40,
        choices=ACTIVITY_STATUS_CHOICES,
        default=ACTIVITY_STATUS_DEFAULT)
    application = models.ForeignKey(Application, related_name='selected_activities')
    updated_by = models.ForeignKey(EmailUser, null=True)
    reason = models.TextField(blank=True)
    cc_email = models.TextField(null=True)
    activity = JSONField(blank=True, null=True)
    licence_activity = models.ForeignKey(
        'wildlifecompliance.LicenceActivity', null=True)
    proposed_start_date = models.DateField(null=True, blank=True)
    proposed_end_date = models.DateField(null=True, blank=True)
    additional_info = models.TextField(blank=True, null=True)
    conditions = models.TextField(blank=True, null=True)
    is_inspection_required = models.BooleanField(default=False)
    licence_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default='0')
    application_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default='0')
    # Additional Fee is the amount an internal officer imposes on an Activity
    # for services excluded from the application fee.
    additional_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default='0')
    additional_fee_text = models.TextField(blank=True, null=True)
    assigned_approver = models.ForeignKey(
        EmailUser,
        blank=True,
        null=True,
        related_name='wildlifecompliance_officer_finalisation')
    assigned_officer = models.ForeignKey(
        EmailUser,
        blank=True,
        null=True,
        related_name='wildlifecompliance_officer')
    additional_licence_info = JSONField(default=list)
    # TODO: issue dates and period dates are not required on Activity.
    original_issue_date = models.DateTimeField(blank=True, null=True)
    issue_date = models.DateTimeField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return "{0}{1}{2}{3}{4}".format(
            "Activity: {name} ".format(name=self.licence_activity.short_name),
            "App. Fee: {fee1} ".format(fee1=self.pre_adjusted_application_fee),
            "Lic. Fee: {fee2} ".format(fee2=self.licence_fee),
            "Add. Fee: {fee3} ".format(fee3=self.additional_fee),
            "(App: {id})".format(id=self.application_id),
        )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'Application selected activity'
        verbose_name_plural = 'Application selected activities'

    @staticmethod
    def is_valid_status(status):
        return filter(lambda x: x[0] == status,
                      ApplicationSelectedActivity.PROCESSING_STATUS_CHOICES)

    @property
    def has_inspection(self):
        """
        Property indicating an Assessment Inspection exist for this
        Selected Activity.
        """
        has_inspection = False
        for assessment in self.application.assessments:
            has_inspection = assessment.has_inspection_opened

        return has_inspection

    @property
    def purposes(self):
        """
        All licence purposes which are available under the Application Selected
        Activity.
        """
        from wildlifecompliance.components.licences.models import LicencePurpose
        return LicencePurpose.objects.filter(
            application__id=self.application_id,
            licence_activity_id=self.licence_activity_id
        ).distinct()

    @property
    def issued_purposes(self):
        """
        All licence purposes which have been proposed and issued.
        """
        from wildlifecompliance.components.licences.models import LicencePurpose

        purposes = [p.purpose for p in self.proposed_purposes.filter(
            processing_status='issue')]
        return purposes

    def can_action(self, purposes_in_open_applications=[]):
        # Returns a DICT object containing can_<action> Boolean results of each action check
        can_action = {
            'licence_activity_id': self.licence_activity_id,
            'can_amend': False,
            'can_renew': False,
            'can_reactivate_renew': False,
            'can_surrender': False,
            'can_cancel': False,
            'can_suspend': False,
            'can_reissue': False,
            'can_reinstate': False,
        }
        current_date = timezone.now().date()

        # return false for all actions if activity is not in latest licence
        if not self.is_in_latest_licence:
            return can_action

        # No action should be available if all of an activity's purposes are in open applications
        # check if there are any purposes in open applications (i.e. can action)
        # return false for all actions if no purposes are still actionable
        if not len(list((set(self.purposes.values_list('id', flat=True)) - set(purposes_in_open_applications)))) > 0:
            return can_action

        # can_amend is true if the activity can be included in a Amendment Application
        # Extra exclude for SUSPENDED due to get_current_activities_for_application_type
        # intentionally not excluding these as part of the default queryset
        can_action['can_amend'] = ApplicationSelectedActivity.get_current_activities_for_application_type(
            Application.APPLICATION_TYPE_AMENDMENT,
            activity_ids=[self.id]
        ).exclude(activity_status=ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED).count() > 0

        # can_renew is true if the activity can be included in a Renewal Application
        # Extra exclude for SUSPENDED due to get_current_activities_for_application_type
        # intentionally not excluding these as part of the default queryset
        can_action['can_renew'] = ApplicationSelectedActivity.get_current_activities_for_application_type(
            Application.APPLICATION_TYPE_RENEWAL,
            activity_ids=[self.id]
        ).exclude(activity_status=ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED).count() > 0

        # can_reactivate_renew is true if the activity has expired, excluding if it was surrendered or cancelled
        can_action['can_reactivate_renew'] = ApplicationSelectedActivity.objects.filter(
            Q(id=self.id, expiry_date__isnull=False),
            Q(expiry_date__lt=current_date) |
            Q(activity_status=ApplicationSelectedActivity.ACTIVITY_STATUS_EXPIRED)
        ).filter(
            processing_status=ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED
        ).exclude(
            activity_status__in=[
                ApplicationSelectedActivity.ACTIVITY_STATUS_SURRENDERED,
                ApplicationSelectedActivity.ACTIVITY_STATUS_CANCELLED,
                ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED
            ]
        ).count() > 0

        # can_surrender is true if the activity is CURRENT or SUSPENDED
        # disable if there are any open applications to maintain licence sequence data integrity
        if not purposes_in_open_applications:
            can_action['can_surrender'] = ApplicationSelectedActivity.get_current_activities_for_application_type(
                Application.APPLICATION_TYPE_SYSTEM_GENERATED,
                activity_ids=[self.id]
            ).count() > 0

        # can_cancel is true if the activity is CURRENT or SUSPENDED
        # disable if there are any open applications to maintain licence sequence data integrity
        if not purposes_in_open_applications:
            can_action['can_cancel'] = ApplicationSelectedActivity.get_current_activities_for_application_type(
                Application.APPLICATION_TYPE_SYSTEM_GENERATED,
                activity_ids=[self.id]
            ).count() > 0

        # can_suspend is true if the activity_status is CURRENT
        # Extra exclude for SUSPENDED due to get_current_activities_for_application_type
        # intentionally not excluding these as part of the default queryset
        can_action['can_suspend'] = ApplicationSelectedActivity.get_current_activities_for_application_type(
            Application.APPLICATION_TYPE_SYSTEM_GENERATED,
            activity_ids=[self.id]
        ).exclude(activity_status=ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED).count() > 0

        # can_reissue is true if the activity can be included in a Reissue Application
        # Extra exclude for SUSPENDED due to get_current_activities_for_application_type
        # intentionally not excluding these as part of the default queryset
        # disable if there are any open applications to maintain licence sequence data integrity
        if not purposes_in_open_applications:
            can_action['can_reissue'] = ApplicationSelectedActivity.get_current_activities_for_application_type(
                Application.APPLICATION_TYPE_REISSUE,
                activity_ids=[self.id]
            ).exclude(
                activity_status__in=[
                    ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED,
                ]
            ).count() > 0

        # can_reinstate is true if the activity has not yet expired and is currently SUSPENDED, CANCELLED or SURRENDERED
        can_action['can_reinstate'] = self.expiry_date and \
               self.expiry_date >= current_date and \
               self.activity_status in [
                   ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED,
                   ApplicationSelectedActivity.ACTIVITY_STATUS_CANCELLED,
                   ApplicationSelectedActivity.ACTIVITY_STATUS_SURRENDERED
               ]

        return can_action

    @property
    def is_in_latest_licence(self):
        # Returns true if the activity is in the latest WildlifeLicence record for the relevant applicant
        from wildlifecompliance.components.licences.models import WildlifeLicence

        licences = WildlifeLicence.objects.filter(
            Q(current_application__org_applicant=self.application.org_applicant)
            if self.application.org_applicant
            else Q(current_application__proxy_applicant=self.application.proxy_applicant)
            if self.application.proxy_applicant
            else Q(current_application__submitter=self.application.submitter, current_application__proxy_applicant=None,
                   current_application__org_applicant=None),
            licence_category_id=self.licence_activity.licence_category_id
        )
        if licences and self in licences.latest('id').latest_activities:
            return True
        return False

    @property
    def base_fees(self):
        return Application.calculate_base_fees(
            self.application.licence_purposes.filter(
                licence_activity_id=self.licence_activity_id
            ).values_list('id', flat=True)
        )

    @property
    def licence_fee_paid(self):
        return self.payment_status in [
            ActivityInvoice.PAYMENT_STATUS_NOT_REQUIRED,
            ActivityInvoice.PAYMENT_STATUS_PAID,
            ActivityInvoice.PAYMENT_STATUS_OVERPAID,
        ]

    @property
    def payment_status(self):
        """
        Activity payment consist of Licence and Additional Fee. Property 
        shows the status for both of these payments. Licence Fee is paid up
        front before additional fees.

        FIXME: Need to check for adjustments to fees by officer which may need
        to be paid at issuance.
        """
        def get_payment_status_for_licence(_status):
            if self.application_fee == 0 and self.total_paid_amount < 1:
                _status = ActivityInvoice.PAYMENT_STATUS_NOT_REQUIRED
            else:
                if self.activity_invoices.count() == 0:
                    _status = ActivityInvoice.PAYMENT_STATUS_UNPAID
                else:
                    try:
                        latest_invoice = Invoice.objects.get(
                            reference=self.activity_invoices.latest(
                                'id').invoice_reference)
                        _status = latest_invoice.payment_status
                    except Invoice.DoesNotExist:
                        _status =  ActivityInvoice.PAYMENT_STATUS_UNPAID

            return _status

        def get_payment_status_for_additional(_status):
            if self.additional_fee > Decimal(0.0):
                _status = ActivityInvoice.PAYMENT_STATUS_UNPAID
                try:
                    latest_invoice = Invoice.objects.get(
                        reference=self.activity_invoices.latest(
                            'id').invoice_reference,
                        amount=self.additional_fee)
                    _status = latest_invoice.payment_status

                except Invoice.DoesNotExist:
                    if self.processing_status == \
                        ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED:
                        _status = ActivityInvoice.PAYMENT_STATUS_PAID

                except BaseException:
                    if self.processing_status == \
                        ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED:
                        _status = ActivityInvoice.PAYMENT_STATUS_PAID

            return _status

        def get_payment_status_for_adjustment(_status):
            if self.application_fee > 0 and self.has_adjusted_application_fee:
                _status = ActivityInvoice.PAYMENT_STATUS_UNPAID
                fees_tot = 0
                for purpose in self.proposed_purposes.all():
                    fees_tot += purpose.licence_fee
                    fees_tot += purpose.adjusted_fee
                    fees_tot += purpose.application_fee              
                if self.total_paid_amount == fees_tot:
                    _status = ActivityInvoice.PAYMENT_STATUS_PAID

            return _status

        paid_status = [
            ActivityInvoice.PAYMENT_STATUS_NOT_REQUIRED,
            ActivityInvoice.PAYMENT_STATUS_PAID,            
        ]

        status = ActivityInvoice.PAYMENT_STATUS_UNPAID
        status = get_payment_status_for_licence(status)
        if status not in paid_status:
            return status

        status = get_payment_status_for_additional(status)
        if status not in paid_status:
            return status

        status = get_payment_status_for_adjustment(status)
        if status not in paid_status:
            return status

        return status

    @property
    def licensing_officers(self):
        """
        Authorised licence officers for this Selected Activity.
        """
        groups = ActivityPermissionGroup.get_groups_for_activities(
            self.licence_activity, 'licensing_officer')

        return EmailUser.objects.filter(groups__id__in=groups).distinct()

    @property
    def issuing_officers(self):
        """
        Authorised issuing officers for this Selected Activity.
        """
        groups = ActivityPermissionGroup.get_groups_for_activities(
            self.licence_activity, 'issuing_officer')

        return EmailUser.objects.filter(groups__id__in=groups).distinct()

    @staticmethod
    def get_current_activities_for_application_type(application_type, **kwargs):
        """
        Retrieves the current or suspended activities for an
        ApplicationSelectedActivity, filterable by LicenceActivity ID and
        Application.APPLICATION_TYPE in the case of the additional date_filter
        (use Application.APPLICATION_TYPE_SYSTEM_GENERATED for no 
        APPLICATION_TYPE filters)
        """
        applications = kwargs.get('applications', Application.objects.none())
        activity_ids = kwargs.get('activity_ids', [])
        activities = None

        date_filter = Application.get_activity_date_filter(
            application_type)

        ACCEPT = ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED
        # TODO: date_filter applies expiry_date
        activities = ApplicationSelectedActivity.objects.filter(
            Q(id__in=activity_ids) if activity_ids else
            Q(application_id__in=applications.values_list('id', flat=True)),
            # **date_filter
        ).filter(
            processing_status=ACCEPT
        ).exclude(
            activity_status__in=[
                ApplicationSelectedActivity.ACTIVITY_STATUS_SURRENDERED,
                ApplicationSelectedActivity.ACTIVITY_STATUS_EXPIRED,
                ApplicationSelectedActivity.ACTIVITY_STATUS_CANCELLED,
                ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED
            ]
        ).distinct()

        a_ids = ApplicationSelectedActivityPurpose.objects.filter(
            # Apply the date filtering on the Purposes.
            selected_activity_id__in=[a.id for a in activities],
            **date_filter
        ).values_list('selected_activity_id', flat=True)
        activities = activities.filter(id__in=a_ids)

        return activities

    @property
    def total_paid_amount(self):
        """
        Property defining the total fees already paid for this licence Activity.
        The total amount includes application fee, additional fee, adjustments
        and licence fee.
        """
        amount = 0
        if self.activity_invoices.count() > 0:
            invoices = ActivityInvoice.objects.filter(
                activity_id=self.id)
            for invoice in invoices:
                lines = ActivityInvoiceLine.objects.filter(
                    invoice_id=invoice.id)
                for line in lines:
                    amount += line.amount
                # exclude the refunds
                detail = Invoice.objects.get(
                    reference=invoice.invoice_reference)
                amount -= detail.refund_amount
     
        return amount

    @property
    def has_adjusted_application_fee(self):
        '''
        Property indicating this Selected Activity has an application fee cost
        different from the base admin fee Activity/Purpose.
        '''
        adjusted = False
        adj_fees = 0
        for p in self.proposed_purposes.all():
            adj_fees += p.adjusted_fee

        return True if not adj_fees == 0 else False

    @property
    def pre_adjusted_application_fee(self):
        '''
        Property returning the application fee amount paid for this Selected
        Activity excluding the additional fees imposed by officer.
        '''
        app_fees = 0
        for p in self.proposed_purposes.all():
            app_fees += p.application_fee

        return app_fees

    @property
    def requires_refund(self):
        """
        Check on the previously paid invoice amount against Activity fee.
        NOTE: there is no use-case for refunding licence activity fee.
        """
        if self.licence_fee < 1:
            return False

        if self.total_paid_amount - self.licence_fee > 0:
            return True

        return False

    @property
    def previous_paid_amount(self):
        '''
        Property for the total application fee (including adjustments) paid for
        on the selected activity. For licence amendments it will be the amount
        paid on the previous application activity when no invoice exist for the
        selected activity.
        '''
        def previous_paid_from_invoice(previous_paid):
            """
            Returns the total application fee (including adjustments) for this
            selected activity.
            """
            if self.payment_status in [
                ActivityInvoice.PAYMENT_STATUS_PAID,
            ]:
                additional = self.licence_fee + self.additional_fee
                previous_paid = self.total_paid_amount - additional
                
            return previous_paid

        def previous_paid_under_review(previous_paid):
            """
            Under Review an Application Ammendment cannot get a refund amount
            triggered by internal officers change to Application. Previous
            paid will be zero.
            """
            if self.application.processing_status ==\
                Application.PROCESSING_STATUS_UNDER_REVIEW:
                # apply the total_paid_amount as application fee is paid.
                if not previous_paid > self.application_fee:
                    previous_paid = self.application_fee - previous_paid
                else:
                    previous_paid = 0
                
            return previous_paid

        def previous_paid_from_licence(previous_paid):
            '''
            Returns the previous amount that was paid for this activity on the
            current licence.
            '''
            try:
                purposes = self.proposed_purposes.all()
                for purpose in purposes:
                    prev = purpose.get_purpose_from_previous()
                    previous_paid += prev.application_fee if prev else 0
                    previous_paid += prev.adjusted_fee if prev else 0
                    # previous_paid += prev_total

                # prev_act = self.get_activity_from_previous()
                # if prev_act and prev_act.has_adjusted_application_fee:
                #     previous_paid += prev_act.additional_fee

            except BaseException:
                raise

            return previous_paid

        previous_paid = 0
        # check for Customer licence amendment.
        if self.application.application_type ==\
                Application.APPLICATION_TYPE_AMENDMENT:
            previous_paid = previous_paid_from_licence(previous_paid)
            previous_paid = previous_paid_from_invoice(previous_paid)
            # previous_paid = previous_paid_under_review(previous_paid)

        return previous_paid

    def set_original_issue_date(self, issue_date):
        '''
        Set the original issue date on all purposes on this activity.
        '''
        for p in self.proposed_purposes.all():
            p.original_issue_date = issue_date if p.is_proposed \
                else p.original_issue_date
            p.save()

    def get_original_issue_date(self):
        '''
        Get the earliest original issue date from all purposes on this activity.
        '''
        o_date = datetime.datetime.strptime('9999-12-31', '%Y-%m-%d')
        try:
            for p in self.proposed_purposes.all():
                o_otime = datetime.datetime.strptime(
                    o_date.strftime('%Y-%m-%d'),
                    '%Y-%m-%d'
                )
                p_otime = datetime.datetime.strptime(
                    p.original_issue_date,
                    '%Y-%m-%d'
                )
                o_date = p.original_issue_date \
                    if p_otime < o_otime and p.is_proposed else o_date

        except BaseException as e:
            logger.error('get_original_issue_date(): {0}'.format(e))
            o_date = None

        return o_date

    def set_issue_date(self, issue_date):
        '''
        Set the issue date on all purposes on this activity.
        '''
        for p in self.proposed_purposes.all():
            p.issue_date = issue_date if p.is_proposed else p.issue_date
            p.save()

    def get_issue_date(self):
        '''
        Get the earliest issue date from all purposes on this activity.
        '''
        issue_date = datetime.datetime.strptime('9999-12-31', '%Y-%m-%d')
        try:
            for p in self.proposed_purposes.all():
                i_itime = datetime.datetime.strptime(
                    issue_date.strftime('%Y-%m-%d'), 
                    '%Y-%m-%d'
                )
                p_itime = datetime.datetime.strptime(
                    p.issue_date.strftime('%Y-%m-%d'),
                    '%Y-%m-%d'
                )
                # p_itime = p.issue_date.strftime('%Y,%m,%d')
                issue_date = p.issue_date \
                    if p_itime < i_itime and p.is_proposed else issue_date

        except BaseException as e:
            logger.error('get_issue_date(): {0}'.format(e))
            issue_date = None

        #return issue_date.strftime('%d/%m/%Y') if issue_date else issue_date
        return issue_date

    def set_start_date(self, start_date):
        '''
        Set the start date on all purposes on this activity.
        '''
        for p in self.proposed_purposes.all():
            p.start_date = start_date if p.is_proposed else p.start_date
            p.save()

    def get_start_date(self):
        '''
        Get the earliest start date from all purposes on this activity.
        '''
        start_date = datetime.datetime.strptime('9999-12-31', '%Y-%m-%d')
        try:
            for p in self.proposed_purposes.all():
                s_stime = datetime.datetime.strptime(
                    start_date.strftime('%Y-%m-%d'),
                    '%Y-%m-%d'
                )
                p_stime = datetime.datetime.strptime(
                    p.start_date.strftime('%Y-%m-%d'),
                    '%Y-%m-%d'
                )
                # p_stime = datetime.datetime.strptime(p.start_date, '%d/%m/%Y')
                start_date = p.start_date \
                    if p_stime < s_stime and p.is_proposed else start_date

        except BaseException as e:
            logger.error('get_start_date(): {0}'.format(e))
            start_date = None

        return start_date

    def set_expiry_date(self, expiry_date):
        '''
        Set the expiry date on all purposes on this activity.
        '''
        for p in self.proposed_purposes.all():
            p.expiry_date = expiry_date if p.is_proposed else p.expiry_date
            p.save()
    
    def get_expiry_date(self):
        '''
        Get the latest expiry date from all purposes on this activity.
        '''
        exp_date = datetime.datetime.strptime('1901-01-01', '%Y-%m-%d')
        try:
            for p in self.proposed_purposes.all():
                e_etime = datetime.datetime.strptime(
                    exp_date.strftime('%Y-%m-%d'),
                    '%Y-%m-%d'
                )
                p_etime = datetime.datetime.strptime(
                    p.expiry_date.strftime('%Y-%m-%d'),
                    '%Y-%m-%d'
                )
                #p_etime = datetime.datetime.strptime(p.expiry_date, '%d/%m/%Y')
                exp_date = p.expiry_date if p_etime > e_etime else exp_date

        except BaseException as e:
            logger.error('get_expiry_date(): {0}'.format(e))
            exp_date = None

        return exp_date

    def is_current(self):
        '''
        Get flag indicating that this activity contains a purpose that has not
        expired.
        '''
        is_current = False
        c_date = timezone.now().date()

        try:
            c_ctime = datetime.datetime.strptime(c_date, '%d/%m/%Y')
            for p in self.proposed_purposes.all():
                p_etime = datetime.datetime.strptime(p.expiry_date, '%d/%m/%Y')
                if c_ctime <= p_etime and p.is_proposed:
                    is_current = True 
                    break

        except BaseException as e:
            logger.error('ASA.is_current(): {0}'.format(e))

        return is_current

    @property
    def is_reissued(self):
        '''
        Attribute to indicate that this activity has been reissued.
        '''
        is_reissued = False
        c_date = timezone.now().date()

        try:
            i_date = self.get_issue_date()
            o_date = self.get_original_issue_date()
            i_dtime = datetime.datetime.strptime(
                i_date.strftime('%Y-%m-%d'),
                '%Y-%m-%d'
            )
            o_dtime = datetime.datetime.strptime(
                o_date.strftime('%Y-%m-%d'),
                '%Y-%m-%d'
            )

            is_reissued = False if idtime == o_dtime else True

        except BaseException as e:
            logger.error('ASA.is_reissued(): {0}'.format(e))

        return is_reissued

    def process_licence_fee_payment(self, request, application):
        from ledger.payments.models import BpointToken
        if self.licence_fee_paid:
            return True

        applicant = application.proxy_applicant if application.proxy_applicant else application.submitter
        card_owner_id = applicant.id
        card_token = BpointToken.objects.filter(user_id=card_owner_id).order_by('-id').first()
        if not card_token:
            logger.error("No card token found for user: %s" % card_owner_id)
            return False

        product_lines = []
        application_submission = u'Activity licence issued for {} application {}'.format(
            u'{} {}'.format(applicant.first_name, applicant.last_name), application.lodgement_number)
        set_session_application(request.session, application)
        product_lines.append({
            'ledger_description': '{}'.format(self.licence_activity.name),
            'quantity': 1,
            'price_incl_tax': str(self.licence_fee),
            'price_excl_tax': str(calculate_excl_gst(self.licence_fee)),
            'oracle_code': ''
        })
        checkout(
            request, application, lines=product_lines,
            invoice_text=application_submission,
            internal=True,
            add_checkout_params={
                'basket_owner': request.user.id,
                'payment_method': 'card',
                'checkout_token': card_token.id,
            }
        )
        try:
            '''
            Requires check for KeyError when an Order has not been successfully created for an Activity Licence. When an Order
            does not exist the session key 'checkout_invoice' will remain from the token's previous Application payment.
            Another check is required to check valid invoice details.
            '''
            invoice_ref = request.session['checkout_invoice']
            created_invoice = Invoice.objects.filter(reference=invoice_ref).first()
            if (created_invoice.text != application_submission):  # text on invoice does not match this payment submission.
                raise KeyError
        except KeyError:
            logger.error("No invoice reference generated for Activity ID: %s" % self.licence_activity_id)
            return False
        invoice = ActivityInvoice.objects.get_or_create(
            activity=self,
            invoice_reference=invoice_ref
        )
        line = ActivityInvoiceLine.object.get_or_create(
            invoice=invoice[0],
            licence_activity=self.licence_activity,
            amount=self.licence_fee
        )
        delete_session_application(request.session)
        flush_checkout_session(request.session)
        return self.licence_fee_paid and send_activity_invoice_email_notification(application, self, invoice_ref, request)

    def reactivate_renew(self, request):
        # TODO: this needs work, reactivate renew logic to be clarified and function adjusted
        # TODO: perhaps set a grace period of default 2 weeks?
        with transaction.atomic():
            self.activity_status = ApplicationSelectedActivity.ACTIVITY_STATUS_EXPIRED
            self.updated_by = request.user
            self.save()

    def surrender(self, request):
        with transaction.atomic():
            self.activity_status = ApplicationSelectedActivity.ACTIVITY_STATUS_SURRENDERED
            self.updated_by = request.user
            self.save()

    def cancel(self, request):
        with transaction.atomic():
            self.activity_status = ApplicationSelectedActivity.ACTIVITY_STATUS_CANCELLED
            self.updated_by = request.user
            self.save()

    def suspend(self, request):
        with transaction.atomic():
            self.activity_status = ApplicationSelectedActivity.ACTIVITY_STATUS_SUSPENDED
            self.updated_by = request.user
            self.save()

    def reinstate(self, request):
        with transaction.atomic():
            self.activity_status = ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT
            self.updated_by = request.user
            self.save()

    def reissue(self, request):
        '''
        Sets this Selected Activity to be a status that allows for re-issuing
        by an approving officer.
        '''
        # TODO:AYN clear previous generated returns to allow re-generation.
        with transaction.atomic():
            self.application.reissue_activity(request, self)

    def mark_as_replaced(self, request):
        with transaction.atomic():
            # TODO:AYN mark on the licence purpose as well.
            self.activity_status = ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED
            self.updated_by = request.user
            self.save()

    def mark_selected_purpose_as_replaced(self, p_id):
        '''
        Set all Selected Purposes for the activity to a processing status of
        replaced.
        '''
        REPLACE = ApplicationSelectedActivityPurpose.PROCESSING_STATUS_REPLACED
        lp = LicencePurpose.objects.get(id=p_id)
        selected_purposes = self.proposed_purposes.filter(
            purpose=lp
        )

        for selected in selected_purposes:
            selected.processing_status = REPLACE
            selected.save()

    def store_proposed_attachments(self, proposed_attachments):
        """
        Stores proposed attachments from Temporary Document Collection to the
        Application Selected Activity.
        """
        with transaction.atomic():
            INPUT_NAME = 'proposed_attachment'
            try:
                for attachment in proposed_attachments.documents.all():
                    document = self.proposed_attachments.get_or_create(
                        application_id=self.application_id,
                        selected_activity_id=self.licence_activity_id,
                        input_name=INPUT_NAME)[0]
                    
                    document.name = str(attachment.name)

                    if document._file and os.path.isfile(document._file.path):
                        os.remove(document._file.path)
                    document.application_id = self.application_id
                    document.selected_activity_id = self.licence_activity_id

                    path = default_storage.save(
                      'wildlifecompliance/applications/{}/documents/{}'.format(
                          self.application_id), ContentFile(
                          attachment._file.read()))  

                    document._file = path                  
                    document.save()

            except BaseException:
                raise

    def get_activity_from_previous(self):
        '''
        Gets this Application Selected Activity from the previous Application
        Selected Activity application licence.

        TODO: Utilise Licence No to get previous instead of chain.
        '''
        previous = None
        prev_app = self.application.previous_application
        # prev_id = prev_app.id if prev_app else 0
        # current_id = self.application.licence_id
        status = {
            ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT,
            ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED,
        }
        prev = prev_app.get_current_activity_chain(
            activity_status__in=status).order_by(
                'licence_activity_id',
            )
        if not prev:
            return previous

        try:
            # Retrieve licence rather than from previous application. Previous
            # application may not have the same activity.
            # licence = WildlifeLicence.objects.get(
            #     id=current_id
            # )

            # prev = licence.current_activities
            act_id = self.licence_activity_id 
            prev = [a for a in prev if a.licence_activity_id == act_id]
            previous = prev[0]

        except WildlifeLicence.DoesNotExist:
            pass

        except BaseException as e:
            raise Exception('get_activity_from_previous(): {}'.format(e))

        return previous

class ApplicationSelectedActivityPurpose(models.Model):
    """
    A purpose selected for issue on an Application Selected Activity.
    """
    PROCESSING_STATUS_SELECTED = 'selected'
    PROCESSING_STATUS_PROPOSED = 'propose'
    PROCESSING_STATUS_ISSUED = 'issue'
    PROCESSING_STATUS_DECLINED = 'decline'
    PROCESSING_STATUS_REPLACED = 'replace'
    PROCESSING_STATUS_CHOICES = (
        (PROCESSING_STATUS_SELECTED, 'Selected for Proposal'),
        (PROCESSING_STATUS_PROPOSED, 'Proposed for Issue'),
        (PROCESSING_STATUS_DECLINED, 'Declined'),
        (PROCESSING_STATUS_ISSUED, 'Issued'),
        (PROCESSING_STATUS_REPLACED, 'Replaced'),
    )
    processing_status = models.CharField(
        'Processing Status',
        max_length=40,
        choices=PROCESSING_STATUS_CHOICES,
        default=PROCESSING_STATUS_SELECTED)
    selected_activity = models.ForeignKey(
        ApplicationSelectedActivity, related_name='proposed_purposes')
    purpose = models.ForeignKey(
        LicencePurpose, related_name='selected_activity_proposed_purpose')
    licence_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default='0')
    application_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default='0')
    # Adjusted Fee is an adjustment amount included to the application fee. It
    # occurs with questions selected by the applicant for an Activity Purpose.
    adjusted_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default='0')
    original_issue_date = models.DateTimeField(blank=True, null=True)
    issue_date = models.DateTimeField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)

    @property
    def is_proposed(self):
        '''
        An attribute to indicate that this selected Activity Purpose has been 
        selected for issuance.
        '''
        proposed_status = [
            self.PROCESSING_STATUS_PROPOSED,
            self.PROCESSING_STATUS_ISSUED,
            self.PROCESSING_STATUS_SELECTED,
        ]

        return True if self.processing_status in proposed_status else False

    @property
    def total_paid_amount(self):
        '''
        An attribute for the total fees paid for this Select Activity Purpose.
        The total amount includes fee, additional and licence fee.
        '''     
        amount = self.application_fee + self.licence_fee + self.adjusted_fee

        return amount

    @property
    def has_adjusted_application_fee(self):
        '''
        An Attribute indicating this Selected Activity Purpose has an adjusted 
        application fee different from the base admin fee.
        '''
        return True if self.adjusted_fee > 0 else False

    @property
    def pre_adjusted_application_fee(self):
        '''
        An attribute for the base admin fee amount paid for this Selected
        Activity Purpose regardless of any adjustments.
        '''
        return self.application_fee

    @property
    def is_reissued(self):
        '''
        Attribute to indicate that this purpose has been reissued.
        '''
        is_reissued = False

        try:
            i_date = self.issue_date
            o_date = self.original_issue_date
            i_dtime = datetime.datetime.strptime(
                i_date.strftime('%Y-%m-%d'),
                '%Y-%m-%d'
            )
            o_dtime = datetime.datetime.strptime(
                o_date.strftime('%Y-%m-%d'),
                '%Y-%m-%d'
            )

            is_reissued = False if idtime == o_dtime else True

        except BaseException as e:
            print(e)

        return is_reissued

    def __str__(self):
        application = self.selected_activity.application_id
        activity = self.selected_activity.licence_activity.short_name
        purpose = self.purpose.short_name
        return "{0}{1}{2}{3}{4}{5}".format(
            "Purpose: {purpose} ".format(purpose=purpose),
            "App. Fee: {fee1} ".format(fee1=self.application_fee),
            "Lic. Fee: {fee2} ".format(fee2=self.licence_fee),
            "Adj. Fee: {fee3} ".format(fee3=self.adjusted_fee),
            "(Act: {activity}".format(activity=activity),
            " App: {application})".format(application=application),
        )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'Application selected activity purpose'

    def get_purpose_from_previous(self):
        '''
        Gets this Application Selected Activity Purpose from the previous
        selected Activity.

        TODO: Utilise Licence No to get previous instead of chain.
        '''
        previous = None
        prev_app = self.selected_activity.application.previous_application
        # prev_id = prev_app.id if prev_app else 0
        # current_id = self.selected_activity.application.licence_id
        status = {
            ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT,
            ApplicationSelectedActivity.ACTIVITY_STATUS_REPLACED,
        }
        # activities = prev_app.get_current_activity_chain(
        #     activity_status__in=status).order_by(
        #         'licence_activity_id',
        #     )
        activities = prev_app.get_current_activity_chain(
            activity_status__in=status)

        if not activities:
            return previous

        try:
            # Retrieve licence rather than from previous application. Previous
            # application may not have the same purpose.
            # licence = WildlifeLicence.objects.get(
            #     id=current_id
            # )
            # activities = licence.current_activities

            act_id = self.selected_activity.licence_activity_id 
            self_id = self.purpose_id
            prev = [a for a in activities if a.licence_activity_id == act_id
                        and self.purpose in a.issued_purposes
            ]

            purposes = prev[0].proposed_purposes.all()
            prev = [p for p in purposes if p.purpose_id == self_id]
            previous = prev[0]

        except WildlifeLicence.DoesNotExist:
            pass

        except BaseException as e:
            print('get_purpose_from_previous(): ({0}) {1}'.format(self, e))
            raise Exception('get_purpose_from_previous(): {}'.format(e))

        return previous


class IssuanceDocument(Document):
    _file = models.FileField(max_length=255)
    # after initial submit prevent document from being deleted
    can_delete = models.BooleanField(default=True)
    selected_activity = models.ForeignKey(
        'ApplicationSelectedActivity',
        related_name='issuance_documents')

    class Meta:
        app_label = 'wildlifecompliance'


class ActivityInvoice(models.Model):
    PAYMENT_STATUS_NOT_REQUIRED = 'payment_not_required'
    PAYMENT_STATUS_UNPAID = 'unpaid'
    PAYMENT_STATUS_PARTIALLY_PAID = 'partially_paid'
    PAYMENT_STATUS_PAID = 'paid'
    PAYMENT_STATUS_OVERPAID = 'over_paid'

    activity = models.ForeignKey(
        ApplicationSelectedActivity, 
        related_name='activity_invoices')
    invoice_reference = models.CharField(
        max_length=50, null=True, blank=True, default='')
    invoice_datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        invoice = self.invoice_reference
        activity = self.activity.licence_activity.short_name
        return "{0}{1}".format(
            "Invoice: {invoice} ".format(invoice=invoice),
            "Activity: {activity} ".format(activity=activity),
        )

    @property
    def active(self):
        try:
            invoice = Invoice.objects.get(reference=self.invoice_reference)
            return False if invoice.voided else True
        except Invoice.DoesNotExist:
            pass
        return False

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = ('activity', 'invoice_reference',)


class ActivityInvoiceLine(models.Model):
    invoice = models.ForeignKey(
        ActivityInvoice, related_name='licence_activity_lines')
    licence_activity = models.ForeignKey(
        'wildlifecompliance.LicenceActivity', null=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2, default='0')

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return 'Invoice #{} - Activity {} : Amount {}'.format(
            self.invoice, self.licence_activity, self.amount)


@python_2_unicode_compatible
class ApplicationFormDataRecord(models.Model):

    INSTANCE_ID_SEPARATOR = "__instance-"

    ACTION_TYPE_ASSIGN_VALUE = 'value'
    ACTION_TYPE_ASSIGN_COMMENT = 'comment'

    COMPONENT_TYPE_TEXT = 'text'
    COMPONENT_TYPE_TAB = 'tab'
    COMPONENT_TYPE_SECTION = 'section'
    COMPONENT_TYPE_GROUP = 'group'
    COMPONENT_TYPE_NUMBER = 'number'
    COMPONENT_TYPE_EMAIL = 'email'
    COMPONENT_TYPE_SELECT = 'select'
    COMPONENT_TYPE_MULTI_SELECT = 'multi-select'
    COMPONENT_TYPE_TEXT_AREA = 'text_area'
    COMPONENT_TYPE_TABLE = 'table'
    COMPONENT_TYPE_EXPANDER_TABLE = 'expander_table'
    COMPONENT_TYPE_LABEL = 'label'
    COMPONENT_TYPE_RADIO = 'radiobuttons'
    COMPONENT_TYPE_CHECKBOX = 'checkbox'
    COMPONENT_TYPE_DECLARATION = 'declaration'
    COMPONENT_TYPE_FILE = 'file'
    COMPONENT_TYPE_DATE = 'date'
    COMPONENT_TYPE_SELECT_SPECIES = 'species'    
    COMPONENT_TYPE_CHOICES = (
        (COMPONENT_TYPE_TEXT, 'Text'),
        (COMPONENT_TYPE_TAB, 'Tab'),
        (COMPONENT_TYPE_SECTION, 'Section'),
        (COMPONENT_TYPE_GROUP, 'Group'),
        (COMPONENT_TYPE_NUMBER, 'Number'),
        (COMPONENT_TYPE_EMAIL, 'Email'),
        (COMPONENT_TYPE_SELECT, 'Select'),
        (COMPONENT_TYPE_MULTI_SELECT, 'Multi-Select'),
        (COMPONENT_TYPE_TEXT_AREA, 'Text Area'),
        (COMPONENT_TYPE_TABLE, 'Table'),
        (COMPONENT_TYPE_EXPANDER_TABLE, 'Expander Table'),
        (COMPONENT_TYPE_LABEL, 'Label'),
        (COMPONENT_TYPE_RADIO, 'Radio'),
        (COMPONENT_TYPE_CHECKBOX, 'Checkbox'),
        (COMPONENT_TYPE_DECLARATION, 'Declaration'),
        (COMPONENT_TYPE_FILE, 'File'),
        (COMPONENT_TYPE_DATE, 'Date'),
        (COMPONENT_TYPE_SELECT_SPECIES, 'Select Species'),
    )

    application = models.ForeignKey(
        Application, related_name='form_data_records')
    field_name = models.CharField(max_length=512, null=True, blank=True)
    schema_name = models.CharField(max_length=256, null=True, blank=True)
    instance_name = models.CharField(max_length=256, null=True, blank=True)
    component_type = models.CharField(
        max_length=64,
        choices=COMPONENT_TYPE_CHOICES,
        default=COMPONENT_TYPE_TEXT)
    component_attribute = JSONField(blank=True, null=True)
    value = JSONField(blank=True, null=True)
    officer_comment = models.TextField(blank=True)
    assessor_comment = models.TextField(blank=True)
    deficiency = models.TextField(blank=True)
    licence_activity = models.ForeignKey(
        LicenceActivity, related_name='form_data_records')
    licence_purpose = models.ForeignKey(
        LicencePurpose, related_name='form_data_records')

    def __str__(self):
        return "Application {id} record {field}".format(
            id=self.application_id,
            field=self.field_name
        )

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = ('application', 'field_name',)


@python_2_unicode_compatible
class ApplicationStandardCondition(RevisionedMixin):
    text = models.TextField()
    code = models.CharField(max_length=10, unique=True)
    obsolete = models.BooleanField(default=False)
    return_type = models.ForeignKey(
        'wildlifecompliance.ReturnType', null=True, blank=True)
    additional_information = models.TextField(
        max_length=1024, null=True, blank=True)

    def __str__(self):
        return self.code

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'Standard condition'


class DefaultCondition(OrderedModel):
    '''
    A Standard Condition that is automatically created for a Licence 
    Application.

    Applies django-smart-selects for chained foreign key.
    '''
    standard_condition = models.ForeignKey(
        ApplicationStandardCondition,
        related_name='default_condition', 
        null=True)    
    licence_activity = models.ForeignKey(
        'wildlifecompliance.LicenceActivity',
        related_name='default_activity', 
        null=True)
    # licence_purpose = models.ForeignKey(
    #     'wildlifecompliance.LicencePurpose',
    #     related_name='default_purpose',
    #     null=True)      
    licence_purpose = ChainedForeignKey(
        'wildlifecompliance.LicencePurpose',
        chained_field='licence_activity',
        chained_model_field='licence_activity',
        show_all=False,
        null=True,
        related_name='default_purpose',
    )
    comments = models.TextField(null=True, blank=True)

    class Meta:
        app_label = 'wildlifecompliance'


class ApplicationCondition(OrderedModel):
    APPLICATION_CONDITION_RECURRENCE_WEEKLY = 'weekly'
    APPLICATION_CONDITION_RECURRENCE_MONTHLY = 'monthly'
    APPLICATION_CONDITION_RECURRENCE_YEARLY = 'yearly'
    RECURRENCE_PATTERNS = (
        (APPLICATION_CONDITION_RECURRENCE_WEEKLY, 'Weekly'),
        (APPLICATION_CONDITION_RECURRENCE_MONTHLY, 'Monthly'),
        (APPLICATION_CONDITION_RECURRENCE_YEARLY, 'Yearly')
    )
    standard_condition = models.ForeignKey(
        ApplicationStandardCondition, null=True, blank=True)
    free_condition = models.TextField(null=True, blank=True)
    default_condition = models.ForeignKey(
        DefaultCondition, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    standard = models.BooleanField(default=True)
    is_rendered = models.BooleanField(default=False)
    application = models.ForeignKey(Application, related_name='conditions')
    due_date = models.DateField(null=True, blank=True)
    recurrence = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(
        max_length=20,
        choices=RECURRENCE_PATTERNS,
        default=APPLICATION_CONDITION_RECURRENCE_WEEKLY)
    recurrence_schedule = models.IntegerField(null=True, blank=True)
    licence_activity = models.ForeignKey(
        'wildlifecompliance.LicenceActivity', null=True)
    return_type = models.ForeignKey(
        'wildlifecompliance.ReturnType', null=True, blank=True)
    licence_purpose = models.ForeignKey(
        'wildlifecompliance.LicencePurpose', null=True, blank=True)
    source_group = models.ForeignKey(
        ActivityPermissionGroup, blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return 'Condition: {}'.format(self.condition[:256])

    def submit(self):
        if self.standard:
            self.return_type = self.standard_condition.return_type
            self.save()

    @property
    def condition(self):
        if self.standard:
            return self.standard_condition.text
        elif self.is_default:
            return self.default_condition.condition
        else:
            return self.free_condition

    def set_source(self, user):
        """
        Sets the users permission group as the source for this condition.
        """
        activity = self.application.activities.get(
            # Get the Application Selected Activity for this condition.
            licence_activity_id = self.licence_activity_id
        )
        if activity.processing_status ==\
             ApplicationSelectedActivity.PROCESSING_STATUS_WITH_ASSESSOR:
            # Set the source_group when added by the assessor.
            group = self.get_assessor_permission_group(user)
            self.source_group = group.activitypermissiongroup
            self.save()

        with_officer = [
            ApplicationSelectedActivity.PROCESSING_STATUS_WITH_OFFICER,
            ApplicationSelectedActivity.PROCESSING_STATUS_OFFICER_CONDITIONS]

        if activity.processing_status in with_officer:
            # Set the source_group when added by the officer.
            group = self.get_officer_permission_group(user)
            self.source_group = group.activitypermissiongroup
            self.save()

    def get_assessor_permission_group(self, user, first=True):
        app_label = get_app_label()
        qs = user.groups.filter(
            permissions__codename='assessor'
        )
        activity_id = self.licence_activity.id
        qs = qs.filter(
            activitypermissiongroup__licence_activities__id__in=activity_id\
                if isinstance(activity_id, (list, models.query.QuerySet)
                ) else [activity_id]
        )
        if app_label:
            qs = qs.filter(permissions__content_type__app_label=app_label)
        return qs.first() if first else qs

    def get_officer_permission_group(self, user, first=True):
        app_label = get_app_label()
        qs = user.groups.filter(
            permissions__codename='licensing_officer'
        )
        activity_id = self.licence_activity.id
        qs = qs.filter(
            activitypermissiongroup__licence_activities__id__in=activity_id\
                if isinstance(activity_id, (list, models.query.QuerySet)
                ) else [activity_id]
        )
        if app_label:
            qs = qs.filter(permissions__content_type__app_label=app_label)
        return qs.first() if first else qs


class ApplicationUserAction(UserAction):
    ACTION_CREATE_CUSTOMER_ = "Create customer {}"
    ACTION_CREATE_PROFILE_ = "Create profile {}"
    ACTION_LODGE_APPLICATION = "Lodge application {}"
    ACTION_SAVE_APPLICATION = "Save changes to application {}"
    ACTION_ASSIGN_TO_OFFICER = "Assign application {} to officer {}"
    ACTION_UNASSIGN_OFFICER = "Unassign officer from application {}"
    ACTION_ACCEPT_ID = "Accept ID"
    ACTION_RESET_ID = "Reset ID"
    ACTION_ID_REQUEST_UPDATE = 'Request ID update'
    ACTION_ACCEPT_CHARACTER = 'Accept character'
    ACTION_RESET_CHARACTER = "Reset character"
    ACTION_ACCEPT_REVIEW = 'Accept review'
    ACTION_RESET_REVIEW = "Reset review"
    ACTION_ID_REQUEST_AMENDMENTS = "Request amendments"
    ACTION_ID_REQUEST_AMENDMENTS_SUBMIT = "Amendment submitted by {}"
    ACTION_SEND_FOR_ASSESSMENT_TO_ = "Sent for assessment to {}"
    ACTION_SEND_ASSESSMENT_REMINDER_TO_ = "Send assessment reminder to {}"
    ACTION_ASSESSMENT_RECALLED = "Assessment recalled {}"
    ACTION_ASSESSMENT_RESENT = "Assessment Resent {}"
    ACTION_ASSESSMENT_COMPLETE = "Assessment Completed for group {} "
    ACTION_ASSESSMENT_ASSIGNED = "Assessment for {} Assigned to {}"
    ACTION_ASSESSMENT_UNASSIGNED = "Unassigned Assessor from Assessment for {}"
    ACTION_ASSESSMENT_INSPECTION_REQUEST = \
        "Inspection {} for Assessment {} was requested."    
    ACTION_DECLINE = "Decline application {}"
    ACTION_ENTER_CONDITIONS = "Entered condition for activity {}"
    ACTION_CREATE_CONDITION_ = "Create condition {}"
    ACTION_ORDER_CONDITION_UP = "Moved ordering higher for condition {}"
    ACTION_ORDER_CONDITION_DOWN = "Moved ordering lower for condition {}"
    ACTION_ISSUE_LICENCE_ = "Issue Licence for activity {}"
    ACTION_REISSUE_LICENCE_ = "Re-issuing Licence for activity {}"
    ACTION_DECLINE_LICENCE_ = "Decline Licence for activity {}"
    ACTION_DISCARD_APPLICATION = "Discard application {}"
    # Assessors
    ACTION_SAVE_ASSESSMENT_ = "Save assessment {}"
    ACTION_CONCLUDE_ASSESSMENT_ = "Conclude assessment {}"
    ACTION_PROPOSED_LICENCE = "Application {} has been proposed for issuing"
    ACTION_PROPOSED_DECLINE = "Application {} has been proposed for decline"

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, application, action, user):
        return cls.objects.create(
            application=application,
            who=user,
            what=str(action)
        )

    application = models.ForeignKey(Application, related_name='action_logs')


@receiver(pre_delete, sender=Application)
def delete_documents(sender, instance, *args, **kwargs):
    for document in instance.documents.all():
        document.delete()


'''
NOTE: REGISTER MODELS FOR REVERSION HERE.
'''
import reversion
reversion.register(
    Application, 
    follow=[
        'selected_activities',
        'invoices',
        'form_data_records',
        'conditions', 
        'action_logs', 
        'comms_logs',
        ]
    )
reversion.register(
    ApplicationSelectedActivity,
    follow=[
        'proposed_purposes',
        'activity_invoices',
        ]    
    )
reversion.register(ApplicationSelectedActivityPurpose)
reversion.register(ApplicationCondition)
reversion.register(ApplicationInvoice)
reversion.register(ApplicationInvoiceLine)
reversion.register(ApplicationDocument)
reversion.register(ApplicationStandardCondition)
reversion.register(ApplicationFormDataRecord)
reversion.register(ApplicationLogEntry)
reversion.register(ApplicationUserAction)
reversion.register(AmendmentRequest)
reversion.register(ActivityPermissionGroup)
reversion.register(ActivityInvoice)
reversion.register(ActivityInvoiceLine)
reversion.register(Assessment)
reversion.register(AssessmentInspection)