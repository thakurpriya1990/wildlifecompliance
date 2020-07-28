from django.urls import reverse
from ledger.accounts.models import EmailUser
from wildlifecompliance.components.applications.models import ReturnRequest
from wildlifecompliance.components.main.fields import CustomChoiceField
from wildlifecompliance.components.returns.services import (
    ReturnService,
)
from wildlifecompliance.components.returns.models import (
    Return,
    ReturnType,
    ReturnUserAction,
    ReturnLogEntry,
)
from wildlifecompliance.components.applications.models import (
    ApplicationCondition,
    ApplicationStandardCondition,
)
from wildlifecompliance.components.licences.models import LicenceActivity
from rest_framework import serializers


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenceActivity
        fields = ('id', 'name', 'short_name')


class StandardConditionSerializer(serializers.ModelSerializer):
    require_return = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationStandardCondition
        fields = ('id', 'code', 'text', 'require_return')

    def get_require_return(self, obj):
        return True if obj.return_type else False


class ReturnConditionSerializer(serializers.ModelSerializer):
    standard_condition = StandardConditionSerializer(read_only=True)
    licence_activity = ActivitySerializer(read_only=True)
    due_date = serializers.SerializerMethodField(read_only=True)

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
            'return_type',)
        readonly_fields = ('order', 'condition')

    def get_due_date(self, obj):
        return obj.due_date.strftime('%d/%m/%Y') if obj.due_date else ''


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


class ReturnSerializer(serializers.ModelSerializer):
    # activity = serializers.CharField(source='application.activity')
    processing_status = serializers.CharField(
        source='get_processing_status_display')
    customer_status = serializers.SerializerMethodField()
    submitter = EmailUserSerializer()
    lodgement_number = serializers.SerializerMethodField()
    sheet_activity_list = serializers.SerializerMethodField()
    sheet_species_list = serializers.SerializerMethodField()
    sheet_species = serializers.SerializerMethodField()
    licence = serializers.SerializerMethodField()
    condition = ReturnConditionSerializer(read_only=True)
    table = serializers.SerializerMethodField()
    return_fee = serializers.DecimalField(
        max_digits=8, decimal_places=2, coerce_to_string=False, read_only=True)
    invoice_url = serializers.SerializerMethodField(read_only=True)
    activity_curators = EmailUserSerializer(many=True)
    amendment_requests = serializers.SerializerMethodField()
    is_draft = serializers.SerializerMethodField(read_only=True)   

    class Meta:
        model = Return
        fields = (
            'id',
            'application',
            'due_date',
            'processing_status',
            'customer_status',
            'submitter',
            'assigned_to',
            'lodgement_number',
            'lodgement_date',
            'nil_return',
            'licence',
            'resources',
            'table',
            'condition',
            'format',
            'template',
            'has_payment',
            'sheet_activity_list',
            'sheet_species_list',
            'sheet_species',
            'return_fee',
            'return_fee_paid',
            'invoice_url',
            'activity_curators',
            'amendment_requests',
            'is_draft',
        )

        # the serverSide functionality of datatables is such that only columns
        # that have field 'data' defined are requested from the serializer. Use
        # datatables_always_serialize to force render of fields that are not
        # listed as 'data' in the datatable columns
        datatables_always_serialize = fields

    def get_customer_status(self, _return):
        '''
        Get displayable custom choice for customer status.
        '''
        return _return.get_customer_status()

    def get_table(self, _return):
        '''
        '''
        return ReturnService.get_details_for(_return)

    def get_lodgement_number(self, _return):
        """
        Gets the lodgement number for a submitted Return.
        :param _return: Return instance.
        :return: lodgement number.
        """
        return _return.lodgement_number

    def get_sheet_activity_list(self, _return):
        """
        Gets the list of Activities available for a Return Running Sheet.
        :param _return: Return instance.
        :return: List of available activities.
        """
        # return _return.sheet.activity_list if _return.has_sheet else None
        return ReturnService.get_sheet_activity_list_for(_return)

    def get_sheet_species_list(self, _return):
        """
        Gets the list of Species available for a Return Running Sheet.
        :param _return: Return instance.
        :return: List of species for a Return Running Sheet.
        """
        # return _return.sheet.species_list if _return.has_sheet else None
        return ReturnService.get_sheet_species_list_for(_return)

    def get_sheet_species(self, _return):
        """
        Gets the Species available for a Return Running Sheet.
        :param _return: Return instance.
        :return: species identifier for a Return Running Sheet.
        """
        # return _return.sheet.species if _return.has_sheet else None
        return ReturnService.get_sheet_species_for(_return)

    def get_licence(self, _return):
        """
        Gets the formatted Licence Number from the return.
        :param _return: Return instance.
        :return: formatted Licence Number.
        """
        return _return.licence.licence_number

    def get_invoice_url(self, _return):
        url = None
        if _return.return_fee_paid:
            latest_invoice = _return.get_latest_invoice()
            if latest_invoice:
                url = reverse(
                    'payments:invoice-pdf',
                    kwargs={'reference': latest_invoice.reference})

        return url

    def get_amendment_requests(self, _return):
        '''
        Get list of requested amendments for this return.
        :param _return: Return instance.
        :return: list of ReturnRequest.
        '''
        requests = None
        requests = ReturnRequest.objects.filter(
            application_id=_return.application_id
        )

        return ReturnRequestSerializer(requests, many=True).data

    def get_is_draft(self, _return):
        '''
        Check for processing status is acceptable for submission by licensee.
        :param _return: Return instance.
        '''
        submission_list = [
            Return.RETURN_PROCESSING_STATUS_DUE,
            Return.RETURN_PROCESSING_STATUS_OVERDUE,
            Return.RETURN_PROCESSING_STATUS_DRAFT,
        ]

        return True if _return.processing_status in submission_list else False


