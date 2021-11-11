from rest_framework import serializers

from ledger.accounts.models import EmailUser

from wildlifecompliance.components.main.models import (
    TemporaryDocumentCollection,
    CommunicationsLogEntry,
)

from wildlifecompliance.components.licences.models import SectionQuestion
from wildlifecompliance.components.licences.models import SectionGroup
from wildlifecompliance.components.licences.models import LicencePurposeSection
from wildlifecompliance.components.licences.models import MasterlistQuestion
from wildlifecompliance.components.licences.models import LicencePurpose
from wildlifecompliance.components.licences.models import QuestionOption


class CommunicationLogEntrySerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(
        queryset=EmailUser.objects.all(), required=False)
    documents = serializers.SerializerMethodField()

    class Meta:
        model = CommunicationsLogEntry
        fields = (
            'id',
            'customer',
            'to',
            'fromm',
            'cc',
            'log_type',
            'reference',
            'subject'
            'text',
            'created',
            'staff',
            'application'
            'documents'
        )

    def get_documents(self, obj):
        return [[d.name, d._file.url] for d in obj.documents.all()]


class SearchKeywordSerializer(serializers.Serializer):
    number = serializers.CharField()
    record_id = serializers.IntegerField()
    record_type = serializers.CharField()
    applicant = serializers.CharField()
    text = serializers.JSONField(required=False)
    licence_document = serializers.CharField(
        source='licence_document._file.url',
        required=False
    )


class SearchReferenceSerializer(serializers.Serializer):
    url_string = serializers.CharField()


#class TemporaryDocumentSerializer(serializers.Serializer):
#    temp_document_collection_id = serializers.IntegerField()
#    uploaded_file = serializers.FileField(max_length=255)

class TemporaryDocumentCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemporaryDocumentCollection
        fields = ('id',)


class BookingSettlementReportSerializer(serializers.Serializer):
    date = serializers.DateTimeField(input_formats=['%d/%m/%Y'])


class OracleSerializer(serializers.Serializer):
    date = serializers.DateField(input_formats=['%d/%m/%Y','%Y-%m-%d'])
    override = serializers.BooleanField(default=False)


class SchemaOptionSerializer(serializers.ModelSerializer):
    '''
    Serializer for Schema builder using Masterlist questions.
    '''
    label = serializers.CharField(allow_blank=True, required=False)
    value = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = QuestionOption
        fields = '__all__'

    def create(self, validated_data):
        return QuestionOption.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.label = validated_data.get('label', instance.label)
        instance.value = validated_data.get('value', instance.value)


class SchemaMasterlistSerializer(serializers.ModelSerializer):
    '''
    Serializer for Schema builder using Masterlist questions.
    '''
    options = serializers.SerializerMethodField()
    headers = serializers.SerializerMethodField()
    expanders = serializers.SerializerMethodField()
    name = serializers.CharField(read_only=True)

    class Meta:
        model = MasterlistQuestion
        fields = '__all__'

    # def get_options_original(self, obj):
    #     option_labels = []
    #     try:
    #         options = self.initial_data.get('options', None)
    #         for o in options:
    #             if not o['label'] == '':
    #                 option_labels.append(o)
    #                 qo = QuestionOption.objects.filter(label=o['label'])
    #                 if qo.exists():
    #                     o['value'] = qo[0].id
    #                     continue
    #                 option_serializer = SchemaOptionSerializer(data=o)
    #                 option_serializer.is_valid(raise_exception=True)
    #                 option_serializer.save()
    #                 opt_id = option_serializer.data['id']
    #                 o['value'] = opt_id
    #         obj.set_property_cache_options(option_labels)
    def get_options(self, obj):
        option_labels = []
        try:
            options = self.initial_data.get('options', None)
            for o in options:
                if not o['label'] == '':
                    #option_labels.append(o)
                    qo = QuestionOption.objects.filter(label=o['label'])
                    if qo.exists():
                        o['value'] = qo[0].id
                    else:
                        option_serializer = SchemaOptionSerializer(data=o)
                        option_serializer.is_valid(raise_exception=True)
                        option_serializer.save()
                        opt_id = option_serializer.data['id']
                        o['value'] = opt_id
                    option_labels.append(o)
            obj.set_property_cache_options(option_labels)

        except Exception:
            options = None
            option_list = obj.get_options()
            if option_list:
                options = [
                    {
                        'label': o.label,
                        'value': o.value,
                        'conditions': obj.ANSWER_TYPE_CONDITIONS,

                    } for o in option_list
                ]

        return options

    def get_headers(self, obj):

        try:
            headers = self.initial_data.get('headers', None)
            obj.set_property_cache_headers(headers)
            obj.save()

        except Exception:
            headers = None
            header_list = obj.get_headers()
            if header_list:
                headers = [
                    {
                        'label': h['label'],
                        'value': h['value'],

                    } for h in header_list
                ]

        return headers

    def get_expanders(self, obj):

        try:
            expanders = self.initial_data.get('expanders', None)
            obj.set_property_cache_expanders(expanders)
            obj.save()

        except Exception:
            expanders = None
            expander_list = obj.get_expanders()
            if expander_list:
                expanders = [
                    {
                        'label': e['label'],
                        'value': e['value'],

                    } for e in expander_list
                ]

        return expanders


