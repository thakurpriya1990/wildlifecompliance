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
        )

from wildlifecompliance.components.offence.serializers import OffenceSerializer, OffenderSerializer
# local EmailUser serializer req?
from wildlifecompliance.components.call_email.serializers import EmailUserSerializer
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
                )
        read_only_fields = (
                'id',
                )


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
    offence = OffenceSerializer(read_only=True)

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
                'person_providing_statement',
                'interviewer',
                'people_attending',
                'offence',
                )
        read_only_fields = (
                'id',
                )


class SaveDocumentArtifactSerializer(ArtifactSerializer):
    document_type_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    custodian_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = DocumentArtifact
        #fields = '__all__'
        fields = (
                'id',
                'identifier',
                'description',
                'custodian_id',
                'artifact_date',
                'artifact_time',
                'document_type_id',
                )
        read_only_fields = (
                'id',
                )


class PhysicalArtifactSerializer(ArtifactSerializer):
    statement = DocumentArtifactSerializer(read_only=True)
    physical_artifact_type = PhysicalArtifactTypeSerializer(read_only=True)
    officer = EmailUserSerializer(read_only=True)
    disposal_method = PhysicalArtifactDisposalMethodSerializer(read_only=True)

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
                )
        read_only_fields = (
                'id',
                )


class SavePhysicalArtifactSerializer(ArtifactSerializer):
    physical_artifact_type_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    custodian_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = PhysicalArtifact
        #fields = '__all__'
        fields = (
                'id',
                'identifier',
                'description',
                'custodian_id',
                'artifact_date',
                'artifact_time',
                'physical_artifact_type_id',
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

