from django.urls import reverse
from ledger.accounts.models import EmailUser
from wildlifecompliance.components.applications.models import ReturnRequest
from wildlifecompliance.components.main.fields import CustomChoiceField
from wildlifecompliance.components.returns.services import (
    ReturnData,
    ReturnQuestion,
    ReturnSheet,
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
    child = None        # Sub Return (Data/Question/Sheet) associated.
    # activity = serializers.CharField(source='application.activity')
    # processing_status = serializers.CharField(
    #     source='get_processing_status_display')
    processing_status = serializers.SerializerMethodField()
    customer_status = serializers.SerializerMethodField()
    submitter = EmailUserSerializer()
    lodgement_number = serializers.SerializerMethodField()
    sheet_activity_list = serializers.SerializerMethodField()
    # sheet_species_list = serializers.SerializerMethodField()
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
    base_fee = serializers.SerializerMethodField(read_only=True)
    all_payments_url = serializers.SerializerMethodField(read_only=True)
    can_be_processed = serializers.SerializerMethodField(read_only=True)
    user_in_officers = serializers.SerializerMethodField(read_only=True)
    can_current_user_edit = serializers.SerializerMethodField(read_only=True)
    apply_fee_field = serializers.SerializerMethodField(read_only=True)
    species_list = serializers.SerializerMethodField(read_only=True)
    species_saved = serializers.SerializerMethodField(read_only=True)
    species = serializers.SerializerMethodField(read_only=True)
    has_species = serializers.SerializerMethodField(read_only=True)
    nil_return = serializers.SerializerMethodField(read_only=True)
    is_accepted = serializers.SerializerMethodField(read_only=True)

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
            # 'sheet_species_list',
            'sheet_species',
            'return_fee',
            'return_fee_paid',
            'invoice_url',
            'activity_curators',
            'amendment_requests',
            'is_draft',
            'total_paid_amount',
            'base_fee',
            'all_payments_url',
            'payment_status',
            'user_in_officers',
            'can_be_processed',
            'can_current_user_edit',
            'apply_fee_field',
            'species_list',
            'species_saved',
            'species',
            'has_species',
            'is_accepted',
        )

        # the serverSide functionality of datatables is such that only columns
        # that have field 'data' defined are requested from the serializer. Use
        # datatables_always_serialize to force render of fields that are not
        # listed as 'data' in the datatable columns
        datatables_always_serialize = fields

    def get_is_accepted(self, _return):
        ACCEPTED = Return.RETURN_PROCESSING_STATUS_ACCEPTED
        accepted = True if _return.processing_status == ACCEPTED else False

        return accepted

    def get_nil_return(self, _return):
        '''
        Get 'yes' or 'no' to indicate data has been included for Return.
        :param _return: Return instance.
        :return: string
        '''
        nil_return = 'yes' if _return.nil_return else 'no'

        return nil_return

    def get_child_return(self, _return):

        self.child = None

        if _return.has_sheet:
            self.child = ReturnSheet(_return)

        if _return.has_data:
            self.child = ReturnData(_return)

        if _return.has_question:
            self.child = ReturnQuestion(_return)

        return self.child

    def get_customer_status(self, _return):
        '''
        Get displayable custom choice for customer status.
        '''
        return _return.get_customer_status()

    def get_processing_status(self, _return):
        '''
        Get displayable custom choice for customer status.
        '''
        return _return.get_processing_status_display()

    def get_table(self, _return):
        '''
        '''
        child_return = self.child if self.child else self.get_child_return(
            _return
        )

        return child_return.table

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
        child_return = self.child if self.child else self.get_child_return(
            _return
        )
        return child_return.activity_list if _return.has_sheet else None

    # def get_sheet_species_list(self, _return):
    #     """
    #     Gets the list of Species available for a Return Running Sheet.
    #     :param _return: Return instance.
    #     :return: List of species for a Return Running Sheet.
    #     """
    #     child_return = self.child if self.child else self.get_child_return(
    #         _return
    #     )
    #     return child_return.species_list if _return.has_sheet else None

    def get_sheet_species(self, _return):
        """
        Gets the Species available for a Return Running Sheet.
        :param _return: Return instance.
        :return: species identifier for a Return Running Sheet.
        """
        child_return = self.child if self.child else self.get_child_return(
            _return
        )
        return child_return.species if _return.has_sheet else None

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

    def get_all_payments_url(self, _return):
        '''
        Builds a url link to ledger for all invoices associated with this
        return.
        '''
        url = None

        if _return.invoices.count() > 0:    # url for all invoices on return.
            invoices = _return.invoices.all()
            latest_invoice = _return.get_latest_invoice()
            invoice_str = latest_invoice.reference
            for invoice in invoices:
                invoice_str += '&invoice={}'.format(invoice.invoice_reference)

            url = '{}?invoice={}'.format(
                reverse('payments:invoice-payment'),
                invoice_str)

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

    def get_base_fee(self, _return):
        '''
        Get the base admin fee on the return type for this return.
        '''

        return _return.return_type.fee_amount

    def get_user_in_officers(self, _return):
        '''
        Check for current user is a returns curator.
        '''
        is_in_officers = False
        if self.context['request'].user in _return.activity_curators:
            is_in_officers = True

        return is_in_officers

    def get_can_be_processed(self, _return):
        '''
        A check that the return is in the correct processing status and
        current user is authorised (assigned) for the processing status.
        '''
        with_curator = [
            Return.RETURN_PROCESSING_STATUS_WITH_CURATOR,
        ]

        is_assigned = False
        if _return.assigned_to \
                and not _return.assigned_to == self.context['request'].user:
            is_assigned = True

        can_be_processed = False
        if _return.processing_status in with_curator:
            can_be_processed = True

        return can_be_processed and not is_assigned

    def get_can_current_user_edit(self, _return):
        '''
        A check for correct processing status for customer.
        '''
        with_customer = [
            Return.RETURN_PROCESSING_STATUS_DUE,
            Return.RETURN_PROCESSING_STATUS_OVERDUE,
            Return.RETURN_PROCESSING_STATUS_DRAFT,
            Return.RETURN_PROCESSING_STATUS_PAYMENT,
        ]
        can_user_edit = False
        is_submitter = _return.application.submitter \
            == self.context['request'].user

        if _return.processing_status in with_customer and is_submitter:
            can_user_edit = True

        return can_user_edit

    def get_apply_fee_field(self, _return):
        '''
        Get the field name of the first instance the Apply Fee attribute is set
        on the return type schema.
        '''
        from wildlifecompliance.components.returns.utils import (
            NumberFieldVisitor,
            ApplyFeeFieldElement,
        )
        schema_field = NumberFieldVisitor(_return, _return.format)
        for_apply_fee_fields = ApplyFeeFieldElement()
        for_apply_fee_fields.accept(schema_field)

        return for_apply_fee_fields.get_field_name()

    def get_species_list(self, obj):
        """
        Gets the list of Species available for a Return Running Sheet.
        :param obj: Return instance.
        :return: List of species for a Return Running Sheet.
        """
        child = self.child if self.child else self.get_child_return(obj)
        s_list = child.get_species_list() if not obj.has_question else None

        return s_list

    def get_species_saved(self, obj):
        """
        Gets the list of Species saved for a Return Running Sheet.
        :param obj: Return instance.
        :return: List of saved species for a Return Running Sheet.
        """
        child = self.child if self.child else self.get_child_return(obj)
        s_list = child.get_species_saved() if not obj.has_question else None

        return s_list

    def get_species(self, _return):
        """
        Gets the Species available for a Return Running Sheet.
        :param _return: Return instance.
        :return: species identifier for a Return Running Sheet.
        """
        child_return = self.child if self.child else self.get_child_return(
            _return
        )
        return child_return.species if not _return.has_question else None

    def get_has_species(self, _return):
        """
        A check whether species is required for this return.
        :param _return: Return instance.
        :return: boolean.
        """
        return _return.has_species_list


class TableReturnSerializer(ReturnSerializer):
    '''
    Serialize returns information for data table presentation.
    '''
    class Meta:
        model = Return
        fields = (
            'id',
            'due_date',
            'processing_status',
            'customer_status',
            'submitter',
            'assigned_to',
            'lodgement_number',
            'lodgement_date',
            'licence',
            'resources',
            'table',
            'condition',
            'format',
            'template',
            'has_payment',
            'return_fee',
            'return_fee_paid',
            'invoice_url',
            'activity_curators',
            'amendment_requests',
            'is_draft',
            'total_paid_amount',
            'base_fee',
            'all_payments_url',
            'payment_status',
            'user_in_officers',
            'can_be_processed',
            'can_current_user_edit',
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
