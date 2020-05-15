from django.urls import reverse
from ledger.accounts.models import EmailUser
# from wildlifecompliance.components.applications.utils import amendment_requests
from wildlifecompliance.components.applications.models import (
    Application,
    ApplicationUserAction,
    ApplicationLogEntry,
    ApplicationCondition,
    ApplicationStandardCondition,
    Assessment,
    ActivityPermissionGroup,
    AmendmentRequest,
    ApplicationSelectedActivity,
    ApplicationFormDataRecord,
    AssessmentInspection,
)
from wildlifecompliance.components.organisations.models import (
    Organisation
)
from wildlifecompliance.components.licences.models import LicenceActivity
from wildlifecompliance.components.main.serializers import CommunicationLogEntrySerializer
from wildlifecompliance.components.organisations.serializers import (
    OrganisationSerializer,
    ExternalOrganisationSerializer
)
from wildlifecompliance.components.users.serializers import UserAddressSerializer, DocumentSerializer
from wildlifecompliance.components.main.fields import CustomChoiceField
from wildlifecompliance import helpers
from wildlifecompliance.management.permissions_manager import PermissionUser

from rest_framework import serializers


class EmailUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'title',
            'organisation')

class ApplicationSelectedActivityCanActionSerializer(serializers.Serializer):
    """
    Custom serializer for ApplicationSelectedActivity.can_action DICT object for each action
    """
    licence_activity_id = serializers.IntegerField(read_only=True)
    can_renew = serializers.BooleanField(read_only=True)
    can_amend = serializers.BooleanField(read_only=True)
    can_surrender = serializers.BooleanField(read_only=True)
    can_cancel = serializers.BooleanField(read_only=True)
    can_suspend = serializers.BooleanField(read_only=True)
    can_reissue = serializers.SerializerMethodField(read_only=True)
    can_reinstate = serializers.BooleanField(read_only=True)

    class Meta:
        fields = (
            'licence_activity_id',
            'can_renew',
            'can_amend',
            'can_surrender',
            'can_cancel',
            'can_suspend',
            'can_reissue',
            'can_reinstate',
        )
        # the serverSide functionality of datatables is such that only columns that have field 'data'
        # defined are requested from the serializer. Use datatables_always_serialize to force render
        # of fields that are not listed as 'data' in the datatable columns
        datatables_always_serialize = fields

    def get_can_reissue(self, obj):
        try:
            user = self.context['request'].user
        except (KeyError, AttributeError):
            return False
        if user is None:
            return False
        perm_user = PermissionUser(user)
        return (user.has_perm('wildlifecompliance.system_administrator') or
            perm_user.has_wildlifelicenceactivity_perm([
                'issuing_officer',
            ], obj.get('licence_activity_id'))) and obj.get('can_reissue')


class ApplicationSelectedActivitySerializer(serializers.ModelSerializer):
    activity_name_str = serializers.SerializerMethodField(read_only=True)
    issue_date = serializers.SerializerMethodField(read_only=True)
    start_date = serializers.SerializerMethodField(read_only=True)
    expiry_date = serializers.SerializerMethodField(read_only=True)
    approve_options = serializers.SerializerMethodField(read_only=True)
    purposes = serializers.SerializerMethodField(read_only=True)
    activity_purpose_names = serializers.SerializerMethodField(read_only=True)
    processing_status = CustomChoiceField(read_only=True)
    activity_status = CustomChoiceField(read_only=True)
    can_action = ApplicationSelectedActivityCanActionSerializer(read_only=True)
    licence_fee = serializers.DecimalField(
        max_digits=8, decimal_places=2, coerce_to_string=False, read_only=True),
    payment_status = serializers.CharField(read_only=True)
    can_pay_licence_fee = serializers.SerializerMethodField()
    officer_name = serializers.SerializerMethodField(read_only=True)
    licensing_officers = EmailUserSerializer(many=True)
    issuing_officers = EmailUserSerializer(many=True)
    is_with_officer = serializers.SerializerMethodField(read_only=True)
    proposed_purposes = serializers.SerializerMethodField(read_only=True)
    additional_fee_text = serializers.CharField(
        required=False, allow_null=True)
    additional_fee = serializers.DecimalField(
        max_digits=7, decimal_places=2, required=False, allow_null=True)
    previous_paid_amount = serializers.SerializerMethodField(read_only=True)
    has_inspection = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ApplicationSelectedActivity
        fields = '__all__'

    def get_activity_name_str(self, obj):
        return obj.licence_activity.name if obj.licence_activity else ''

    def get_issue_date(self, obj):
        # return obj.get_issue_date().strftime('%d/%m/%Y %H:%M') if obj.get_issue_date() else ''
        return obj.get_issue_date() if obj.get_issue_date() else ''

    def get_start_date(self, obj):
        # return obj.get_start_date().strftime('%Y-%m-%d') if obj.get_start_date() else ''
        return obj.get_start_date() if obj.get_start_date() else ''

    def get_expiry_date(self, obj):
        # return obj.get_expiry_date().strftime('%Y-%m-%d') if obj.get_expiry_date() else ''
        return obj.get_expiry_date() if obj.get_expiry_date() else ''

    def get_approve_options(self, obj):
        return [{'label': 'Approved', 'value': 'approved'}, {'label': 'Declined', 'value': 'declined'}]

    def get_purposes(self, obj):
        from wildlifecompliance.components.licences.serializers import PurposeSerializer
        return PurposeSerializer(obj.purposes, many=True).data

    def get_proposed_purposes(self, obj):
        from wildlifecompliance.components.licences.serializers\
             import PurposeSerializer
        purposes = []
        proposed_purposes = obj.proposed_purposes.all()
        for proposed in proposed_purposes:
            purposes.append(proposed.purpose)
        return PurposeSerializer(purposes, many=True).data

    def get_issued_purposes(self, obj):
        from wildlifecompliance.components.licences.serializers\
             import PurposeSerializer
        purposes = obj.issued_purposes

        return PurposeSerializer(purposes, many=True).data

    def get_activity_purpose_names(self, obj):
        purposes = [p.purpose for p in obj.proposed_purposes.exclude(
            processing_status='decline')]

        if obj.proposed_action \
                == ApplicationSelectedActivity.PROPOSED_ACTION_DEFAULT:
            purposes = obj.purposes

        return ','.join([p.name for p in purposes])

    def get_can_pay_licence_fee(self, obj):
        return not obj.licence_fee_paid and obj.processing_status == ApplicationSelectedActivity.PROCESSING_STATUS_AWAITING_LICENCE_FEE_PAYMENT

    def get_officer_name(self, obj):
        return '{0} {1}'.format(obj.assigned_officer.first_name, obj.assigned_officer.last_name) if obj.assigned_officer else ''

    def get_is_with_officer(self, obj):
        return True if obj.processing_status in [
            'with_officer', 'with_officer_conditions'] else False

    def get_previous_paid_amount(self, obj):
        return obj.previous_paid_amount if obj.previous_paid_amount else None

    def get_has_inspection(self, obj):
        return obj.has_inspection


