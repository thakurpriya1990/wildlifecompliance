import logging
import re

from django.db.models import Q
from django.urls import reverse
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from ledger.payments.helpers import is_payment_admin
from wildlifecompliance.components.call_email.serializers import EmailUserSerializer
from wildlifecompliance.components.inspection.serializers import IndividualSerializer
from wildlifecompliance.components.main.fields import CustomChoiceField
from wildlifecompliance.components.main.related_item import get_related_items
from wildlifecompliance.components.main.serializers import CommunicationLogEntrySerializer
from wildlifecompliance.components.offence.models import AllegedOffence
from wildlifecompliance.components.offence.serializers import OffenderSerializer, \
    OffenceSerializer
from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDate
from wildlifecompliance.components.sanction_outcome_due.serializers import SanctionOutcomeDueDateSerializer
from wildlifecompliance.components.section_regulation.serializers import SectionRegulationSerializer
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, RemediationAction, \
    SanctionOutcomeCommsLogEntry, SanctionOutcomeUserAction, AllegedCommittedOffence, AmendmentRequestReason, \
    AmendmentRequestForRemediationAction, RemediationActionNotification, SanctionOutcomeDocumentAccessLog
from wildlifecompliance.components.users.serializers import CompliancePermissionGroupMembersSerializer
from wildlifecompliance.helpers import is_internal

logger = logging.getLogger('payment_checkout')


def can_user_approve(obj, user):
    # User can have action buttons
    # when user is assigned to the target object or
    # when user is a member of the allocated group and no one is assigned to the target object

    # user = self.context.get('request', {}).user
    offence = obj.sanction_outcome.offence
    if user.id == offence.assigned_to_id:
        return True
    elif offence.allocated_group and not offence.assigned_to_id:
        if user.id in [member.id for member in offence.allocated_group.members]:
            return True
    return False


class RemediationActionUpdateStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = RemediationAction
        fields = ('status',)

    def validate(self, data):
        new_status = data.get('status')
        req = self.context.get('request', {})
        obj = self.instance

        if new_status == RemediationAction.STATUS_ACCEPTED:
            if can_user_approve(self.instance, req.user):
                # Only a certain person can approve a remediation action
                return data
            else:
                raise serializers.ValidationError('You don\'t have permission')
        elif new_status == RemediationAction.STATUS_SUBMITTED:
            if req.user == obj.sanction_outcome.get_offender()[0]:
                # Only the offender of the remediation action can submit it
                return data
            else:
                raise serializers.ValidationError('You don\'t have permission')

        return data


class AmendmentRequestForRemediationActionSerializer(serializers.ModelSerializer):

    class Meta:
        model = AmendmentRequestForRemediationAction
        fields = (
            'reason',
            'details',
            'created_at',
            'updated_at',
        )


