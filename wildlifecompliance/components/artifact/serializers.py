import traceback

from rest_framework.fields import CharField
from ledger.accounts.models import EmailUser, Address
from wildlifecompliance.components.main.related_item import get_related_items
from wildlifecompliance.components.main.serializers import CommunicationLogEntrySerializer
from wildlifecompliance.components.users.serializers import (
    ComplianceUserDetailsOptimisedSerializer,
    CompliancePermissionGroupMembersSerializer
)
from rest_framework import serializers
from django.core.exceptions import ValidationError
from wildlifecompliance.components.main.fields import CustomChoiceField

from wildlifecompliance.components.users.serializers import (
    ComplianceUserDetailsOptimisedSerializer,
    CompliancePermissionGroupMembersSerializer,
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
        #LegalCaseRunningSheetArtifacts,
        )

from wildlifecompliance.components.offence.serializers import OffenceSerializer, OffenderSerializer
# local EmailUser serializer req?
from wildlifecompliance.components.call_email.serializers import EmailUserSerializer
#from wildlifecompliance.components.legal_case.serializers import LegalCaseSerializer
from reversion.models import Version
from django.utils import timezone


#class LegalCasePrioritySerializer(serializers.ModelSerializer):
#    class Meta:
#        model = LegalCasePriority
#        fields = ('__all__')
#        read_only_fields = (
#                'id',
#                )

class ArtifactSerializer(serializers.ModelSerializer):
    #custodian = EmailUserSerializer(read_only=True)
    #statement = DocumentArtifactStatementSerializer(read_only=True)
    artifact_object_type = serializers.SerializerMethodField()
    class Meta:
        model = Artifact
        #fields = '__all__'
        fields = (
                'id',
                #'_file',
                'identifier',
                'description',
                #'custodian',
                'artifact_date',
                'artifact_time',
                'artifact_object_type',
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
    type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    user_action = serializers.SerializerMethodField()

    class Meta:
        model = Artifact
        fields = (
            'id',
            'number',
            'type',
            'status',
            'user_action',
            'artifact_date',
            'identifier',
            'description',
        )

    def get_type(self, artifact_obj):
        pa = PhysicalArtifact.objects.filter(artifact_ptr_id=artifact_obj.id)
        if pa and pa.first().physical_artifact_type and pa.first().physical_artifact_type.artifact_type:
            return pa.first().physical_artifact_type.artifact_type

        da = DocumentArtifact.objects.filter(artifact_ptr_id=artifact_obj.id)
        if da and da.first().document_type and da.first().document_type.artifact_type:
            return da.first().document_type.artifact_type

        return '---'

    def get_status(self, obj):
        return 'not implemented yet'

    def get_user_action(self, obj):
        url_list = []
        view_url = '<a href=/internal/object/' + str(obj.id) + '>View</a>'
        url_list.append(view_url)

        urls = '<br />'.join(url_list)
        return urls


class DocumentArtifactTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentArtifactType
        fields = (
                'id',
                'artifact_type',
                'version',
                'description',
                'date_created',

                )
        read_only_fields = (
                'id',
                )


class PhysicalArtifactTypeSerializer(serializers.ModelSerializer):
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
                )
        read_only_fields = (
                'id',
                )

class PhysicalArtifactDisposalMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentArtifactType
        fields = (
                'id',
                'disposal_method',
                'description',
                'date_created',
                )
        read_only_fields = (
                'id',
                )


class DocumentArtifactStatementSerializer(ArtifactSerializer):
    class Meta:
        model = DocumentArtifact
        fields = (
                'id',
                #'_file',
                'identifier',
                'description',
                'custodian',
                )
        read_only_fields = (
                'id',
                )