class ExternalApplicationSelectedActivitySerializer(serializers.ModelSerializer):
    activity_name_str = serializers.SerializerMethodField(read_only=True)
    issue_date = serializers.SerializerMethodField(read_only=True)
    start_date = serializers.SerializerMethodField(read_only=True)
    expiry_date = serializers.SerializerMethodField(read_only=True)
    activity_purpose_names = serializers.SerializerMethodField(read_only=True)
    activity_status = CustomChoiceField(read_only=True)
    can_action = ApplicationSelectedActivityCanActionSerializer(read_only=True)
    can_pay_licence_fee = serializers.SerializerMethodField()
    licence_fee = serializers.DecimalField(
        max_digits=8, decimal_places=2, coerce_to_string=False, read_only=True)
    payment_status = serializers.CharField(read_only=True)

    class Meta:
        model = ApplicationSelectedActivity
        fields = (
            'id',
            'activity_name_str',
            'issue_date',
            'start_date',
            'expiry_date',
            'activity_purpose_names',
            'activity_status',
            'can_action',
            'licence_fee',
            'payment_status',
            'can_pay_licence_fee',
        )
        # the serverSide functionality of datatables is such that only columns that have field 'data'
        # defined are requested from the serializer. Use datatables_always_serialize to force render
        # of fields that are not listed as 'data' in the datatable columns
        datatables_always_serialize = fields

    def get_activity_name_str(self, obj):
        return obj.licence_activity.name if obj.licence_activity else ''

    def get_issue_date(self, obj):
        # return obj.get_issue_date().strftime('%d/%m/%Y') if obj.get_issue_date() else ''
        return obj.get_issue_date() if obj.get_issue_date() else ''

    def get_start_date(self, obj):
        # return obj.get_start_date().strftime('%d/%m/%Y') if obj.get_start_date() else ''
        return obj.get_start_date() if obj.get_start_date() else ''

    def get_expiry_date(self, obj):
        # return obj.get_expiry_date().strftime('%d/%m/%Y') if obj.get_expiry_date() else ''
        return obj.get_expiry_date() if obj.get_expiry_date() else ''

    def get_activity_purpose_names(self, obj):
        return ','.join([p.name for p in obj.purposes])

    def get_can_pay_licence_fee(self, obj):
        return not obj.licence_fee_paid and obj.processing_status == ApplicationSelectedActivity.PROCESSING_STATUS_AWAITING_LICENCE_FEE_PAYMENT