class RemediationActionSerializer(serializers.ModelSerializer):
    user_action = serializers.SerializerMethodField()
    action_taken_editable = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    status = CustomChoiceField(read_only=True)
    amendment_requests = AmendmentRequestForRemediationActionSerializer(read_only=True, many=True)

    class Meta:
        model = RemediationAction
        fields = (
            'id',
            'action',
            'status',
            'due_date',
            'user_action',
            'action_taken',
            'documents',
            'action_taken_editable',
            'remediation_action_id',
            'amendment_requests',
        )

    def can_user_approve(self, obj, user):
        return can_user_approve(obj, user)

    def get_action_taken_editable(self, obj):
        req = self.context.get('request', {})

        if req.user == obj.sanction_outcome.get_offender()[0] and obj.status in (RemediationAction.STATUS_OPEN):
            # if user is the offender
            # then editable
            return True
        return False

    def get_user_action(self, obj):
        req = self.context.get('request', {})

        view_url = '<a href="/external/remediation_action/' + str(obj.id) + '">View</a>'
        submit_url = '<a href="/external/remediation_action/' + str(obj.id) + '">Submit</a>'
        # accept_url = '<a href="/api/remediation_action/' + str(obj.id) + '/accept">Accept</a>'
        # request_amendment_url = '<a href="/api/remediation_action/' + str(obj.id) + '/request_amendment">Request Amendment</a>'
        accept_url = '<a data-id="{}" data-action="{}" class="accept_remediation_action">Accept</a>'.format(str(obj.id), 'accept')
        request_amendment_url = '<a data-id="{}" data-action="{}" class="request_amendment_remediation_action">Request Amendment</a>'.format(str(obj.id), 'request_amendment')

        url_list = []

        if is_internal(req):
            if self.can_user_approve(obj, req.user) and obj.status == RemediationAction.STATUS_SUBMITTED:
                # If User is one of the officers of the obj.sanction_outcome and if obj.status is submitted
                # then 'accept' and 'request amendment'
                url_list.append(accept_url)
                url_list.append(request_amendment_url)
        else:
            if req.user == obj.sanction_outcome.get_offender()[0]:
                if obj.status == RemediationAction.STATUS_OPEN:
                    url_list.append(submit_url)
                else:
                    url_list.append(view_url)

        urls = '<br />'.join(url_list)
        return urls

    def get_documents(self, obj):
        url_list = []

        if obj.documents.all().count():
            # Paper notices
            for doc in obj.documents.all():
                url = '<a href="{}" target="_blank">{}</a>'.format(doc._file.url, doc.name)
                url_list.append(url)

        urls = '<br />'.join(url_list)
        return urls


class AllegedOffenceSerializer(serializers.ModelSerializer):
    offence = OffenceSerializer(read_only=True)
    section_regulation = SectionRegulationSerializer(read_only=True)

    class Meta:
        model = AllegedOffence
        fields = (
            'id',
            'offence',
            'section_regulation',
        )
        validators = [
            UniqueTogetherValidator(
                queryset=AllegedOffence.objects.filter(removed=False),
                fields=['offence', 'section_regulation'],
                message='Offence cannot associated with the sambe section regulation more than once'
            )
        ]

    def validate(self, data):
        # TODO: Add object level validation here if needed
        return data


class AllegedCommittedOffenceCreateSerializer(serializers.ModelSerializer):
    alleged_offence_id = serializers.IntegerField(write_only=True,)
    sanction_outcome_id = serializers.IntegerField(write_only=True,)

    class Meta:
        model = AllegedCommittedOffence
        fields = (
            'alleged_offence_id',
            'sanction_outcome_id',
        )

    def validate(self, data):
        request = self.context.get('request', {})
        offender_id = request.data.get('offender_id', 0)
        alleged_offence = AllegedOffence.objects.get(id=data['alleged_offence_id'])
        acos = AllegedCommittedOffence.get_active_alleged_committed_offences(alleged_offence)

        for aco in acos:
            if aco.sanction_outcome.offender:
                # Sanction outcome has an offender
                if aco.sanction_outcome.offender.person.id == offender_id:
                    # Sanction outcome has been already created for this offender
                    raise serializers.ValidationError('Sanction outcome has been issued for the alleged offence: {} - {} to the offender: {}'.format(
                        alleged_offence.section_regulation.act,
                        alleged_offence.section_regulation.name,
                        aco.sanction_outcome.offender.person))
            else:
                # Sanction outome has been already created without any offenders
                raise serializers.ValidationError('Sanction outcome has been issued for the alleged offence: {} - {}'.format(
                    alleged_offence.section_regulation.act,
                    alleged_offence.section_regulation.name))

        # if acos.count():
        #     # TODO:
        #     ao = acos.first().alleged_offence
        #     raise serializers.ValidationError('Alleged offence: %s is duplicated' % ao)

        return data