class DTSchemaMasterlistSerializer(SchemaMasterlistSerializer):
    '''
    Serializer for Schema Masterlist Datatables.
    '''
    options = serializers.SerializerMethodField()
    headers = serializers.SerializerMethodField()
    expanders = serializers.SerializerMethodField()

    class Meta:
        model = MasterlistQuestion
        fields = (
            'id',
            'name',
            'question',
            'answer_type',
            'options',
            'headers',
            'expanders',
        )
        # the serverSide functionality of datatables is such that only columns
        # that have field 'data' defined are requested from the serializer. Use
        # datatables_always_serialize to force render of fields that are not
        # listed as 'data' in the datatable columns.
        datatables_always_serialize = fields

    def get_options(self, obj):
        options = obj.get_options()
        data = [{'value': o.value, 'label': o.label} for o in options]
        return data

    def get_headers(self, obj):
        headers = obj.get_headers()
        data = [{'value': h['value'], 'label': h['label']} for h in headers]
        return data

    def get_expanders(self, obj):
        expanders = obj.get_expanders()
        data = [{'value': e['value'], 'label': e['label']} for e in expanders]
        return data


class LicencePurposeSerializer(serializers.ModelSerializer):
    '''
    Serializer for Licence Purpose.
    '''
    class Meta:
        model = LicencePurpose
        fields = '__all__'


class SchemaPurposeSerializer(serializers.ModelSerializer):
    '''
    Serializer for Schema builder using Purpose sections.
    '''
    section_name = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = LicencePurposeSection
        fields = '__all__'


class DTSchemaPurposeSerializer(SchemaPurposeSerializer):
    '''
    Serializer for datatables using Purpose sections.
    '''
    licence_purpose = serializers.SerializerMethodField()

    class Meta:
        model = LicencePurposeSection
        fields = (
            'id',
            'section_name',
            'section_label',
            'index',
            'licence_purpose',
        )

        # the serverSide functionality of datatables is such that only columns
        # that have field 'data' defined are requested from the serializer. Use
        # datatables_always_serialize to force render of fields that are not
        # listed as 'data' in the datatable columns.
        datatables_always_serialize = fields

    def get_licence_purpose(self, obj):
        return LicencePurposeSerializer(obj.licence_purpose).data


class SchemaGroupSerializer(serializers.ModelSerializer):
    '''
    Serializer for Schema builder using Sections Groups.
    '''
    group_name = serializers.CharField(allow_blank=True, required=False)
    repeatable = serializers.SerializerMethodField()

    class Meta:
        model = SectionGroup
        fields = '__all__'

    def get_repeatable(self, obj):
        try:
            repeatable = self.initial_data.get('repeatable', None)
            obj.set_property_cache_repeatable(repeatable)
            obj.save()

        except Exception:
            repeatable = obj.repeatable

        return repeatable


class DTSchemaGroupSerializer(SchemaGroupSerializer):
    '''
    Serializer for Schema Group Datatables.
    '''
    licence_purpose = serializers.SerializerMethodField()
    section = SchemaPurposeSerializer()

    class Meta:
        model = SectionGroup
        fields = (
            'id',
            'licence_purpose',
            'group_label',
            'section',
            'repeatable',
        )
        # the serverSide functionality of datatables is such that only columns
        # that have field 'data' defined are requested from the serializer. Use
        # datatables_always_serialize to force render of fields that are not
        # listed as 'data' in the datatable columns.
        datatables_always_serialize = fields

    def get_licence_purpose(self, obj):
        return LicencePurposeSerializer(obj.section.licence_purpose).data


class SchemaQuestionSerializer(serializers.ModelSerializer):
    '''
    Serializer for Schema builder using Section Questions.
    '''
    tag = serializers.ListField(child=serializers.CharField())
    # parent_question = SchemaMasterlistSerializer(read_only=True)
    # parent_answer = SchemaOptionSerializer(read_only=True)

    conditions = [
        {'label': 'IncreaseLicenceFee', 'value': ''},
        {'label': 'IncreaseRenewalFee', 'value': ''},
        {'label': 'IncreaseApplicationFee', 'value': ''},
        {'label': 'StandardCondition', 'value': ''},
        {'label': 'RequestInspection', 'value': False},
    ]
    options = serializers.SerializerMethodField()
    # conditions = serializers.SerializerMethodField()

    class Meta:
        model = SectionQuestion
        fields = (
            'section',
            'question',
            'parent_question',
            'parent_answer',
            'order',
            'section_group',
            'options',
            'tag',
        )

    def get_options(self, obj):
        try:
            options = self.initial_data.get('options', None)
            obj.set_property_cache_options(options)
            obj.save()

        except Exception:
            options = None
            option_list = obj.get_options()
            if option_list:
                options = [
                    {
                        'label': o.label,
                        'value': o.value,
                        'conditions': self.conditions

                    } for o in option_list
                ]

        return options

    # def get_conditions(self, obj):
    #     return self.conditions


class DTSchemaQuestionSerializer(SchemaQuestionSerializer):
    '''
    Serializer for Schema builder using Section Questions.
    '''
    question = serializers.SerializerMethodField()
    section = SchemaPurposeSerializer()
    question_id = serializers.SerializerMethodField()
    licence_purpose = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    section_group = SchemaGroupSerializer()

    class Meta:
        model = SectionQuestion
        fields = (
            'id',
            'section',
            'question',
            'question_id',
            'parent_question',
            'parent_answer',
            'licence_purpose',
            'section_group',
            'options',
            'tag',
            'order',
        )

        # the serverSide functionality of datatables is such that only columns
        # that have field 'data' defined are requested from the serializer. Use
        # datatables_always_serialize to force render of fields that are not
        # listed as 'data' in the datatable columns.
        datatables_always_serialize = fields

    def get_question(self, obj):
        masterlist = SchemaMasterlistSerializer(obj.question).data
        return masterlist['question']

    def get_question_id(self, obj):
        return obj.question_id

    def get_licence_purpose(self, obj):
        return obj.section.licence_purpose.name

    def get_options(self, obj):
        options = obj.get_options()
        data = [
            {
                'value': o['value'],
                'label': o['label'],
                'conditions': o['conditions']
            } for o in options
        ]
        return data