class ExternalApplicationSelectedActivityMergedSerializer(serializers.Serializer):
    """
    Custom serializer for WildlifeLicence.latest_activities_merged LIST of DICT objects for each
    ApplicationSelectedActivity, therefore use of obj.get('fieldname') to retrieve data in SerializerMethodFields
    """
    licence_activity_id = serializers.IntegerField(read_only=True)
    activity_name_str = serializers.CharField(read_only=True)
    issue_date = serializers.SerializerMethodField(read_only=True)
    start_date = serializers.SerializerMethodField(read_only=True)
    expiry_date = serializers.SerializerMethodField(read_only=True)
    activity_purpose_names_and_status = serializers.CharField(read_only=True)
    can_action = ApplicationSelectedActivityCanActionSerializer(read_only=True)

    class Meta:
        fields = (
            'licence_activity_id',
            'activity_name_str',
            'issue_date',
            'start_date',
            'expiry_date',
            'activity_purpose_names_and_status',
            'can_action',
        )
        # the serverSide functionality of datatables is such that only columns that have field 'data'
        # defined are requested from the serializer. Use datatables_always_serialize to force render
        # of fields that are not listed as 'data' in the datatable columns
        datatables_always_serialize = fields

    def get_issue_date(self, obj):
        # return obj.get('issue_date').strftime('%d/%m/%Y') if obj.get('issue_date') else ''
        return obj.get('issue_date') if obj.get('issue_date') else ''

    def get_start_date(self, obj):
        # return obj.get('start_date').strftime('%d/%m/%Y') if obj.get('start_date') else ''
        return obj.get('start_date') if obj.get('start_date') else ''

    def get_expiry_date(self, obj):
        # return obj.get('expiry_date').strftime('%d/%m/%Y') if obj.get('expiry_date') else ''
        # return obj.get('expiry_date').strftime('%d/%m/%Y') if obj.get('expiry_date') else ''
        return obj.get('expiry_date') if obj.get('expiry_date') else ''


class EmailUserAppViewSerializer(serializers.ModelSerializer):
    residential_address = UserAddressSerializer()
    identification = DocumentSerializer()

    class Meta:
        model = EmailUser
        fields = ('id',
                  'email',
                  'first_name',
                  'last_name',
                  'dob',
                  'title',
                  'organisation',
                  'residential_address',
                  'identification',
                  'email',
                  'phone_number',
                  'mobile_number',)


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenceActivity
        fields = ('id', 'name', 'short_name')


class ActivityPermissionGroupSerializer(serializers.ModelSerializer):
    licence_activities = ActivitySerializer(many=True)

    class Meta:
        model = ActivityPermissionGroup
        fields = (
            'id',
            'name',
            'display_name',
            'licence_activities')


class AssessmentSerializer(serializers.ModelSerializer):
    assessor_group = ActivityPermissionGroupSerializer(read_only=True)
    status = CustomChoiceField(read_only=True)
    assessors = EmailUserAppViewSerializer(many=True)
    assigned_assessor = EmailUserSerializer()  

    class Meta:
        model = Assessment
        fields = (
            'id',
            'application',
            'assessor_group',
            'date_last_reminded',
            'status',
            'licence_activity',
            'final_comment',
            'is_inspection_required',
            'assessors',
            'assigned_assessor',
        )


class SimpleSaveAssessmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Assessment
        fields = (
            'final_comment',
            'is_inspection_required',
            )


class SaveAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = (
            'assessor_group',
            'application',
            'text',
            'licence_activity')

    def validate(self, data):
        licence_activity = data.get('licence_activity')
        assessor_group = data.get('assessor_group')
        if not licence_activity:
            raise serializers.ValidationError("No licence activity supplied!")

        group_match = ActivityPermissionGroup.get_groups_for_activities(
            licence_activity, 'assessor').filter(id=assessor_group.id).first()
        if not group_match:
            raise serializers.ValidationError("Invalid group (ID: %s) selected to assess activity ID: %s" % (
                assessor_group, licence_activity))

        return data


class ValidCompleteAssessmentSerializer(serializers.Serializer):
    activity_id = serializers.ListField(child=serializers.IntegerField())
    final_comment = serializers.CharField(
        required=False,
        allow_blank=True, 
        allow_null=True)

    def validate(self, data):
        # validate licence activity selected.
        activities = len(data.get('activity_id'))
        if activities < 1:
            raise serializers.ValidationError(
                'Please select a licence activity.')

        return data


class AmendmentRequestSerializer(serializers.ModelSerializer):
    reason = CustomChoiceField()

    class Meta:
        model = AmendmentRequest
        fields = '__all__'


class ExternalAmendmentRequestSerializer(serializers.ModelSerializer):
    reason = CustomChoiceField(read_only=True)
    licence_activity = ActivitySerializer(read_only=True)

    class Meta:
        model = AmendmentRequest
        fields = '__all__'


class ApplicationFormDataRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationFormDataRecord
        fields = (
            'field_name',
            'schema_name',
            'component_type',
            'instance_name',
            'officer_comment',
            'assessor_comment',
            'deficiency',
            'value',
            'licence_activity_id',
            'licence_purpose_id',
            'component_attribute',
        )
        read_only_fields = (
            'field_name',
            'schema_name',
            'component_type',
            'instance_name',
            'officer_comment',
            'assessor_comment',
            'deficiency',
            'value',
            'licence_activity_id',
            'licence_purpose_id',
            'component_attribute',
        )


