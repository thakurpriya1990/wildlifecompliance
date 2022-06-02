import traceback

from rest_framework.fields import CharField
from ledger.accounts.models import EmailUser, Address
from wildlifecompliance.components.main.related_item import get_related_items
from wildlifecompliance.components.main.serializers import CommunicationLogEntrySerializer
from wildlifecompliance.components.users.serializers import (
    ComplianceUserDetailsOptimisedSerializer,
    #CompliancePermissionGroupMembersSerializer
)
from rest_framework import serializers
from django.core.exceptions import ValidationError
from wildlifecompliance.components.main.fields import CustomChoiceField

from wildlifecompliance.components.users.serializers import (
    ComplianceUserDetailsOptimisedSerializer,
    #CompliancePermissionGroupMembersSerializer,
    UserAddressSerializer,
)
from wildlifecompliance.components.artifact.models import (
        Artifact,
        DocumentArtifact,
        PhysicalArtifact,
        DocumentArtifactType,
        PhysicalArtifactType,
        PhysicalArtifactDisposalMethod,
        ArtifactCommsLogEntry,
        ArtifactUserAction,
        PhysicalArtifactFormDataRecord,
        BriefOfEvidenceRecordOfInterview,
        BriefOfEvidenceOtherStatements,
        BriefOfEvidencePhysicalArtifacts,
        BriefOfEvidenceDocumentArtifacts,
        ProsecutionBriefPhysicalArtifacts,
        ProsecutionBriefDocumentArtifacts,
        ProsecutionBriefRecordOfInterview,
        ProsecutionBriefOtherStatements,
        PhysicalArtifactLegalCases,
    )

from wildlifecompliance.components.offence.serializers import OffenceSerializer, OffenderSerializer
# local EmailUser serializer req?
from wildlifecompliance.components.call_email.serializers import EmailUserSerializer
from reversion.models import Version
from django.utils import timezone


class PhysicalArtifactFormDataRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicalArtifactFormDataRecord
        fields = (
            'field_name',
            'schema_name',
            'component_type',
            'instance_name',
            'comment',
            'deficiency',
            'value',
        )
        read_only_fields = (
            'field_name',
            'schema_name',
            'component_type',
            'instance_name',
            'comment',
            'deficiency',
            'value',
        )


class ArtifactSerializer(serializers.ModelSerializer):
    status = CustomChoiceField(read_only=True)
    artifact_object_type = serializers.SerializerMethodField()
    class Meta:
        model = Artifact
        fields = (
                'id',
                'identifier',
                'description',
                'artifact_date',
                'artifact_time',
                'artifact_object_type',
                'status',
                )
        read_only_fields = (
                'id',
                )

    def get_artifact_object_type(self, artifact_obj):
        artifact_object_type = None
        pa = PhysicalArtifact.objects.filter(artifact_ptr_id=artifact_obj.id)
        if pa and pa.first().id:
            artifact_object_type = 'physical'

        da = DocumentArtifact.objects.filter(artifact_ptr_id=artifact_obj.id)
        if da and da.first().id:
            artifact_object_type = 'document'

        return artifact_object_type