class RemediationActionNotificationCreateSerializer(serializers.ModelSerializer):
    remediation_action_id = serializers.IntegerField(write_only=True,)
    sanction_outcome_comms_log_entry_id = serializers.IntegerField(write_only=True,)

    class Meta:
        model = RemediationActionNotification
        fields = (
            'remediation_action_id',
            'sanction_outcome_comms_log_entry_id',
            'type',
        )

    def validate(self, data):
        return data


class AllegedCommittedOffenceSerializer(serializers.ModelSerializer):
    alleged_offence = AllegedOffenceSerializer(read_only=True,)
    # removed_by_id = serializers.IntegerField(write_only=True, required=False)
    in_editable_status = serializers.SerializerMethodField()
    can_user_restore = serializers.SerializerMethodField()

    class Meta:
        model = AllegedCommittedOffence
        fields = (
            'id',
            'included',
            # 'removed',
            # 'reason_for_removal',
            # 'removed_by',
            # 'removed_by_id',
            'alleged_offence',
            'in_editable_status',
            'can_user_restore',
        )

    def get_in_editable_status(self, obj):
        # Check if the sanction outcome is in the status of STATUS_AWAITING_AMENDMENT or SanctionOutcome,
        # Which means the sanction outcome is under some officer at the moment, therefore it should be editable
        return obj.sanction_outcome.status in (SanctionOutcome.STATUS_DRAFT,)

    def get_can_user_restore(self, obj):
        can_user_restore = False

        if self.get_in_editable_status(obj):
            existing = AllegedCommittedOffence.objects.filter(sanction_outcome=obj.sanction_outcome, alleged_offence=obj.alleged_offence, included=True)
            if not existing:
                # If there is not same alleged committed offence in the database, there should be restore button
                can_user_restore = True

        return can_user_restore


class SanctionOutcomeSerializer(serializers.ModelSerializer):
    status = CustomChoiceField(read_only=True)
    type = CustomChoiceField(read_only=True)
    payment_status = CustomChoiceField(read_only=True)
    # payment_status = serializers.ReadOnlyField()
    alleged_committed_offences = serializers.SerializerMethodField()
    offender = OffenderSerializer(read_only=True,)
    offence = OffenceSerializer(read_only=True,)
    allocated_group = serializers.SerializerMethodField()
    user_in_group = serializers.SerializerMethodField()
    can_user_action = serializers.SerializerMethodField()
    user_is_assignee = serializers.SerializerMethodField()
    related_items = serializers.SerializerMethodField()
    paper_notices = serializers.SerializerMethodField()
    due_dates = serializers.SerializerMethodField()
    is_parking_offence = serializers.ReadOnlyField()
    registration_holder = IndividualSerializer()
    driver = IndividualSerializer()
    remediation_actions = RemediationActionSerializer(read_only=True, many=True)  # This is related field

    class Meta:
        model = SanctionOutcome
        fields = (
            'id',
            'type',
            'status',
            'payment_status',
            'lodgement_number',
            'region_id',
            'district_id',
            'identifier',
            'offence',
            'offender',
            'alleged_committed_offences',
            'issued_on_paper',
            'paper_id',
            'paper_notices',
            'description',
            'date_of_issue',
            'time_of_issue',
            'assigned_to_id',
            'allocated_group',
            'allocated_group_id',
            'user_in_group',
            'can_user_action',
            'user_is_assignee',
            'related_items',
            'penalty_amount_1st',
            'penalty_amount_2nd',
            'due_date_extended_max',
            'due_dates',
            'is_parking_offence',
            'registration_holder',
            'driver',
            'registration_holder_id',
            'driver_id',
            'registration_number',
            'remediation_actions',
        )

    def get_due_dates(self, obj):
        ret = []

        for date in obj.due_dates.all():
            ret.append(SanctionOutcomeDueDateSerializer(date).data)

        return ret

    def get_paper_notices(self, obj):
        return [[r.name, r._file.url] for r in obj.documents.all()]

    def get_allocated_group(self, obj):
        allocated_group = [{
            'email': '',
            'first_name': '',
            'full_name': '',
            'id': None,
            'last_name': '',
            'title': '',
        }]
        returned_allocated_group = CompliancePermissionGroupMembersSerializer(instance=obj.allocated_group)
        for member in returned_allocated_group.data['members']:
            allocated_group.append(member)

        return allocated_group

    def get_user_in_group(self, obj):
        user_id = self.context.get('request', {}).user.id

        if obj.allocated_group:
            for member in obj.allocated_group.members:
                if user_id == member.id:
                    return True
        return False

    def get_can_user_action(self, obj):
        # User can have action buttons
        # when user is assigned to the target object or
        # when user is a member of the allocated group and no one is assigned to the target object
        user_id = self.context.get('request', {}).user.id
        if user_id == obj.assigned_to_id:
            return True
        elif obj.allocated_group and not obj.assigned_to_id:
            if user_id in [member.id for member in obj.allocated_group.members]:
                return True

        return False

    def get_user_is_assignee(self, obj):
        user_id = self.context.get('request', {}).user.id
        if user_id == obj.assigned_to_id:
            return True

        return False

    def get_related_items(self, obj):
        return get_related_items(obj)

    def get_alleged_committed_offences(self, so_obj):
        qs_allegedCommittedOffences = so_obj.retrieve_alleged_committed_offences()
        return [AllegedCommittedOffenceSerializer(item, context={'request': self.context.get('request', {})}).data for item in qs_allegedCommittedOffences]


class UpdateAssignedToIdSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = SanctionOutcome
        fields = (
            'assigned_to_id',
        )


class SanctionOutcomeDocumentAccessLogSerializer(serializers.ModelSerializer):
    sanction_outcome_document_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    accessed_by_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = SanctionOutcomeDocumentAccessLog
        fields = (
            'sanction_outcome_document_id',
            'accessed_by_id',
        )


class SanctionOutcomeDatatableSerializer(serializers.ModelSerializer):
    payment_status = CustomChoiceField(read_only=True)
    # payment_status = serializers.ReadOnlyField()
    status = CustomChoiceField(read_only=True)
    type = CustomChoiceField(read_only=True)
    user_action = serializers.SerializerMethodField()
    # offender = OffenderSerializer(read_only=True,)
    offender = serializers.SerializerMethodField()
    paper_notices = serializers.SerializerMethodField()
    coming_due_date = serializers.ReadOnlyField()
    # remediation_actions = serializers.SerializerMethodField()
    # remediation_actions = RemediationActionSerializer(read_only=True, many=True)  # This is related field
    remediation_actions = serializers.SerializerMethodField()

    class Meta:
        model = SanctionOutcome
        fields = (
            'id',
            'type',
            'payment_status',
            'status',
            'lodgement_number',
            'region',
            'district',
            'identifier',
            'offence',
            'offender',
            'alleged_offences',
            'issued_on_paper',
            'paper_id',
            'description',
            'date_of_issue',
            'time_of_issue',
            'user_action',
            'paper_notices',
            'coming_due_date',
            'remediation_actions',
        )
        read_only_fields = ()

    def get_remediation_actions(self, obj):
        r_actions = obj.remediation_actions.all().order_by('due_date')
        remes = RemediationActionSerializer(r_actions, many=True, context={'request': self.context.get('request', {})})
        return remes.data

    def get_offender(self, obj):
        if obj.driver:
            serializer = EmailUserSerializer(obj.driver)
            return serializer.data
        elif obj.registration_holder:
            serializer = EmailUserSerializer(obj.registration_holder)
            return serializer.data
        elif obj.offender:
            serializer = OffenderSerializer(obj.offender)
            return serializer.data
        else:
            return ''

    def get_paper_notices(self, obj):
        url_list = []

        if obj.documents.all().count():
            # Paper notices
            for doc in obj.documents.all():
                if self.context.get('internal', False):
                    count_logs = doc.access_logs.count()
                    viewed_text = ' Viewed by offender: <i class="fa fa-check-circle fa-lg viewed-by-offender" aria-hidden="true"></i>' if count_logs else ''
                    url = '<a href="{}" target="_blank">{}</a>'.format(doc._file.url, doc.name) + viewed_text
                else:
                    # To detect if the external user accessing the pdf file, we make Django serve the pdf file
                    url = '<a href="/api/sanction_outcome/{}/doc?name={}" target="_blank">{}</a>'.format(obj.id, doc.name, doc.name)
                url_list.append(url)

        urls = '<br />'.join(url_list)
        return urls

    def get_user_action(self, obj):
        url_list = []

        # Retrieve existing invoice if there is
        inv_ref = ''
        if obj.infringement_penalty:
            ipi = obj.infringement_penalty.infringement_penalty_invoices.all().last()
            if ipi:
                inv_ref = ipi.invoice_reference

        user = self.context.get('request', {}).user
        view_url = '<a href=/internal/sanction_outcome/' + str(obj.id) + '>View</a>'
        process_url = '<a href=/internal/sanction_outcome/' + str(obj.id) + '>Process</a>'
        view_payment_url = '<a href="/ledger/payments/invoice/payment?invoice=' + inv_ref + '">View Payment</a>' if inv_ref else ''
        cc_payment_url = '<a href="#" data-pay-infringement-penalty="' + str(obj.id) + '">Pay</a>'

        record_payment_url = '<a href="' + reverse('payments:invoice-payment') + '?invoice={}'.format(inv_ref) + '">Record Payment</a>' if inv_ref \
            else '<a href="' + reverse('preview_deferred_invoicing', kwargs={'sanction_outcome_pk': obj.id}) + '">Record Payment</a>'

        if user == obj.get_offender()[0]:
            # If offender
            if obj.payment_status == 'unpaid' and obj.status == SanctionOutcome.STATUS_AWAITING_PAYMENT:
                url_list.append(cc_payment_url)
        elif is_internal(self.context.get('request')):
            if obj.status not in SanctionOutcome.FINAL_STATUSES:
                # infringement notice is not in the final statuses
                if user.id == obj.assigned_to_id:
                    # if user is assigned to the object, the user can process it
                    url_list.append(process_url)
                elif (obj.allocated_group and not obj.assigned_to_id) and user.id in [member.id for member in obj.allocated_group.members]:
                    # if user belongs to the same group of the object
                    # and no one is assigned to the object,
                    # the user can process it
                    url_list.append(process_url)

                if is_payment_admin(user):
                    if inv_ref:
                        # There is an invoice
                        if obj.payment_status != SanctionOutcome.PAYMENT_STATUS_PAID:
                            if obj.payment_status == SanctionOutcome.PAYMENT_STATUS_PARTIALLY_PAID:
                                # Partially paid
                                url_list.append(record_payment_url)
                            elif obj.payment_status == SanctionOutcome.PAYMENT_STATUS_UNPAID:
                                url_list.append(cc_payment_url)
                                url_list.append(record_payment_url)
                        else:
                            # Paid
                            url_list.append(view_payment_url)
                    else:
                        if obj.payment_status != SanctionOutcome.PAYMENT_STATUS_PAID and obj.status == SanctionOutcome.STATUS_AWAITING_PAYMENT:
                            url_list.append(cc_payment_url)
                            url_list.append(record_payment_url)
                        else:
                            # Should not reach here
                            logger.warn('Sanction Outcome: {} payment status is PAID, but no invoices found.')

            if not url_list:
                # In other case user can view
                url_list.append(view_url)

        urls = '<br />'.join(url_list)
        return urls