class BaseApplicationSerializer(serializers.ModelSerializer):
    org_applicant = OrganisationSerializer()
    proxy_applicant = EmailUserAppViewSerializer()
    readonly = serializers.SerializerMethodField(read_only=True)
    licence_type_short_name = serializers.ReadOnlyField()
    documents_url = serializers.SerializerMethodField()
    character_check_status = CustomChoiceField(read_only=True)
    return_check_status = CustomChoiceField(read_only=True)
    application_fee = serializers.DecimalField(
        max_digits=8, decimal_places=2, coerce_to_string=False, read_only=True)
    category_id = serializers.SerializerMethodField(read_only=True)
    category_name = serializers.SerializerMethodField(read_only=True)
    activity_names = serializers.SerializerMethodField(read_only=True)
    activity_purpose_string = serializers.SerializerMethodField(read_only=True)
    purpose_string = serializers.SerializerMethodField(read_only=True)
    amendment_requests = serializers.SerializerMethodField(read_only=True)
    can_current_user_edit = serializers.SerializerMethodField(read_only=True)
    payment_status = serializers.SerializerMethodField(read_only=True)
    can_be_processed = serializers.SerializerMethodField(read_only=True)
    activities = serializers.SerializerMethodField()
    processed = serializers.SerializerMethodField()
    id_check_status = CustomChoiceField(read_only=True)
    processing_status = CustomChoiceField(read_only=True, choices=Application.PROCESSING_STATUS_CHOICES)
    data = ApplicationFormDataRecordSerializer(many=True)
    application_type = CustomChoiceField(read_only=True)
    invoice_url = serializers.SerializerMethodField(read_only=True)
    can_user_view = serializers.SerializerMethodField(read_only=True)
    payment_url = serializers.SerializerMethodField(read_only=True)
    total_paid_amount = serializers.SerializerMethodField(read_only=True)
    all_payments_url = serializers.SerializerMethodField(read_only=True)
    adjusted_paid_amount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Application
        fields = (
            'id',
            'data',
            'schema',
            'licence_type_data',
            'licence_type_name',
            'licence_type_short_name',
            'licence_category',
            'customer_status',
            'processing_status',
            'review_status',
            'applicant',
            'org_applicant',
            'proxy_applicant',
            'submitter',
            'previous_application',
            'lodgement_number',
            'lodgement_date',
            'documents',
            'conditions',
            'readonly',
            'can_user_edit',
            'can_user_view',
            'has_amendment',
            'amendment_requests',
            'documents_url',
            'id_check_status',
            'character_check_status',
            'return_check_status',
            'application_fee',
            'category_id',
            'category_name',
            'activity_names',
            'activity_purpose_string',
            'purpose_string',
            'can_current_user_edit',
            'payment_status',
            'can_be_processed',
            'activities',
            'processed',
            'application_type',
            'invoice_url',
            'total_paid_amount',
            'has_amended_fees',
            'payment_url',
            'requires_refund',
            'all_payments_url',
            'adjusted_paid_amount',
        )
        read_only_fields = ('documents',)

    def get_documents_url(self, obj):
        return '/media/applications/{}/documents/'.format(obj.id)

    def get_readonly(self, obj):
        return False

    def get_payment_status(self, obj):
        return obj.payment_status

    def get_category_id(self, obj):
        return obj.licence_category_id

    def get_category_name(self, obj):
        return obj.licence_category_name

    def get_activity_purpose_string(self, obj):
        activity_names = obj.licence_type_name.split(' - ')[1] if ' - ' in obj.licence_type_name else obj.licence_type_name
        return activity_names

    def get_purpose_string(self, obj):
        return obj.licence_purpose_names

    def get_activity_names(self, obj):
        return obj.licence_activity_names

    def get_activities(self, obj):
        return ApplicationSelectedActivitySerializer(obj.activities, many=True).data

    def get_amendment_requests(self, obj):
        amendment_request_data = []
        # qs = obj.amendment_requests
        # qs = qs.filter(status = 'requested')
        # if qs.exists():
        #     for item in obj.amendment_requests:
        #         print("printing from serializer")
        #         print(item.id)
        #         print(str(item.licence_activity.name))
        #         print(item.licence_activity.id)
        #         amendment_request_data.append({"licence_activity":str(item.licence_activity),"id":item.licence_activity.id})
        return amendment_request_data

    def get_can_be_processed(self, obj):
        return obj.activities.exclude(processing_status__in=[
            ApplicationSelectedActivity.PROCESSING_STATUS_DRAFT,
            ApplicationSelectedActivity.PROCESSING_STATUS_DECLINED,
            ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED,
            ApplicationSelectedActivity.PROCESSING_STATUS_AWAITING_LICENCE_FEE_PAYMENT,
        ]).exists()

    def get_processed(self, obj):
        """ check if any activities have been processed (i.e. licence issued)"""
        return True if obj.activities.filter(processing_status__in=[
            ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED,
            ApplicationSelectedActivity.PROCESSING_STATUS_DECLINED,
        ]).first() else False

    def get_can_current_user_edit(self, obj):
        result = False
        is_proxy_applicant = False
        is_in_org_applicant = False
        is_app_licence_officer = self.context['request'].user in obj.licence_officers
        is_submitter = obj.submitter == self.context['request'].user
        if obj.proxy_applicant:
            is_proxy_applicant = obj.proxy_applicant == self.context['request'].user
        if obj.org_applicant:
            user_orgs = [
                org.id for org in self.context['request'].user.wildlifecompliance_organisations.all()]
            is_in_org_applicant = obj.org_applicant_id in user_orgs

        result = False if obj.customer_status == \
            Application.CUSTOMER_STATUS_AWAITING_PAYMENT else obj.can_user_edit

        if obj.processing_status == \
                Application.PROCESSING_STATUS_AWAITING_APPLICANT_RESPONSE:
            # Outstanding amendment request - edit required.
            result = True

        if result and (
            is_app_licence_officer 
            or is_submitter
            or is_proxy_applicant
            or is_in_org_applicant):
                result = True
        return result

    def get_can_user_view(self, obj):
        result = True if obj.customer_status == \
            Application.CUSTOMER_STATUS_AWAITING_PAYMENT else obj.can_user_view
        return result

    def get_invoice_url(self, obj):
        url = None
        if obj.latest_invoice:
            url = reverse(
                'payments:invoice-pdf',
                kwargs={'reference': obj.latest_invoice.reference})

        return url

    def get_payment_url(self, app):
        """
        Builds a url link to ledger for invoice details associated with a
        licence activity on this application.
        """
        url = None

        if app.latest_invoice:  # url for latest invoice on app.
            url = '{}?invoice={}'.format(
                reverse('payments:invoice-payment'),
                app.latest_invoice.reference)

        return url

    def get_all_payments_url(self, app):
        """
        Builds a url link to ledger for all invoices associated with this
        application.
        """
        url = None

        if app.invoices.count() > 0:    # url for all invoices on app.
            invoices = app.invoices.all()
            invoice_str = app.latest_invoice.reference
            for invoice in invoices:
                invoice_str += '&invoice={}'.format(invoice.invoice_reference)

            if app.requires_refund:
                if app.application_type == \
                        Application.APPLICATION_TYPE_AMENDMENT:
                    previous = Application.objects.get(
                        id=app.previous_application.id)
                    invoices = previous.invoices.all()
                    for invoice in invoices:
                        invoice_str += '&invoice={}'.format(
                            invoice.invoice_reference)

            url = '{}?invoice={}'.format(
                reverse('payments:invoice-payment'),
                invoice_str)

        return url

    def get_total_paid_amount(self, obj):
        """
        Total amount paid on this application.
        """
        return obj.total_paid_amount

    def get_adjusted_paid_amount(self, obj):
        """
        Total paid amount adjusted for presentation purposes. Only applicable
        for internal officers to enforce refundable payments.

        TODO: REDUNDANT
        """
        # adjusted = None
        # # Include previously paid amounts for amendments.
        # adjusted = obj.total_paid_amount + obj.previous_paid_amount

        # if obj.processing_status == \
        #   Application.PROCESSING_STATUS_UNDER_REVIEW:
        #     # when Under Review, fee for amendment is paid and included in
        #     # previous paid amount as well as total paid amount. Need to
        #     # exclude this previous amount.
        #     adjusted = adjusted - obj.previous_paid_amount

        # # licence fee is paid with the application fee. Licence fee needs
        # # to be excluded from total paid for application.
        # licence_fee_paid = 0
        # for activity in obj.activities:
        #     licence_fee_paid += activity.licence_fee
        # adjusted = adjusted - licence_fee_paid

        adjusted = 0

        return adjusted