class TableReturnSerializer(ReturnSerializer):
    '''
    Serialize returns information for data table presentation.
    '''
    class Meta:
        model = Return
        fields = (
            'id',
            'application',
            'due_date',
            'processing_status',
            'customer_status',
            'submitter',
            'assigned_to',
            'lodgement_number',
            'lodgement_date',
        )

        # the serverSide functionality of datatables is such that only columns
        # that have field 'data' defined are requested from the serializer. Use
        # datatables_always_serialize to force render of fields that are not
        # listed as 'data' in the datatable columns
        datatables_always_serialize = fields


class ExternalReturnSerializer(ReturnSerializer):
    '''
    Serialize returns information for external presentation.
    '''
    class Meta:
        model = Return
        fields = (
            'id',
            'application',
            'due_date',
            'processing_status',
            'customer_status',
            'submitter',
            'assigned_to',
            'lodgement_number',
            'lodgement_date',
        )

        # the serverSide functionality of datatables is such that only columns
        # that have field 'data' defined are requested from the serializer. Use
        # datatables_always_serialize to force render of fields that are not
        # listed as 'data' in the datatable columns
        datatables_always_serialize = fields


class InternalReturnSerializer(ReturnSerializer):
    '''
    Serialize returns information for internal presentation.
    '''
    class Meta:
        model = Return
        fields = (
            'id',
            'application',
            'due_date',
            'processing_status',
            'customer_status',
            'submitter',
            'assigned_to',
            'lodgement_number',
            'lodgement_date',
        )

        # the serverSide functionality of datatables is such that only columns
        # that have field 'data' defined are requested from the serializer. Use
        # datatables_always_serialize to force render of fields that are not
        # listed as 'data' in the datatable columns
        datatables_always_serialize = fields


class ReturnTypeSerializer(serializers.ModelSerializer):
    data_format = CustomChoiceField(read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = ReturnType
        fields = (
            'id',
            'resources',
            'data_format',
            'name',
        )

    def get_name(self, _return_type):
        """
        Present name with versioning.
        :param _return_type: Return_Type instance.
        :return: formatted name.
        """
        return '{0} - v{1}'.format(_return_type.name, _return_type.version)


class ReturnActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')

    class Meta:
        model = ReturnUserAction
        fields = '__all__'


class ReturnLogEntrySerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = ReturnLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self, obj):
        return [[d.name, d._file.url] for d in obj.documents.all()]


class ReturnRequestSerializer(serializers.ModelSerializer):
    reason = CustomChoiceField()

    class Meta:
        model = ReturnRequest
        fields = '__all__'