class ArtifactPaginatedSerializer(serializers.ModelSerializer):
    artifact_type_display = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    user_action = serializers.SerializerMethodField()
    entity = serializers.SerializerMethodField()
    digital_documents = serializers.SerializerMethodField()

    class Meta:
        model = Artifact
        fields = (
            'id',
            'number',
            'artifact_type',
            'status',
            'user_action',
            'artifact_date',
            'identifier',
            'description',
            'entity',
            'digital_documents',
            'artifact_type_display',
        )

    def get_status(self, obj):
        display_name = ''
        for choice in Artifact.STATUS_CHOICES:
            if obj.status == choice[0]:
                display_name = choice[1]
        return display_name

    def get_user_action(self, obj):
        #url_list = []
        #view_url = '<a href=/internal/object/' + str(obj.id) + '>View</a>'
        #url_list.append(view_url)

        #urls = '<br />'.join(url_list)
        url = '<a href=/internal/object/' + str(obj.id) + '>View</a>'
        if hasattr(obj, "physicalartifact") and obj.status == 'active':
            url = '<a href=/internal/object/' + str(obj.id) + '>Edit</a>'
        return url

    def get_entity(self, obj):
        entity = {
                'id': obj.id,
                'data_type': obj.object_type,
                'identifier': obj.identifier,
                'artifact_type': obj.artifact_type,
                'display': obj.artifact_type,
                }
        return entity

    def get_digital_documents(self, obj):
        url_list = []

        if obj.documents.all().count():
            for doc in obj.documents.all():
                url = '<a href="{}" target="_blank">{}</a>'.format(doc._file.url, doc.name)
                url_list.append(url)

        urls = '<br />'.join(url_list)
        return urls

    def get_artifact_type_display(self, artifact_obj):
        display_name = ''
        pa = PhysicalArtifact.objects.filter(artifact_ptr_id=artifact_obj.id)
        if pa and pa.first().id:
            physical_artifact = pa.first()
            for choice in PhysicalArtifactType.TYPE_CHOICES:
                if physical_artifact.artifact_type == choice[0]:
                    display_name = choice[1]

        da = DocumentArtifact.objects.filter(artifact_ptr_id=artifact_obj.id)
        if da and da.first().id:
            document_artifact = da.first()
            for choice in DocumentArtifact.DOCUMENT_TYPE_CHOICES:
                if document_artifact.document_type == choice[0]:
                    display_name = choice[1]
        return display_name


class PhysicalArtifactTypeSerializer(serializers.ModelSerializer):
    artifact_type_display = serializers.SerializerMethodField()
    class Meta:
        model = PhysicalArtifactType
        fields = (
                'id',
                'artifact_type',
                'details_schema',
                'storage_schema',
                'version',
                'description',
                'date_created',
                'artifact_type_display',
                )
        read_only_fields = (
                'id',
                )

    def get_artifact_type_display(self, obj):
        display_name = ''
        for choice in PhysicalArtifactType.TYPE_CHOICES:
            if obj.artifact_type == choice[0]:
                display_name = choice[1]
        return display_name


class PhysicalArtifactTypeSchemaSerializer(serializers.ModelSerializer):
    artifact_type_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = PhysicalArtifactType
        fields = (
            'id',
            'details_schema',
            'storage_schema',
            'artifact_type_id',
        )
        read_only_fields = (
            'id', 
            )

class PhysicalArtifactDisposalMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicalArtifactDisposalMethod
        fields = (
                'id',
                'disposal_method',
                'description',
                )
        read_only_fields = (
                'id',
                )


class DocumentArtifactStatementSerializer(serializers.ModelSerializer):
    document_type_display = serializers.SerializerMethodField()
    custodian = serializers.SerializerMethodField()

    class Meta:
        model = DocumentArtifact
        fields = (
                'id',
                'identifier',
                'description',
                'document_type_display',
                'custodian',
                )
        read_only_fields = (
                'id',
                )

    def get_document_type_display(self, obj):
        display_name = ''
        for choice in DocumentArtifact.DOCUMENT_TYPE_CHOICES:
            if obj.document_type == choice[0]:
                display_name = choice[1]
        return display_name

    def get_custodian(self, obj):
        custodian = None
        WITNESS_STATEMENT = 'witness_statement'
        RECORD_OF_INTERVIEW = 'record_of_interview'
        OFFICER_STATEMENT = 'officer_statement'
        EXPERT_STATEMENT = 'expert_statement'
        if obj.document_type in ('witness_statement', 'expert_statement') and obj.person_providing_statement:
            custodian = obj.person_providing_statement.get_full_name()
        elif obj.document_type in ('record_of_interview', 'officer_statement') and obj.officer_interviewer:
            custodian = obj.officer_interviewer.get_full_name()
        return custodian