class DTInternalApplicationSerializer(BaseApplicationSerializer):
    submitter = EmailUserSerializer()
    applicant = serializers.CharField(read_only=True)
    org_applicant = OrganisationSerializer()
    proxy_applicant = EmailUserSerializer()
    processing_status = CustomChoiceField(read_only=True, choices=Application.PROCESSING_STATUS_CHOICES)
    customer_status = CustomChoiceField(read_only=True)
    can_current_user_edit = serializers.SerializerMethodField(read_only=True)
    payment_status = serializers.SerializerMethodField(read_only=True)
    can_be_processed = serializers.SerializerMethodField(read_only=True)
    user_in_officers = serializers.SerializerMethodField(read_only=True)
    application_type = CustomChoiceField(read_only=True)
    activities = ApplicationSelectedActivitySerializer(many=True, read_only=True)
    payment_url = serializers.SerializerMethodField(read_only=True)
    all_payments_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Application
        fields = (
            'id',
            'customer_status',
            'processing_status',
            'applicant',
            'proxy_applicant',
            'org_applicant',
            'submitter',
            'lodgement_number',
            'lodgement_date',
            'category_id',
            'category_name',
            'activity_names',
            'activity_purpose_string',
            'purpose_string',
            'can_user_view',
            'can_current_user_edit',
            'payment_status',
            'can_be_processed',
            'user_in_officers',
            'application_type',
            'activities',
            'invoice_url',
            'payment_url',
            'all_payments_url',
        )
        # the serverSide functionality of datatables is such that only columns that have field 'data'
        # defined are requested from the serializer. Use datatables_always_serialize to force render
        # of fields that are not listed as 'data' in the datatable columns
        datatables_always_serialize = fields

    def get_user_in_officers(self, obj):
        groups = obj.get_permission_groups(['licensing_officer','issuing_officer']).values_list('id', flat=True)
        can_process = EmailUser.objects.filter(groups__id__in=groups).distinct()               
        if self.context['request'].user and self.context['request'].user in can_process:
            return True

        return False

