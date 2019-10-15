import traceback

from rest_framework.fields import CharField
#from rest_framework_gis.serializers import GeoFeatureModelSerializer, GeometryField

from ledger.accounts.models import EmailUser, Address
#from wildlifecompliance.components.call_email.serializers import LocationSerializer, LocationSerializerOptimized
from wildlifecompliance.components.legal_case.models import (
    LegalCase,
    LegalCaseUserAction,
    LegalCaseCommsLogEntry,
    )
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
#from wildlifecompliance.components.offence.serializers import OrganisationSerializer
#from django.contrib.auth.models import Permission, ContentType


class LegalCaseSerializer(serializers.ModelSerializer):
    #allocated_group = serializers.SerializerMethodField()
    #all_officers = serializers.SerializerMethodField()
    #user_in_group = serializers.SerializerMethodField()
    #can_user_action = serializers.SerializerMethodField()
    #user_is_assignee = serializers.SerializerMethodField()
    #status = CustomChoiceField(read_only=True)
    ##inspection_team = EmailUserSerializer(many=True, read_only=True)
    #individual_inspected = IndividualSerializer()
    #organisation_inspected = OrganisationSerializer(read_only=True)
    ##inspection_type = InspectionTypeSerializer()
    #related_items = serializers.SerializerMethodField()
    #inspection_report = serializers.SerializerMethodField()
    #data = InspectionFormDataRecordSerializer(many=True)
    #location = LocationSerializer(read_only=True)

    class Meta:
        model = LegalCase
        fields = (
                'id',
                'number',
                'status',
                'title',
                'details',
                'created_date',
                'created_time',
                'assigned_to_id',
                #'allocated_group',
                #'allocated_group_id',
                #'user_in_group',
                #'can_user_action',
                #'user_is_assignee',
                #'related_items',
                'call_email_id',
                #'region_id',
                #'district_id',
                )
        read_only_fields = (
                'id',
                )

    #def get_related_items(self, obj):
    #    return get_related_items(obj)

    #def get_user_in_group(self, obj):
    #    return_val = False
    #    user_id = self.context.get('request', {}).user.id
    #    # inspection team should apply if status is 'open'
    #    if obj.status == 'open' and obj.inspection_team:
    #        for member in obj.inspection_team.all():
    #            if user_id == member.id:
    #                return_val = True
    #    elif obj.allocated_group:
    #       for member in obj.allocated_group.members:
    #           if user_id == member.id:
    #              return_val = True
    #    return return_val

    #def get_can_user_action(self, obj):
    #    return_val = False
    #    user_id = self.context.get('request', {}).user.id

    #    if user_id == obj.assigned_to_id:
    #        return_val = True
    #    if obj.status == 'open' and obj.inspection_team and not obj.assigned_to_id:
    #        for member in obj.inspection_team.all():
    #            if user_id == member.id:
    #                return_val = True
    #    elif obj.allocated_group and not obj.assigned_to_id:
    #       for member in obj.allocated_group.members:
    #           if user_id == member.id:
    #              return_val = True
    #    return return_val

    #def get_user_is_assignee(self, obj):
    #    return_val = False
    #    user_id = self.context.get('request', {}).user.id
    #    if user_id == obj.assigned_to_id:
    #        return_val = True

    #    return return_val


class SaveLegalCaseSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    allocated_group_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    call_email_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = LegalCase
        fields = (
                'id',
                'title',
                'details',
                'created_date',
                'created_time',
                'assigned_to_id',
                'allocated_group_id',
                'call_email_id',
                )
        read_only_fields = (
                'id',
                )

        
class LegalCaseUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')

    class Meta:
        model = LegalCaseUserAction
        fields = '__all__'


class LegalCaseCommsLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = LegalCaseCommsLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self, obj):
        return [[d.name, d._file.url] for d in obj.documents.all()]


class LegalCaseDatatableSerializer(serializers.ModelSerializer):
    user_action = serializers.SerializerMethodField()
    #planned_for = serializers.SerializerMethodField()
    status = CustomChoiceField(read_only=True)
    assigned_to = ComplianceUserDetailsOptimisedSerializer(read_only=True)
    inspection_team_lead = EmailUserSerializer()
    
    class Meta:
        model = LegalCase
        fields = (
                'number',
                'title',
                'status',
                #'planned_for',
                'user_action',
                'assigned_to',
                'assigned_to_id',
                )

    #def get_user_action(self, obj):
    #    user_id = self.context.get('request', {}).user.id
    #    view_url = '<a href=/internal/inspection/' + str(obj.id) + '>View</a>'
    #    process_url = '<a href=/internal/inspection/' + str(obj.id) + '>Process</a>'
    #    returned_url = ''

    #    if obj.status == 'closed':
    #        returned_url = view_url
    #    elif user_id == obj.assigned_to_id:
    #        returned_url = process_url
    #    if obj.status == 'open' and obj.inspection_team and not obj.assigned_to_id:
    #        for member in obj.inspection_team.all():
    #            if user_id == member.id:
    #                returned_url = process_url
    #    elif (obj.allocated_group
    #            and not obj.assigned_to_id):
    #        for member in obj.allocated_group.members:
    #            if user_id == member.id:
    #                returned_url = process_url

    #    if not returned_url:
    #        returned_url = view_url

    #    return returned_url

    #def get_planned_for(self, obj):
    #    if obj.planned_for_date:
    #        if obj.planned_for_time:
    #            return obj.planned_for_date.strftime("%d/%m/%Y") + '  ' + obj.planned_for_time.strftime('%H:%M')
    #        else:
    #            return obj.planned_for_date.strftime("%d/%m/%Y")
    #    else:
    #        return None

#class UpdateAssignedToIdSerializer(serializers.ModelSerializer):
#    assigned_to_id = serializers.IntegerField(
#        required=False, write_only=True, allow_null=True)
#    
#    class Meta:
#        model = Inspection
#        fields = (
#            'assigned_to_id',
#        )

