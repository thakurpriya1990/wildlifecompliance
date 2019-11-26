import traceback

from rest_framework.fields import CharField
#from rest_framework_gis.serializers import GeoFeatureModelSerializer, GeometryField

from ledger.accounts.models import EmailUser, Address
#from wildlifecompliance.components.call_email.serializers import LocationSerializer, LocationSerializerOptimized
from wildlifecompliance.components.legal_case.models import (
    LegalCase,
    LegalCaseUserAction,
    LegalCaseCommsLogEntry,
    LegalCasePriority,
    LegalCaseRunningSheetEntry,
    LegalCasePerson,
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
from reversion.models import Version
#from datetime import datetime, timedelta, date
from django.utils import timezone


class LegalCasePrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalCasePriority
        fields = ('__all__')
        read_only_fields = (
                'id',
                )


class LegalCasePersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalCasePerson
        fields = (
                'id',
                'full_name',
                )
        read_only_fields = (
                'id',
                )


class RunningSheetEntryVersionSerializer(serializers.ModelSerializer):
    #serializable_value = serializers.JSONField()
    entry_fields = serializers.SerializerMethodField()
    date_modified = serializers.SerializerMethodField()
    class Meta:
        model = Version
        #fields = '__all__'
        fields = (
                'id',
                'revision',
                'serialized_data',
                'entry_fields',
                'date_modified',
                )
        read_only_fields = (
                'id',
                'revision',
                'serialized_data',
                'entry_fields',
                'date_modified',
                )

    def get_date_modified(self, obj):
        date_modified = None
        modified_fields = obj.field_dict
        if modified_fields.get('date_modified'):
            date_modified_utc = modified_fields.get('date_modified')
            date_modified = timezone.localtime(date_modified_utc)
        return date_modified

    def get_entry_fields(self, obj):
        modified_fields = obj.field_dict
        user_full_name = ''
        if modified_fields and obj.field_dict.get('user_id'):
            user_obj = EmailUser.objects.get(id=obj.field_dict.get('user_id'))
            user_full_name = user_obj.get_full_name()
        modified_fields['user_full_name'] = user_full_name
        if modified_fields.get('date_modified'):
            date_modified_utc = modified_fields.get('date_modified')
            date_modified = timezone.localtime(date_modified_utc)
            modified_fields['date_mod'] = date_modified.strftime('%d/%m/%Y')
            modified_fields['time_mod'] = date_modified.strftime('%I:%M:%S %p')
        else:
            modified_fields['date_mod'] = ''
            modified_fields['time_mod'] = ''
        return modified_fields


class LegalCaseRunningSheetEntrySerializer(serializers.ModelSerializer):
    #person = LegalCasePersonSerializer(many=True)
    #legal_case_persons = LegalCasePersonSerializer(many=True)
    #action = serializers.SerializerMethodField()
    user_full_name = serializers.SerializerMethodField()
    versions = serializers.SerializerMethodField()
    date_mod = serializers.SerializerMethodField()
    time_mod = serializers.SerializerMethodField()

    class Meta:
        model = LegalCaseRunningSheetEntry
        fields = (
                'id',
                #'person',
                #'legal_case_persons',
                'legal_case_id',
                'number',
                'date_modified',
                'date_mod',
                'time_mod',
                'user_full_name',
                'user_id',
                'description',
                'deleted',
                #'action',
                'versions',
                )
        read_only_fields = (
                'id',
                )

    #def get_action(self, obj):
     #   return ['Delete', 'History']

    def get_date_mod(self, obj):
        date_modified_loc = timezone.localtime(obj.date_modified)
        return date_modified_loc.strftime('%d/%m/%Y')

    def get_time_mod(self, obj):
        date_modified_loc = timezone.localtime(obj.date_modified)
        return date_modified_loc.strftime('%I:%M:%S %p')

    #def get_time_mod(self, obj):
     #   return obj.date_modified.strftime('%I:%M:%S')

    def get_versions(self, obj):
        #pass
        #versions = []
        #entry_version_objs = Version.objects.get_for_object(obj)
        entry_versions = RunningSheetEntryVersionSerializer(
                Version.objects.get_for_object(obj),
                many=True)
        #print(entry_versions.data)
        #if entry_versions:
         #   versions = entry_versions
        return entry_versions.data

    def get_user_full_name(self, obj):
        user_full_name = ''
        if obj.user:
            user_full_name = obj.user.get_full_name()
        return user_full_name


class SaveLegalCaseRunningSheetEntrySerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = LegalCaseRunningSheetEntry
        fields = (
                'id',
                'number',
                #'legal_case_persons',
                'legal_case_id',
                'user_id',
                'description',
                #'date_modified',
                )
        read_only_fields = (
                'id',
                'number',
                'legal_case_id',
                )


class CreateLegalCaseRunningSheetEntrySerializer(serializers.ModelSerializer):
    legal_case_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    user_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = LegalCaseRunningSheetEntry
        fields = (
                #'id',
                #'number',
                #'legal_case_persons',
                'legal_case_id',
                'user_id',
                )

    def create(self, validated_data):
        print("wtf")
        print(validated_data)
        legal_case_id = validated_data.get('legal_case_id')
        user_id = validated_data.get('user_id')
        new_entry = LegalCaseRunningSheetEntry.objects.create_running_sheet_entry(
                legal_case_id=legal_case_id, 
                user_id=user_id)
        #new_entry.save()
        return new_entry


class LegalCaseRunningSheetSerializer(serializers.ModelSerializer):
    running_sheet_entries = LegalCaseRunningSheetEntrySerializer(many=True)

    class Meta:
        model = LegalCase
        fields = (
                'id',
                'running_sheet_entries',
                )
        read_only_fields = (
                'id',
                )


class LegalCaseSerializer(serializers.ModelSerializer):
    running_sheet_entries = LegalCaseRunningSheetEntrySerializer(many=True)
    #running_sheet_entries = serializers.SerializerMethodField()
    allocated_group = serializers.SerializerMethodField()
    #all_officers = serializers.SerializerMethodField()
    user_in_group = serializers.SerializerMethodField()
    can_user_action = serializers.SerializerMethodField()
    user_is_assignee = serializers.SerializerMethodField()
    status = CustomChoiceField(read_only=True)
    related_items = serializers.SerializerMethodField()
    legal_case_priority = LegalCasePrioritySerializer()
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
                'case_created_date',
                'case_created_time',
                'assigned_to_id',
                'allocated_group',
                'allocated_group_id',
                'user_in_group',
                'can_user_action',
                'user_is_assignee',
                'related_items',
                'call_email_id',
                'region_id',
                'district_id',
                'legal_case_priority',
                'legal_case_priority_id',
                'running_sheet_entries',
                )
        read_only_fields = (
                'id',
                )

    def get_related_items(self, obj):
        return get_related_items(obj)

    def get_user_in_group(self, obj):
        return_val = False
        user_id = self.context.get('request', {}).user.id
        if obj.allocated_group:
           for member in obj.allocated_group.members:
               if user_id == member.id:
                  return_val = True
        return return_val

    def get_can_user_action(self, obj):
        return_val = False
        user_id = self.context.get('request', {}).user.id
        if user_id == obj.assigned_to_id:
            return_val = True
        elif obj.allocated_group and not obj.assigned_to_id:
           for member in obj.allocated_group.members:
               if user_id == member.id:
                  return_val = True
        return return_val

    def get_user_is_assignee(self, obj):
        return_val = False
        user_id = self.context.get('request', {}).user.id
        if user_id == obj.assigned_to_id:
            return_val = True

        return return_val

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

    #def get_running_sheet_entries(self, obj):
    #    #entries = 
    #    return 
    #    pass