class DTExternalApplicationSerializer(BaseApplicationSerializer):
    submitter = EmailUserSerializer()
    applicant = serializers.CharField(read_only=True)
    org_applicant = ExternalOrganisationSerializer()
    proxy_applicant = EmailUserSerializer()
    processing_status = CustomChoiceField(read_only=True, choices=Application.PROCESSING_STATUS_CHOICES)
    customer_status = CustomChoiceField(read_only=True)
    can_current_user_edit = serializers.SerializerMethodField(read_only=True)
    payment_status = serializers.SerializerMethodField(read_only=True)
    application_type = CustomChoiceField(read_only=True)
    activities = ExternalApplicationSelectedActivitySerializer(many=True, read_only=True)
    invoice_url = serializers.SerializerMethodField(read_only=True)
    payment_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Application
        fields = (
            'id',
            'customer_status',
            'processing_status',
            'applicant',
            'org_applicant',
            'proxy_applicant',
            'submitter',
            'lodgement_number',
            'lodgement_date',
            'category_id',
            'category_name',
            'activity_names',
            'activity_purpose_string',
            'purpose_string',
            'can_user_view',
            'can_current_user_edit',
            'payment_status',
            'application_type',
            'activities',
            'invoice_url',
            'payment_url',
        )
        # the serverSide functionality of datatables is such that only columns that have field 'data'
        # defined are requested from the serializer. Use datatables_always_serialize to force render
        # of fields that are not listed as 'data' in the datatable columns
        datatables_always_serialize = fields


class WildlifeLicenceApplicationSerializer(BaseApplicationSerializer):
    """
    Minimised serializer for WildlifeLicence.current_application
    """
    applicant = serializers.CharField(read_only=True)
    org_applicant = ExternalOrganisationSerializer()
    proxy_applicant = EmailUserSerializer()

    class Meta:
        model = Application
        fields = (
            'id',
            'applicant',
            'org_applicant',
            'proxy_applicant',
            'submitter',
            'category_id',
            'category_name',
        )
        # the serverSide functionality of datatables is such that only columns that have field 'data'
        # defined are requested from the serializer. Use datatables_always_serialize to force render
        # of fields that are not listed as 'data' in the datatable columns
        datatables_always_serialize = fields


class ApplicationSerializer(BaseApplicationSerializer):
    submitter = serializers.CharField(source='submitter.get_full_name')
    processing_status = CustomChoiceField(read_only=True, choices=Application.PROCESSING_STATUS_CHOICES)
    review_status = CustomChoiceField(read_only=True)
    customer_status = CustomChoiceField(read_only=True)
    amendment_requests = serializers.SerializerMethodField(read_only=True)
    can_current_user_edit = serializers.SerializerMethodField(read_only=True)
    payment_status = serializers.SerializerMethodField(read_only=True)
    can_be_processed = serializers.SerializerMethodField(read_only=True)

    def get_readonly(self, obj):
        return not obj.can_user_edit

    def get_amendment_requests(self, obj):
        return ExternalAmendmentRequestSerializer(
            obj.active_amendment_requests.filter(status=AmendmentRequest.AMENDMENT_REQUEST_STATUS_REQUESTED),
            many=True
        ).data


class CreateExternalApplicationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, read_only=True)
    licence_purposes = serializers.ListField(required=False, write_only=True)
    data = ApplicationFormDataRecordSerializer(required=False, many=True)

    class Meta:
        model = Application
        fields = (
            'id',
            'data',
            'schema',
            'licence_type_data',
            'licence_type_name',
            'licence_category',
            'applicant',
            'org_applicant',
            'proxy_applicant',
            'submitter',
            'licence_purposes',
            'application_type',
            'previous_application',
            'licence',
        )


class SaveApplicationSerializer(BaseApplicationSerializer):

    class Meta:
        model = Application
        fields = (
            'id',
            'data',
            'comment_data',
            'schema',
            'customer_status',
            'review_status',
            'org_applicant',
            'proxy_applicant',
            'submitter',
            'previous_application',
            'lodgement_date',
            'documents',
            'conditions',
            'readonly',
            'can_user_edit',
            'can_user_view',
            'licence_type_data',
            'licence_type_name',
            'licence_category',
            'application_fee',
        )
        read_only_fields = ('documents', 'conditions')


class ApplicantSerializer(serializers.ModelSerializer):
    from wildlifecompliance.components.organisations.serializers import OrganisationAddressSerializer
    address = OrganisationAddressSerializer()

    class Meta:
        model = Organisation
        fields = (
            'id',
            'name',
            'abn',
            'address',
            'email',
            'phone_number',
        )