class DocumentArtifactSerializer(ArtifactSerializer):
    statement = DocumentArtifactStatementSerializer(read_only=True)
    document_type = DocumentArtifactTypeSerializer(read_only=True)
    person_providing_statement = EmailUserSerializer(read_only=True)
    interviewer = EmailUserSerializer(read_only=True)
    people_attending = EmailUserSerializer(read_only=True, many=True)
    #legal_case = LegalCaseSerializer(read_only=True, many=True)
    legal_case_id_list = serializers.SerializerMethodField()
    offence = OffenceSerializer(read_only=True)
    offender = OffenderSerializer(read_only=True)
    related_items = serializers.SerializerMethodField()

    class Meta:
        model = DocumentArtifact
        #fields = '__all__'
        fields = (
                'id',
                'identifier',
                'description',
                #'custodian',
                'artifact_date',
                'artifact_time',
                'document_type',
                'document_type_id',
                'statement',
                'statement_id',
                'person_providing_statement',
                'interviewer',
                'people_attending',
                'legal_case_id_list',
                'offence',
                'offender',
                'related_items',
                'interviewer_email',
                )
        read_only_fields = (
                'id',
                )

    def get_related_items(self, obj):
        return get_related_items(obj)

    def get_legal_case_id_list(self, obj):
        legal_case_id_list = []
        for legal_case in obj.legal_case.all():
            legal_case_id_list.append(legal_case.id)
        return legal_case_id_list


class SaveDocumentArtifactSerializer(ArtifactSerializer):
    document_type_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    custodian_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    statement_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    person_providing_statement_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    interviewer_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    offence_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    offender_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = DocumentArtifact
        #fields = '__all__'
        fields = (
                'id',
                'identifier',
                'description',
                'custodian_id',
                'statement_id',
                'artifact_date',
                'artifact_time',
                'document_type_id',
                'person_providing_statement_id',
                'interviewer_id',
                'offence_id',
                'offender_id',
                'interviewer_email',
                )
        read_only_fields = (
                'id',
                )


class PhysicalArtifactSerializer(ArtifactSerializer):
    statement = DocumentArtifactSerializer(read_only=True)
    physical_artifact_type = PhysicalArtifactTypeSerializer(read_only=True)
    officer = EmailUserSerializer(read_only=True)
    disposal_method = PhysicalArtifactDisposalMethodSerializer(read_only=True)
    related_items = serializers.SerializerMethodField()
    legal_case_id_list = serializers.SerializerMethodField()

    class Meta:
        model = PhysicalArtifact
        #fields = '__all__'
        fields = (
                'id',
                'identifier',
                'description',
                'artifact_date',
                'artifact_time',
                'statement',
                'physical_artifact_type',
                'used_within_case',
                'sensitive_non_disclosable',
                'disposal_method',
                'description',
                'officer',
                'disposal_date',
                'disposal_details',
                'disposal_method',
                'related_items',
                'legal_case_id_list',
                'officer_email',
                )
        read_only_fields = (
                'id',
                )

    def get_related_items(self, obj):
        return get_related_items(obj)

    def get_legal_case_id_list(self, obj):
        legal_case_id_list = []
        for legal_case in obj.legal_case.all():
            legal_case_id_list.append(legal_case.id)
        return legal_case_id_list


class SavePhysicalArtifactSerializer(ArtifactSerializer):
    physical_artifact_type_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    custodian_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    #legal_case_id = serializers.IntegerField(
     #   required=False, write_only=True, allow_null=True)

    class Meta:
        model = PhysicalArtifact
        #fields = '__all__'
        fields = (
                'id',
                'identifier',
                'description',
                'custodian_id',
                #'legal_case_id',
                'artifact_date',
                'artifact_time',
                'physical_artifact_type_id',
                'officer_email',
                )
        read_only_fields = (
                'id',
                )


class ArtifactUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')

    class Meta:
        model = ArtifactUserAction
        fields = '__all__'


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


#class LegalCaseRunningSheetArtifactsSerializer(serializers.ModelSerializer):
#    document_artifacts = DocumentArtifactSerializer(read_only=True, many=True)
#    physical_artifacts = PhysicalArtifactSerializer(read_only=True, many=True)
#    class Meta:
#        model = LegalCaseRunningSheetArtifacts
#        fields = (
#                'id',
#                'legal_case_id',
#                'document_artifacts',
#                'physical_artifacts',
#                )
#        read_only_fields = (
#                'id',
#                'legal_case_id',
#                )


#class SaveLegalCaseRunningSheetArtifactsSerializer(serializers.ModelSerializer):
#    legal_case_id = serializers.IntegerField(
#        required=False, write_only=True, allow_null=True)
#    class Meta:
#        model = LegalCaseRunningSheetArtifacts
#        fields = (
#                'id',
#                'legal_case_id',
#                'document_artifacts',
#                'physical_artifacts',
#                )
#        read_only_fields = (
#                'id',
#                'legal_case_id',
#                )
