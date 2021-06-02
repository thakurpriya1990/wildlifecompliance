from rest_framework import serializers

from ledger.accounts.models import EmailUser

from wildlifecompliance.components.main.models import (
    TemporaryDocumentCollection,
    CommunicationsLogEntry,
)

from wildlifecompliance.components.licences.models import SectionQuestion
from wildlifecompliance.components.licences.models import LicencePurposeSection
from wildlifecompliance.components.licences.models import MasterlistQuestion


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


class SchemaMasterlistSerializer(serializers.ModelSerializer):
    '''
    Serializer for Schema builder using Masterlist questions.
    '''
    # name = serializers.CharField(
    #     required=False,
    #     allow_blank=True,
    #     allow_null=True)
    name = serializers.CharField(read_only=True)

    class Meta:
        model = MasterlistQuestion
        fields = '__all__'


class DTSchemaMasterlistSerializer(SchemaMasterlistSerializer):
    '''
    Serializer for Schema Masterlist Datatables.
    '''
    class Meta:
        model = MasterlistQuestion
        fields = (
            'id',
            'name',
            'question',
            'option',
            'answer_type',
        )
        # the serverSide functionality of datatables is such that only columns
        # that have field 'data' defined are requested from the serializer. Use
        # datatables_always_serialize to force render of fields that are not
        # listed as 'data' in the datatable columns.
        datatables_always_serialize = fields


class DTSchemaMasterlistSelectSerializer(DTSchemaMasterlistSerializer):
    '''
    Serializer for all list selects required for Schema Masterlist datatable.
    '''
    all_answer_types = serializers.SerializerMethodField()

    class Meta:
        model = MasterlistQuestion
        fields = (
            'all_answer_types',
        )

    def get_all_answer_types(self, obj):
        '''
        Returns all Masterlist questions available for Schema Section Question.
        '''

        excl_choices = [
            # None
         ]

        answer_types = [
            {'value': a[0], 'label': a[1]} for a in obj.ANSWER_TYPE_CHOICES
            if a[0] not in excl_choices
        ]
        return answer_types


class SchemaPurposeSerializer(serializers.ModelSerializer):
    '''
    Serializer for Schema builder using Purpose sections.
    '''
    class Meta:
        model = LicencePurposeSection
        fields = '__all__'


class DTSchemaPurposeSerializer(SchemaPurposeSerializer):
    '''
    Serializer for Schema builder using Purpose sections.
    '''
    class Meta:
        model = LicencePurposeSection
        fields = '__all__'

        # the serverSide functionality of datatables is such that only columns
        # that have field 'data' defined are requested from the serializer. Use
        # datatables_always_serialize to force render of fields that are not
        # listed as 'data' in the datatable columns.
        datatables_always_serialize = fields


class SchemaGroupSerializer(serializers.ModelSerializer):
    '''
    Serializer for Schema builder using Sections Groups.
    '''
    class Meta:
        model = SectionQuestion
        fields = '__all__'

        # the serverSide functionality of datatables is such that only columns
        # that have field 'data' defined are requested from the serializer. Use
        # datatables_always_serialize to force render of fields that are not
        # listed as 'data' in the datatable columns.
        datatables_always_serialize = fields


class SchemaQuestionSerializer(serializers.ModelSerializer):
    '''
    Serializer for Schema builder using Section Questions.
    '''
    conditions = serializers.SerializerMethodField()

    class Meta:
        model = SectionQuestion
        fields = (
            'section',
            'question',
            'question_id',
            'parent_question',
            'parent_answer',
            'order',
            'conditions',
        )

    def get_conditions(self, obj):
        options = [
            {'label': 'IncreaseLicenceFee', 'value': ''},
            {'label': 'IncreaseRenewalFee', 'value': ''},
            {'label': 'IncreaseApplicationFee', 'value': ''},
            {'label': 'StandardCondition', 'value': ''},
            {'label': 'RequestInspection', 'value': False},
        ]
        return options


class DTSchemaQuestionSerializer(SchemaQuestionSerializer):
    '''
    Serializer for Schema builder using Section Questions.
    '''
    question = serializers.SerializerMethodField()
    section = SchemaPurposeSerializer()
    question_id = serializers.SerializerMethodField()
    licence_purpose = serializers.SerializerMethodField()

    class Meta:
        model = SectionQuestion
        fields = (
            'id',
            'section',
            'question',
            'question_id',
            'conditions',
            'licence_purpose',
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


class DTSchemaQuestionSelectSerializer(DTSchemaQuestionSerializer):
    '''
    Serializer for all list selects required for Schema Question datatable.
    '''
    all_masterlist = serializers.SerializerMethodField(read_only=True)
    all_purpose = serializers.SerializerMethodField(read_only=True)
    all_section = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SectionQuestion
        fields = (
            'all_masterlist',
            'all_purpose',
            'conditions',
            'all_section'
        )

    def get_all_masterlist(self, obj):
        '''
        Get all Masterlist questions available for Schema Section Question.
        '''
        qs = MasterlistQuestion.objects.all()
        serializer = SchemaMasterlistSerializer(qs, many=True)

        return serializer.data

    def get_all_purpose(self, obj):
        '''
        Get all Licence Purpose available for Schema Section Question.
        '''
        sections = LicencePurposeSection.objects.all()
        purposes = [
            {
                'label': s.licence_purpose.name, 'value': s.licence_purpose.id
            } for s in sections
        ]

        return purposes

    def get_all_section(self, obj):
        '''
        Get all Sections available for Schema Section Question.
        '''
        sections = LicencePurposeSection.objects.all()
        names = [
            {
                'label': s.section_label, 'value': s.id
            } for s in sections
        ]

        return names