class DocumentArtifactSerializer(serializers.ModelSerializer):
    statement = DocumentArtifactStatementSerializer(read_only=True)
    document_type_display = serializers.SerializerMethodField()
    person_providing_statement = EmailUserSerializer(read_only=True)
    officer_interviewer = EmailUserSerializer(read_only=True)
    interviewer = EmailUserSerializer(read_only=True)
    people_attending_id_list = serializers.SerializerMethodField()
    associated_legal_case_id_list = serializers.SerializerMethodField()
    offence = OffenceSerializer(read_only=True)
    offender = OffenderSerializer(read_only=True)
    related_items = serializers.SerializerMethodField()
    available_statement_artifacts = serializers.SerializerMethodField()
    primary_legal_case_id = serializers.SerializerMethodField()
    status = CustomChoiceField(read_only=True)

    class Meta:
        model = DocumentArtifact
        fields = (
                'id',
                'number',
                'identifier',
                'description',
                'artifact_date',
                'artifact_time',
                'document_type',
                'statement',
                'statement_id',
                'person_providing_statement',
                'interviewer',
                'people_attending_id_list',
                'associated_legal_case_id_list',
                'primary_legal_case_id',
                'offence',
                'offender',
                'offence_id',
                'offender_id',
                'related_items',
                'officer_interviewer',
                'document_type_display',
                'status',
                'created_at',
                'available_statement_artifacts',
                )
        read_only_fields = (
                'id',
                )

    def get_related_items(self, obj):
        return get_related_items(obj)

    def get_primary_legal_case_id(self, obj):
        return obj.primary_legal_case_id

    def get_associated_legal_case_id_list(self, obj):
        legal_case_id_list = []
        for legal_case in obj.legal_cases.all():
            legal_case_id_list.append(legal_case.id)
        return legal_case_id_list

    def get_people_attending_id_list(self, obj):
        people_attending_id_list = []
        for person in obj.people_attending.all():
            people_attending_id_list.append(person.id)
        return people_attending_id_list

    def get_document_type_display(self, obj):
        display_name = ''
        for choice in DocumentArtifact.DOCUMENT_TYPE_CHOICES:
            if obj.document_type == choice[0]:
                display_name = choice[1]
        return display_name

    def get_available_statement_artifacts(self, obj):
        artifact_list = []
        primary_legal_case = None
        for link in obj.documentartifactlegalcases_set.all():
            if link.primary:
                primary_legal_case = link.legal_case
        if primary_legal_case:
            for link in primary_legal_case.documentartifactlegalcases_set.all():
                    if (link.primary and link.document_artifact.document_type and 
                            link.document_artifact.document_type in [
                        'record_of_interview',
                        'witness_statement',
                        'expert_statement',
                        'officer_statement'
                    ]):
                        serialized_artifact = DocumentArtifactStatementSerializer(link.document_artifact)
                        artifact_list.append(serialized_artifact.data)
            return artifact_list


class SaveDocumentArtifactSerializer(serializers.ModelSerializer):
    statement_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    person_providing_statement_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    offence_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    offender_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    officer_interviewer_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = DocumentArtifact
        fields = (
                'id',
                'identifier',
                'description',
                'statement_id',
                'artifact_date',
                'artifact_time',
                'document_type',
                'person_providing_statement_id',
                'offence_id',
                'offender_id',
                'officer_interviewer_id',
                )
        read_only_fields = (
                'id',
                )


class PhysicalArtifactLegalCasesSerializer(serializers.ModelSerializer):

    class Meta:
        model = PhysicalArtifactLegalCases
        fields = (
                'id',
                'physical_artifact_id',
                'legal_case_id',
                'primary',
                'used_within_case',
                'sensitive_non_disclosable',
                )
        read_only_fields = (
                'id',
                )