class RecordFerCaseNumberSerializer(serializers.ModelSerializer):

    class Meta:
        model = SanctionOutcome
        fields = (
            'fer_case_number',
        )

    def validate(self, data):
        field_errors = {}

        z = re.match("^\d{2}\/[0-9 ]{8}$", data['fer_case_number'])
        if not z:
            field_errors['FER Case Number'] = ['This must be fomatted like 12/34567890',]
        if field_errors:
            raise serializers.ValidationError(field_errors)

        return data


class SaveSanctionOutcomeSerializer(serializers.ModelSerializer):
    offence_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    offender_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    region_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    district_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    allocated_group_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    registration_holder_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    driver_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = SanctionOutcome
        fields = (
            'id',
            'type',
            'identifier',
            'offence_id',
            'offender_id',
            'region_id',
            'district_id',
            'allocated_group_id',
            'issued_on_paper',
            'paper_id',
            'description',
            'date_of_issue',
            'time_of_issue',
            'registration_holder_id',
            'driver_id',
            'registration_number',
            'status',
        )

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        if not data['region_id']:
            non_field_errors.append('Sanction Outcome must have a region')

        if data['issued_on_paper']:
            if not data['paper_id']:
                non_field_errors.append('Paper ID is required')
            if not data['date_of_issue']:
                non_field_errors.append('Date of Issue is required')
            if not data['time_of_issue']:
                non_field_errors.append('Time of Issue is required')
            if not self.context['num_of_documents_attached']:
                non_field_errors.append('Paper notice is required')
            if not data['offender_id']:
                # Offender should be on the paper issued already
                non_field_errors.append('Offender is required')

        if field_errors:
            raise serializers.ValidationError(field_errors)

        if non_field_errors:
            raise serializers.ValidationError(non_field_errors)

        return data

    def create(self, validated_data):
        """
        this method is called when creating new record after the validate() method.
        here is the best place to edit data here if needed
        """

        return super(SaveSanctionOutcomeSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        """
        this method is called when updating existing record after the validate() method.
        here is the best place to edit data here if needed
        """
        return super(SaveSanctionOutcomeSerializer, self).update(instance, validated_data)


class SaveRemediationActionSerializer(serializers.ModelSerializer):
    sanction_outcome_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = RemediationAction
        fields = (
            'id',
            'action',
            'due_date',
            'action_taken',
            'sanction_outcome_id',
        )

    def validate(self, obj):
        return obj


class SanctionOutcomeUserActionSerializer(serializers.ModelSerializer):
    # who = serializers.CharField(source='who.get_full_name')
    who = serializers.SerializerMethodField()

    class Meta:
        model = SanctionOutcomeUserAction
        fields = '__all__'

    def get_who(self, obj):
        if obj.who:
            return obj.who.get_full_name()
        else:
            # When who==None, which means System performed the action
            return 'System'


class SanctionOutcomeCommsLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(SanctionOutcomeCommsLogEntrySerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = SanctionOutcomeCommsLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self, obj):
        docs = []
        for d in obj.documents.all():
            if d._file:
                docs.append([d.name, d._file.url])
            else:
                if d.name:
                    # If there is d.name but no d._file, we expect that which is infringement notice pdf file
                    # docs.append([d.name, '/sanction_outcome/pdf/' + str(obj.sanction_outcome.id)])
                    pass
        return docs
        # return [[d.name, d._file.url] for d in obj.documents.all()]


class AmendmentRequestReasonSerializer(serializers.ModelSerializer):

    class Meta:
        model = AmendmentRequestReason
        fields = '__all__'


class SaveAmendmentRequestForRemediationAction(serializers.ModelSerializer):
    remediation_action_id = serializers.IntegerField(write_only=True,)

    class Meta:
        model = AmendmentRequestForRemediationAction
        fields = ('reason',
                  'details',
                  'remediation_action_id')

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        if not data.get('reason'):
            field_errors['Reason'] = ['Please select a reason',]
        if not data.get('details'):
            field_errors['Details'] = ['Please enter details.',]
        if not data.get('remediation_action_id'):
            non_field_errors.append('Something wrong...')

        if field_errors:
            raise serializers.ValidationError(field_errors)
        if non_field_errors:
            raise serializers.ValidationError(non_field_errors)
        return data
