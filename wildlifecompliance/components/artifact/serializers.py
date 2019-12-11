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
#from wildlifecompliance.components.offence.serializers import OrganisationSerializer
#from django.contrib.auth.models import Permission, ContentType
from reversion.models import Version
#from datetime import datetime, timedelta, date
from django.utils import timezone


#class LegalCasePrioritySerializer(serializers.ModelSerializer):
#    class Meta:
#        model = LegalCasePriority
#        fields = ('__all__')
#        read_only_fields = (
#                'id',
#                )

class ArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artifact
        #fields = '__all__'
        fields = (
                'id',
                '_file',
                'identifier',
                'description',
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


class DocumentArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentArtifact
        fields = '__all__'


class PhysicalArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhysicalArtifact
        fields = '__all__'


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