class PhysicalArtifactSerializer(serializers.ModelSerializer):
    statement = DocumentArtifactSerializer(read_only=True)
    physical_artifact_type = PhysicalArtifactTypeSerializer(read_only=True)
    officer = EmailUserSerializer(read_only=True)
    disposal_method = PhysicalArtifactDisposalMethodSerializer(read_only=True)
    related_items = serializers.SerializerMethodField()
    associated_legal_case_id_list = serializers.SerializerMethodField()
    data = PhysicalArtifactFormDataRecordSerializer(many=True)
    status = CustomChoiceField(read_only=True)
    legal_case_links = serializers.SerializerMethodField()
    custodian = EmailUserSerializer(read_only=True)

    class Meta:
        model = PhysicalArtifact
        fields = (
                'id',
                'number',
                'identifier',
                'description',
                'artifact_date',
                'artifact_time',
                'statement',
                'statement_id',
                'physical_artifact_type',
                'physical_artifact_type_id',
                'disposal_method',
                'description',
                'officer',
                'disposal_date',
                'disposal_details',
                'disposal_method',
                'related_items',
                'associated_legal_case_id_list',
                'custodian',
                'status',
                'created_at',
                'data',
                'legal_case_links',
                )
        read_only_fields = (
                'id',
                )

    def get_related_items(self, obj):
        return get_related_items(obj)

    def get_legal_case_links(self, obj):
        legal_case_links = []
        for legal_case_link in obj.physicalartifactlegalcases_set.all():
            serializer = PhysicalArtifactLegalCasesSerializer(legal_case_link)
            legal_case_links.append(serializer.data)
        return legal_case_links

    def get_associated_legal_case_id_list(self, obj):
        legal_case_id_list = []
        for legal_case in obj.legal_cases.all():
            legal_case_id_list.append(legal_case.id)
        return legal_case_id_list


class SavePhysicalArtifactSerializer(serializers.ModelSerializer):
    statement_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    physical_artifact_type_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    custodian_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    officer_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = PhysicalArtifact
        fields = (
                'id',
                'identifier',
                'description',
                'custodian_id',
                'artifact_date',
                'artifact_time',
                'physical_artifact_type_id',
                'officer_id',
                'custodian_id',
                'statement_id',
                )
        read_only_fields = (
                'id',
                )


class ArtifactUserActionSerializer(serializers.ModelSerializer):
    who = serializers.SerializerMethodField()

    class Meta:
        model = ArtifactUserAction
        fields = '__all__'

    def get_who(self, obj):
        if obj.who:
            return obj.who.get_full_name()
        else:
            # When who==None, which means System performed the action
            return 'System'


class ArtifactCommsLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = ArtifactCommsLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self, obj):
        return [[d.name, d._file.url] for d in obj.documents.all()]


class BriefOfEvidenceRecordOfInterviewSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    hyperlink = serializers.SerializerMethodField()
    show = serializers.SerializerMethodField()

    class Meta:
        model = BriefOfEvidenceRecordOfInterview
        fields = (
                'id',
                'legal_case_id',
                'offence_id',
                'offender_id',
                'record_of_interview_id',
                'associated_doc_artifact_id',
                'ticked',
                'label',
                'hyperlink',
                'show',
                )
        read_only_fields = (
                'id',
                )

    def get_label(self, obj):
        return obj.label

    def get_hyperlink(self, obj):
        return obj.hyperlink

    def get_show(self, obj):
        return obj.show


class BriefOfEvidenceOtherStatementsSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    hyperlink = serializers.SerializerMethodField()
    show = serializers.SerializerMethodField()

    class Meta:
        model = BriefOfEvidenceOtherStatements
        fields = (
                'id',
                'legal_case_id',
                'person_id',
                'statement_id',
                'associated_doc_artifact_id',
                'ticked',
                'label',
                'hyperlink',
                'show',
                )
        read_only_fields = (
                'id',
                )

    def get_label(self, obj):
        return obj.label

    def get_hyperlink(self, obj):
        return obj.hyperlink

    def get_show(self, obj):
        return obj.show


class BriefOfEvidencePhysicalArtifactsSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    hyperlink = serializers.SerializerMethodField()

    class Meta:
        model = BriefOfEvidencePhysicalArtifacts
        fields = (
                'id',
                'legal_case_id',
                'physical_artifact_id',
                'ticked',
                'label',
                'hyperlink',
                'reason_sensitive_non_disclosable',
                )
        read_only_fields = (
                'id',
                )

    def get_label(self, obj):
        return obj.label

    def get_hyperlink(self, obj):
        return obj.hyperlink


class BriefOfEvidenceDocumentArtifactsSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    hyperlink = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = BriefOfEvidenceDocumentArtifacts
        fields = (
                'id',
                'legal_case_id',
                'document_artifact_id',
                'ticked',
                'label',
                'hyperlink',
                'attachments',
                )
        read_only_fields = (
                'id',
                )

    def get_attachments(self, obj):
        returned_file_data = [dict(
                    file=d._file.url,
                    id=d.id,
                    name=d.name,
                    type=d.name.split(".")[1]
                    ) for d in obj.document_artifact.documents.all() if d._file]
        return returned_file_data

    def get_label(self, obj):
        return obj.label

    def get_hyperlink(self, obj):
        return obj.hyperlink


class ProsecutionBriefRecordOfInterviewSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    hyperlink = serializers.SerializerMethodField()
    show = serializers.SerializerMethodField()

    class Meta:
        model = ProsecutionBriefRecordOfInterview
        fields = (
                'id',
                'legal_case_id',
                'offence_id',
                'offender_id',
                'record_of_interview_id',
                'associated_doc_artifact_id',
                'ticked',
                'label',
                'hyperlink',
                'show',
                )
        read_only_fields = (
                'id',
                )

    def get_label(self, obj):
        return obj.label

    def get_hyperlink(self, obj):
        return obj.hyperlink

    def get_show(self, obj):
        return obj.show

class ProsecutionBriefOtherStatementsSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    hyperlink = serializers.SerializerMethodField()
    show = serializers.SerializerMethodField()

    class Meta:
        model = ProsecutionBriefOtherStatements
        fields = (
                'id',
                'legal_case_id',
                'person_id',
                'statement_id',
                'associated_doc_artifact_id',
                'ticked',
                'label',
                'hyperlink',
                'show',
                )
        read_only_fields = (
                'id',
                )

    def get_label(self, obj):
        return obj.label

    def get_hyperlink(self, obj):
        return obj.hyperlink

    def get_show(self, obj):
        return obj.show


class ProsecutionBriefPhysicalArtifactsSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    hyperlink = serializers.SerializerMethodField()

    class Meta:
        model = ProsecutionBriefPhysicalArtifacts
        fields = (
                'id',
                'legal_case_id',
                'physical_artifact_id',
                'ticked',
                'label',
                'hyperlink',
                'reason_sensitive_non_disclosable',
                )
        read_only_fields = (
                'id',
                )

    def get_label(self, obj):
        return obj.label

    def get_hyperlink(self, obj):
        return obj.hyperlink


class ProsecutionBriefDocumentArtifactsSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    hyperlink = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = ProsecutionBriefDocumentArtifacts
        fields = (
                'id',
                'legal_case_id',
                'document_artifact_id',
                'ticked',
                'label',
                'hyperlink',
                'attachments',
                )
        read_only_fields = (
                'id',
                )

    def get_attachments(self, obj):
        returned_file_data = [dict(
                    file=d._file.url,
                    id=d.id,
                    name=d.name,
                    type=d.name.split(".")[1]
                    ) for d in obj.document_artifact.documents.all() if d._file]
        return returned_file_data

    def get_label(self, obj):
        return obj.label

    def get_hyperlink(self, obj):
        return obj.hyperlink