class InternalApplicationSerializer(BaseApplicationSerializer):
    applicant = serializers.CharField(read_only=True)
    org_applicant = OrganisationSerializer()
    proxy_applicant = EmailUserAppViewSerializer()
    processing_status = CustomChoiceField(read_only=True, choices=Application.PROCESSING_STATUS_CHOICES)
    review_status = CustomChoiceField(read_only=True)
    customer_status = CustomChoiceField(read_only=True)
    character_check_status = CustomChoiceField(read_only=True)
    return_check_status = CustomChoiceField(read_only=True)
    submitter = EmailUserAppViewSerializer()
    licences = serializers.SerializerMethodField(read_only=True)
    payment_status = serializers.SerializerMethodField(read_only=True)
    can_be_processed = serializers.SerializerMethodField(read_only=True)
    activities = serializers.SerializerMethodField()
    processed = serializers.SerializerMethodField()
    licence_officers = EmailUserAppViewSerializer(many=True)
    user_in_licence_officers = serializers.SerializerMethodField(read_only=True)
    user_roles = serializers.SerializerMethodField(read_only=True)
    assessments = AssessmentSerializer(many=True)
    licence_approvers = EmailUserAppViewSerializer(many=True)
    permit = serializers.CharField(source='licence_document._file.url')
    total_paid_amount = serializers.SerializerMethodField()
    adjusted_paid_amount = serializers.SerializerMethodField()


    class Meta:
        model = Application
        fields = (
            'id',
            'data',
            'schema',
            'application_type',
            'customer_status',
            'processing_status',
            'review_status',
            'id_check_status',
            'character_check_status',
            'return_check_status',
            'licence_type_data',
            'applicant',
            'org_applicant',
            'proxy_applicant',
            'submitter',
            'previous_application',
            'lodgement_date',
            'lodgement_number',
            'documents',
            'conditions',
            'readonly',
            'can_user_edit',
            'can_user_view',
            'documents_url',
            'comment_data',
            'licences',
            'permit',
            'payment_status',
            'can_be_processed',
            'licence_category',
            'activities',
            'processed',
            'licence_officers',
            'user_in_licence_officers',
            'user_roles',
            'assessments',
            'licence_approvers',
            'total_paid_amount',
            'adjusted_paid_amount',
        )
        read_only_fields = ('documents', 'conditions')

    def get_activities(self, obj):
        user = self.context['request'].user
        if user is None:
            return []
        application_activities = ApplicationSelectedActivity.objects.filter(
            application_id=obj.id
        )

        """
        # Uncomment to filter out activities that the internal user cannot assess / process (to hide activity tabs on the UI).
        if not user.has_perm('wildlifecompliance.system_administrator'):
            for activity in application_activities:
                if not user.has_wildlifelicenceactivity_perm([
                    'assessor',
                    'licensing_officer',
                    'issuing_officer',
                ], activity.licence_activity_id):
                    application_activities = application_activities.exclude(licence_activity_id=activity.licence_activity_id)
        """

        return ApplicationSelectedActivitySerializer(application_activities, many=True).data

    def get_readonly(self, obj):
        return True

    def get_licences(self, obj):
        licence_data = []
        active_licences = obj.get_licences_by_status(ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT)

        for licence in active_licences:
            for activity in licence.current_activities:
                licence_data.append(
                    {
                        "licence_activity": str(
                            activity.licence_activity),
                        "licence_activity_id": activity.licence_activity_id,
                        "start_date": activity.start_date,
                        "expiry_date": activity.expiry_date})
        return licence_data

    def get_processed(self, obj):
        """ check if any activities have been processed """
        return True if obj.activities.filter(processing_status__in=[
            ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED,
            ApplicationSelectedActivity.PROCESSING_STATUS_DECLINED
        ]).first() else False

    def get_user_in_licence_officers(self, obj):
        if self.context['request'].user and self.context['request'].user in obj.licence_officers:
            return True
        return False

    def get_user_roles(self, obj):
        try:
            user = self.context['request'].user
        except (KeyError, AttributeError):
            return []

        available_roles = ['assessor', 'licensing_officer', 'issuing_officer', 'return_curator']
        is_administrator = user.has_perm('wildlifecompliance.system_administrator')
        roles = []
        perm_user = PermissionUser(user)
        for activity in obj.selected_activities.all():
            for role in available_roles:
                if is_administrator or perm_user.has_wildlifelicenceactivity_perm(role, activity.licence_activity_id):
                    roles.append({'activity_id': activity.licence_activity_id, 'role': role})
        return roles


class ApplicationUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')

    class Meta:
        model = ApplicationUserAction
        fields = '__all__'


class ApplicationLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self, obj):
        return [[d.name, d._file.url] for d in obj.documents.all()]


class ApplicationConditionSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(
        input_formats=['%d/%m/%Y'],
        required=False,
        allow_null=True)
    purpose_name = serializers.SerializerMethodField(read_only=True)
    source_name = serializers.SerializerMethodField(read_only=True)
    source_group = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ApplicationCondition
        fields = (
            'id',
            'due_date',
            'free_condition',
            'standard_condition',
            'standard',
            'is_default',
            'default_condition',
            'order',
            'application',
            'recurrence',
            'recurrence_schedule',
            'recurrence_pattern',
            'condition',
            'licence_activity',
            'return_type',
            'licence_purpose',
            'source_group',
            'purpose_name',
            'source_name',
            )
        readonly_fields = ('order', 'condition')

    def get_purpose_name(self, obj):
        return obj.licence_purpose.short_name if obj.licence_purpose else None

    def get_source_name(self, obj):
        return obj.source_group.name if obj.source_group else 'SYSTEM'

    def get_source_group(self, obj):
        try:
            user = self.context['request'].user

        except (KeyError, AttributeError):
            return None

        is_member = None
        if obj.source_group and user:
            is_member = True if user in obj.source_group.members else False

        return obj.source_group.name if is_member else None


class ApplicationStandardConditionSerializer(serializers.ModelSerializer):
    require_return = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationStandardCondition
        fields = ('id', 'code', 'text', 'require_return')

    def get_require_return(self, obj):
        return True if obj.return_type else False


class ApplicationProposedIssueSerializer(serializers.ModelSerializer):
    """
    Application Selected Activities which have been proposed for issue.
    """
    proposed_action = CustomChoiceField(read_only=True)
    decision_action = CustomChoiceField(read_only=True)
    licence_activity = ActivitySerializer()
    issued_purposes_id = serializers.SerializerMethodField(read_only=True)
    additional_fee_text = serializers.CharField(
        required=False, allow_null=True)
    additional_fee = serializers.DecimalField(
        max_digits=7, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = ApplicationSelectedActivity
        fields = '__all__'

    def get_issued_purposes_id(self, obj):
        purposes = [p.id for p in obj.issued_purposes]

        return purposes


class ProposedLicenceSerializer(serializers.Serializer):
    expiry_date = serializers.DateField(
        input_formats=['%d/%m/%Y'], required=False, allow_null=True)
    start_date = serializers.DateField(
        input_formats=['%d/%m/%Y'], required=False, allow_null=True)
    reason = serializers.CharField()
    cc_email = serializers.CharField(required=False, allow_null=True)
    activity = serializers.ListField(child=serializers.IntegerField())
    approver_detail = serializers.CharField(required=False, allow_null=True)

    def validate(self, obj):
        # validate additional fees.
        activities = self.initial_data['activities']
        try:
            incomplete_fees = [a for a in activities if float(a[
                'additional_fee']) > 0 and not a['additional_fee_text']]
        except (TypeError):
            incomplete_fees = False  # Allow for NoneTypes in Fees.
        except (ValueError):
            raise serializers.ValidationError(
                'Numeric value required for additional fee amount.')

        if incomplete_fees:
            raise serializers.ValidationError(
                'Please provide description for additional fees.')

        return obj


class ProposedDeclineSerializer(serializers.Serializer):
    reason = serializers.CharField()
    cc_email = serializers.CharField(required=False, allow_null=True)
    activity = serializers.ListField(child=serializers.IntegerField())


class DTAssessmentSerializer(serializers.ModelSerializer):
    assessor_group = ActivityPermissionGroupSerializer(read_only=True)
    status = CustomChoiceField(read_only=True)
    licence_activity = ActivitySerializer(read_only=True)
    submitter = serializers.SerializerMethodField(read_only=True)
    application_lodgement_date = serializers.CharField(
        source='application.lodgement_date')
    applicant = serializers.CharField(source='application.applicant')
    application_category = serializers.CharField(
        source='application.licence_category_name')
    application = serializers.CharField(
        source='application.lodgement_number')
    application_id = serializers.CharField(
        source='application.id')
    application_type = CustomChoiceField(
        source='application.application_type',
        choices=Application.APPLICATION_TYPE_CHOICES,
        read_only=True)
    can_be_processed = serializers.SerializerMethodField(read_only=True)    

    class Meta:
        model = Assessment
        fields = (
            'id',
            'application',
            'assessor_group',
            'date_last_reminded',
            'status',
            'licence_activity',
            'submitter',
            'application_lodgement_date',
            'applicant',
            'application_category',
            'application_type',
            'application_id',
            'can_be_processed'
        )
        # the serverSide functionality of datatables is such that only columns that have field 'data'
        # defined are requested from the serializer. Use datatables_always_serialize to force render
        # of fields that are not listed as 'data' in the datatable columns
        datatables_always_serialize = fields

    def get_submitter(self, obj):
        return EmailUserSerializer(obj.application.submitter).data

    def get_can_be_processed(self, obj):
        groups = obj.application.get_permission_groups(['assessor']).values_list('id', flat=True)
        can_process = EmailUser.objects.filter(groups__id__in=groups).distinct()               
        if self.context['request'].user and self.context['request'].user in can_process and obj.status == obj.STATUS_AWAITING_ASSESSMENT:
            return True

        return False