class SaveLegalCaseSerializer(serializers.ModelSerializer):
    #running_sheet_entries = SaveLegalCaseRunningSheetEntrySerializer(many=True)
    assigned_to_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    allocated_group_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    call_email_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    legal_case_priority_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = LegalCase
        fields = (
                'id',
                'title',
                'details',
                'case_created_date',
                'case_created_time',
                'assigned_to_id',
                'allocated_group_id',
                'call_email_id',
                'legal_case_priority_id',
                #'running_sheet_entries',
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
    created_date = serializers.SerializerMethodField()
    status = CustomChoiceField(read_only=True)
    assigned_to = ComplianceUserDetailsOptimisedSerializer(read_only=True)
    #inspection_team_lead = EmailUserSerializer()
    
    class Meta:
        model = LegalCase
        fields = (
                'number',
                'title',
                'status',
                #'case_created_date',
                'created_date',
                'user_action',
                'assigned_to',
                'assigned_to_id',
                )

    def get_user_action(self, obj):
        user_id = self.context.get('request', {}).user.id
        view_url = '<a href=/internal/legal_case/' + str(obj.id) + '>View</a>'
        process_url = '<a href=/internal/legal_case/' + str(obj.id) + '>Process</a>'
        returned_url = ''

        if obj.status == 'closed':
            returned_url = view_url
        elif user_id == obj.assigned_to_id:
            returned_url = process_url
        elif (obj.allocated_group
                and not obj.assigned_to_id):
            for member in obj.allocated_group.members:
                if user_id == member.id:
                    returned_url = process_url

        if not returned_url:
            returned_url = view_url

        return returned_url

    def get_created_date(self, obj):
        if obj.case_created_date:
            if obj.case_created_time:
                return obj.case_created_date.strftime("%d/%m/%Y") + '  ' + obj.case_created_time.strftime('%H:%M')
            else:
                return obj.case_created_date.strftime("%d/%m/%Y")
        else:
            return None

class UpdateAssignedToIdSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    
    class Meta:
        model = LegalCase
        fields = (
            'assigned_to_id',
        )

