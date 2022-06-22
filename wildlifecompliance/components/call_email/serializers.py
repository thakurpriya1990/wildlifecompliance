import traceback

from rest_framework.fields import CharField
from rest_framework_gis.serializers import GeoFeatureModelSerializer, GeometryField

from django.conf import settings
from ledger.accounts.models import EmailUser, Address
from wildlifecompliance.helpers import is_compliance_management_volunteer
from wildlifecompliance.components.call_email.models import (
    CallEmail,
    Classification,
    CallType,
    WildcareSpeciesType,
    WildcareSpeciesSubType,
    Referrer,
    ReportType,
    ComplianceFormDataRecord,
    CallEmailLogEntry,
    Location,
    CallEmailUserAction,
    MapLayer,
    #ComplianceWorkflowLogEntry,
    )
from wildlifecompliance.components.main.related_item import get_related_items
from wildlifecompliance.components.main.models import Region, District, ComplianceManagementSystemGroup
from wildlifecompliance.components.main.utils import get_region_gis, get_district_gis
from wildlifecompliance.components.main.serializers import CommunicationLogEntrySerializer
from wildlifecompliance.components.users.serializers import (
    ComplianceUserDetailsOptimisedSerializer,
    #CompliancePermissionGroupMembersSerializer
)
from rest_framework import serializers
from django.core.exceptions import ValidationError
from wildlifecompliance.components.main.fields import CustomChoiceField

from wildlifecompliance.components.users.serializers import UserAddressSerializer
from django.contrib.auth.models import Permission, ContentType


class SaveEmailUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(allow_blank=True)  # We need allow_blank=True otherwise blank is not allowed by blank=False setting in the model
    last_name = serializers.CharField(allow_blank=True)  # We need allow_blank=True otherwise blank is not allowed by blank=False setting in the model
    residential_address = UserAddressSerializer(read_only=True)
    residential_address_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    # residential_address = UserAddressSerializer()

    # def create(self, validated_data):
    #     return super(SaveEmailUserSerializer, self).create(validated_data)

    # def update(self, instance, validated_data):
    #     return super(SaveEmailUserSerializer, self).update(instance, validated_data)
    def validate_first_name(self, value):
        # if not value:
        #     raise serializers.ValidationError('First name must not be null.')
        return value

    def validate_last_name(self, value):
        # if not value:
        #     raise serializers.ValidationError('Last name must not be null.')
        return value

    def validate(self, data):
        # return data
        if not data['first_name'] and not data['last_name']:
            raise serializers.ValidationError('Please fill in at least Given Name(s) field or Last Name field.')
        else:
            return data

    class Meta:
        model = EmailUser
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'residential_address',
            'residential_address_id',
            'phone_number',
            'mobile_number',
            'organisation',
            'dob',
        )
        read_only_fields = (
            # 'id',
            # 'residential_address',
        )


class SaveUserAddressSerializer(serializers.ModelSerializer):
    line1 = serializers.CharField(allow_blank=True)  # We need allow_blank=True otherwise blank is not allowed by blank=False setting in the model
    postcode = serializers.CharField(allow_blank=True)  # We need allow_blank=True otherwise blank is not allowed by blank=False setting in the model
    locality = serializers.CharField(allow_blank=True)  # We need allow_blank=True otherwise blank is not allowed by blank=False setting in the model
    country = serializers.CharField(allow_blank=True)  # We need allow_blank=True otherwise blank is not allowed by blank=False setting in the model
    user_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = Address
        fields = (
            'id',
            'line1',
            'line2',
            'line3',
            'locality',
            'state',
            'country',
            'postcode',
            'user_id',
        )


class EmailUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    residential_address = UserAddressSerializer()

    class Meta:
        model = EmailUser
        fields = (
            'id',
            'email',
            'full_name',
            'first_name',
            'last_name',
            'residential_address',
            'phone_number',
            'mobile_number',
            'organisation',
            'dob',
        )

    def get_full_name(self, obj):
        return obj.get_full_name()


class ComplianceFormDataRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceFormDataRecord
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


class ClassificationSerializer(serializers.ModelSerializer):
    classification_display = serializers.SerializerMethodField()

    class Meta:
        model = Classification
        fields = (
            'id',
            'name',
            'classification_display',
        )
        read_only_fields = ('id', 'name', )

    def get_classification_display(self, obj):
        display_name = ''
        for choice in Classification.NAME_CHOICES:
            if obj.name == choice[0]:
                display_name = choice[1]
        return display_name

class CallTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallType
        fields = (
            'id',
            'name',
        )
        read_only_fields = ('id', 'name', )
class WildcareSpeciesTypeSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = WildcareSpeciesType
        fields = (
            'id',
            'call_type_id',
            'species_name',
        )
        read_only_fields = ('id', 'species_name', )

class WildcareSpeciesSubTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = WildcareSpeciesSubType
        fields = (
            'id',
            'wildcare_species_type_id',
            'species_sub_name',
        )
        read_only_fields = ('id', 'species_sub_name', )


class ReferrerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Referrer
        fields = (
            'id',
            'name',
        )
        read_only_fields = ('id', 'name', )


class LocationSerializerOptimized(GeoFeatureModelSerializer):
    class Meta:
        model = Location
        geo_field = 'wkb_geometry'

        fields = (
            'id',
            'wkb_geometry',
            'call_email_id',
        )


class LocationSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Location
        geo_field = 'wkb_geometry'
        
        fields = (
            'id',
            'street',
            'town_suburb',
            'state',
            'postcode',
            'country',
            'wkb_geometry',
            'details',
            'ben_number',
            #'call_email_id',
        )
        

class ReportTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportType
        fields = (
            'id', 
            'report_type',
            'version',
            'advice_url',
        )
        read_only_fields = (
            'id', 
            'report_type',
            'version',
            'advice_url',
             )


class SaveCallEmailSerializer(serializers.ModelSerializer):
    status = CustomChoiceField(read_only=True)
    entangled = serializers.MultipleChoiceField(choices=CallEmail.ENTANGLED_CHOICES, allow_null=True, allow_blank=True, required=False)
    gender = serializers.MultipleChoiceField(choices=CallEmail.GENDER_CHOICES, allow_null=True, allow_blank=True, required=False)
    baby_kangaroo = serializers.MultipleChoiceField(choices=CallEmail.BABY_KANGAROO_CHOICES, allow_null=True, allow_blank=True, required=False)
    age = serializers.MultipleChoiceField(choices=CallEmail.AGE_CHOICES, allow_null=True, allow_blank=True, required=False)
    classification = ClassificationSerializer(read_only=True)
    call_type = CallTypeSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    report_type = ReportTypeSerializer(read_only=True)
    referrer = ReferrerSerializer(read_only=True)
    email_user = EmailUserSerializer(read_only=True)
    classification_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    call_type_id= serializers.IntegerField(
        write_only=True, required=False, allow_null=True)
    wildcare_species_type_id= serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    wildcare_species_sub_type_id= serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    report_type_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    location_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    email_user_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    #region_id = serializers.IntegerField(
    #    required=False, write_only=True, allow_null=True)
    #district_id = serializers.IntegerField(
    #    required=False, write_only=True, allow_null=True)
    assigned_to_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    allocated_group_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    volunteer_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = CallEmail
        fields = (
            'id',
            'number',
            'status',
            'entangled',
            'entangled_other',
            'gender',
            'baby_kangaroo',
            'age',
            'assigned_to_id',
            # 'allocated_to',
            'allocated_group_id',
            # 'status_display',
            'schema',
            'location',
            'classification',
            'call_type',
            'report_type',
            'location_id',
            'classification_id',
            'call_type_id',
            'wildcare_species_type_id',
            'wildcare_species_sub_type_id',
            'species_name',
            'dead',
            'euthanise',
            'number_of_animals',
            'brief_nature_of_call',
            'report_type_id',
            'caller',
            'referrer',
            'caller_phone_number',
            'anonymous_call',
            'caller_wishes_to_remain_anonymous',
            'occurrence_from_to',
            'occurrence_date_from',
            'occurrence_time_start',
            'occurrence_date_to',
            'occurrence_time_end',
            'date_of_call',
            'time_of_call',
            'advice_given',
            'advice_details',
            'email_user',
            'email_user_id',
            #'region_id',
            #'district_id',
            'volunteer_id',
        )
        read_only_fields = (
            'id', 
            'number', 
            'location',
            'classification',
            'report_type',
            'referrer',
            'email_user',
            )

    def validate(self, data):
        custom_errors = {}
        if not self.context.get('draft'):
            if not data.get("call_type_id"):
                custom_errors["Call Type"] = "You must choose call type"
            if not data.get("brief_nature_of_call"):
                custom_errors["Brief Nature of Call"] = "You must fill in brief nature of call"

            if custom_errors.keys():
                raise serializers.ValidationError(custom_errors)

        return data


class ReportTypeSchemaSerializer(serializers.ModelSerializer):
    report_type_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    adviceurl = serializers.SerializerMethodField()

    class Meta:
        model = CallEmail
        fields = (
            'id',
            'schema',
            'report_type_id',
            'adviceurl',
        )
        read_only_fields = (
            'id',
            )

    def get_adviceurl(self, obj):
        print("obj.report_type")
        print(obj.report_type)
        print(type(obj))
        advice_url = ""
        #if obj.report_type and obj.report_type.advice_url:
         #   advice_url = obj.report_type.advice_url
        if obj.report_type:
            advice_url = obj.advice_url
        return advice_url


class CallEmailOptimisedSerializer(serializers.ModelSerializer):
    classification = ClassificationSerializer(read_only=True)
    location = LocationSerializerOptimized()
    report_type = ReportTypeSerializer(read_only=True)

    class Meta:
        model = CallEmail
        fields = (
            'id',
            'location',
            'classification',
            'number',
            'report_type',
        )
        read_only_fields = ('id', )


#class CallEmailAllocatedGroupSerializer(serializers.ModelSerializer):
#    #allocated_group = CompliancePermissionGroupMembersSerializer()
#    allocated_group = ComplianceSystemGroupMembersSerializer()
#
#    class Meta:
#        model = CallEmail
#        fields = (
#            'allocated_group',
#        )


class CallEmailSerializer(serializers.ModelSerializer):
    status = CustomChoiceField(read_only=True)
    entangled = serializers.MultipleChoiceField(choices=CallEmail.ENTANGLED_CHOICES, read_only=True)
    gender = serializers.MultipleChoiceField(choices=CallEmail.GENDER_CHOICES, read_only=True)
    baby_kangaroo = serializers.MultipleChoiceField(choices=CallEmail.BABY_KANGAROO_CHOICES, read_only=True)
    age = serializers.MultipleChoiceField(choices=CallEmail.AGE_CHOICES, read_only=True)
    classification = ClassificationSerializer(read_only=True)
    call_type= CallTypeSerializer(read_only=True)
    lodgement_date = serializers.CharField(source='lodged_on')
    report_type = ReportTypeSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    referrer = ReferrerSerializer(many=True)
    data = ComplianceFormDataRecordSerializer(many=True)
    email_user = EmailUserSerializer(read_only=True)
    # allocated_group = CallEmailAllocatedGroupSerializer(many=True)
    # allocated_group = CompliancePermissionGroupMembersSerializer()
    allocated_group = serializers.SerializerMethodField()
    user_in_group = serializers.SerializerMethodField()
    related_items = serializers.SerializerMethodField()
    selected_referrers = serializers.SerializerMethodField()
    user_is_assignee = serializers.SerializerMethodField()
    can_user_action = serializers.SerializerMethodField()
    can_user_edit_form = serializers.SerializerMethodField()
    can_user_search_person = serializers.SerializerMethodField()
    user_is_volunteer = serializers.SerializerMethodField()
    volunteer_list = serializers.SerializerMethodField()
    current_user_id = serializers.SerializerMethodField()
    region_gis = serializers.SerializerMethodField()
    district_gis = serializers.SerializerMethodField()

    class Meta:
        model = CallEmail
        fields = (
            'id',
            'status',
            'entangled',
            'entangled_other',
            'gender',
            'baby_kangaroo',
            'age',
            # 'status_display',
            'assigned_to_id',
            'allocated_group',
            'allocated_group_id',
            'location',
            'location_id',
            'classification',
            'classification_id',
            'schema',
            'lodgement_date',
            'number',
            'caller',
            'call_type',
            'call_type_id',
            'wildcare_species_type_id',
            'wildcare_species_sub_type_id',
            'species_name',
            'dead',
            'euthanise',
            'number_of_animals',
            'brief_nature_of_call',
            'report_type',
            'report_type_id',
            'data',
            'caller_phone_number',
            'anonymous_call',
            'caller_wishes_to_remain_anonymous',
            'occurrence_from_to',
            'occurrence_date_from',
            'occurrence_time_start',
            'occurrence_date_to',
            'occurrence_time_end',
            'date_of_call',
            'time_of_call',
            'referrer',
            'advice_given',
            'advice_details',
            'email_user',
            #'region_id',
            #'district_id',
            'user_in_group',
            'related_items',
            'selected_referrers',
            'user_is_assignee',
            'can_user_action',
            'can_user_edit_form',
            'can_user_search_person',
            'user_is_volunteer',
            'volunteer_list',
            'volunteer_id',
            'current_user_id',
            'region_gis',
            'district_gis',
        )
        read_only_fields = (
            'id', 
            )

    def get_region_gis(self, obj):
        try:
            res = get_region_gis(obj.location.wkb_geometry)
            region_list = Region.objects.filter(cddp_name__iexact=res.strip())
            if region_list:
                return region_list[0].name
        except Exception as e:
            return ''
        return ''

    def get_district_gis(self, obj):
        try:
            res = get_district_gis(obj.location.wkb_geometry)
            district_list = District.objects.filter(cddp_name__iexact=res.strip())
            if district_list:
                return district_list[0].name
        except Exception as e:
            return ''
        return ''

    def get_current_user_id(self, obj):
        return self.context.get('request', {}).user.id

    def get_user_in_group(self, obj):
        user_id = self.context.get('request', {}).user.id

        if obj.allocated_group:
           for member in obj.allocated_group.get_members():
               if user_id == member.id:
                  return True
        
        return False

    def get_can_user_action(self, obj):
        user_id = self.context.get('request', {}).user.id

        if user_id == obj.assigned_to_id:
            return True
        elif obj.allocated_group and not obj.assigned_to_id:
           for member in obj.allocated_group.get_members():
               if user_id == member.id:
                  return True
        
        return False

    def get_allocated_group(self, obj):
        allocated_group = [{
            'email': '',
            'first_name': '',
            'full_name': '',
            'id': None,
            'last_name': '',
            'title': '',
            }]
        returned_allocated_group = ComplianceUserDetailsOptimisedSerializer(obj.allocated_group.get_members(), many=True).data
        for member in returned_allocated_group:
            allocated_group.append(member)

        return allocated_group

    def get_related_items(self, obj):
        return get_related_items(obj)

    def get_selected_referrers(self, obj):
        referrers_selected  = []
        #returned_referrers = ReferrerSerializer(obj.referrer)
        #print(returned_referrers.data)
        for referrer in obj.referrer.all():
            referrers_selected.append(str(referrer.id))

        return referrers_selected
    
    def get_user_is_assignee(self, obj):
        user_id = self.context.get('request', {}).user.id
        if user_id == obj.assigned_to_id:
            return True

        return False

    def get_can_user_edit_form(self, obj):
        user_id = self.context.get('request', {}).user.id

        if obj.status == 'draft':
            if user_id == obj.assigned_to_id:
                return True
            elif obj.allocated_group and not obj.assigned_to_id:
               for member in obj.allocated_group.get_members():
                   if user_id == member.id:
                      return True
        
        return False

    def get_can_user_search_person(self, obj):
        user_id = self.context.get('request', {}).user.id

        if obj.status == 'open':
            if user_id == obj.assigned_to_id:
                return True
            elif obj.allocated_group and not obj.assigned_to_id:
               for member in obj.allocated_group.get_members():
                   if user_id == member.id:
                      return True
        return False

    def get_user_is_volunteer(self, obj):
        return is_compliance_management_volunteer(self.context.get('request'))

    def get_volunteer_list(self, obj):
        volunteers = ComplianceManagementSystemGroup.objects.get(name=settings.GROUP_VOLUNTEER).get_members()
        volunteer_list = [{
            'email': '',
            'first_name': '',
            'full_name': '',
            'id': None,
            'last_name': '',
            'title': '',
            }]
        serialized_volunteers = ComplianceUserDetailsOptimisedSerializer(volunteers, many=True).data
        for member in serialized_volunteers:
            volunteer_list.append(member)

        return volunteer_list


class CallEmailDatatableSerializer(serializers.ModelSerializer):
    status = CustomChoiceField(read_only=True)
    #classification = CustomChoiceField(read_only=True)
    classification = ClassificationSerializer(read_only=True)
    #lodgement_date = serializers.CharField(source='lodged_on')
    user_is_assignee = serializers.SerializerMethodField()
    assigned_to = ComplianceUserDetailsOptimisedSerializer(read_only=True)
    user_action = serializers.SerializerMethodField()
    user_is_volunteer = serializers.SerializerMethodField()
    species_sub_type = serializers.SerializerMethodField()

    class Meta:
        model = CallEmail
        fields = (
            'id',
            'status',
            'user_is_assignee',
            'classification',
            'classification_id',
            'lodged_on',
            'number',
            'caller',
            'assigned_to',
            'assigned_to_id',
            'user_action',
            'user_is_volunteer',
            'volunteer_id',
            'species_sub_type',
        )
        read_only_fields = (
            'id', 
            )

    def get_species_sub_type(self, obj):
        return obj.wildcare_species_sub_type.species_sub_name if obj.wildcare_species_sub_type else ''

    def get_user_is_assignee(self, obj):
        user_id = self.context.get('request', {}).user.id
        if user_id == obj.assigned_to_id:
            return True

    def get_user_action(self, obj):
        user_id = self.context.get('request', {}).user.id
        view_url = '<a href=/internal/call_email/' + str(obj.id) + '>View</a>'
        process_url = '<a href=/internal/call_email/' + str(obj.id) + '>Process</a>'
        returned_url = ''
        #return process_url

        if obj.status == 'closed':
            returned_url = view_url
        elif user_id == obj.assigned_to_id:
            returned_url = process_url
        elif (obj.allocated_group
                and not obj.assigned_to_id):
            for member in obj.allocated_group.get_members():
                if user_id == member.id:
                    returned_url = process_url

        if not returned_url:
            returned_url = view_url

        return returned_url

    def get_user_is_volunteer(self, obj):
        return is_compliance_management_volunteer(self.context.get('request'))


class UpdateAssignedToIdSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    
    class Meta:
        model = CallEmail
        fields = (
            'assigned_to_id',
        )


class CreateCallEmailSerializer(serializers.ModelSerializer):
    # status_display = serializers.CharField(source='get_status_display')
    status = CustomChoiceField(read_only=True)
    # customer_status = CustomChoiceField(read_only=True)
    entangled = serializers.MultipleChoiceField(choices=CallEmail.ENTANGLED_CHOICES, allow_null=True, allow_blank=True, required=False)
    gender = serializers.MultipleChoiceField(choices=CallEmail.GENDER_CHOICES, allow_null=True, allow_blank=True, required=False)
    baby_kangaroo = serializers.MultipleChoiceField(choices=CallEmail.BABY_KANGAROO_CHOICES, allow_null=True, allow_blank=True, required=False)
    age = serializers.MultipleChoiceField(choices=CallEmail.AGE_CHOICES, allow_null=True, allow_blank=True, required=False)
    lodgement_date = serializers.CharField(
        source='lodged_on')
    classification_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    report_type_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    call_type_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    wildcare_species_type_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    wildcare_species_sub_type_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    location_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)        
    #region_id = serializers.IntegerField(
    #    required=False, write_only=True, allow_null=True)
    #district_id = serializers.IntegerField(
    #    required=False, write_only=True, allow_null=True)
    assigned_to_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    #allocated_group_id = serializers.IntegerField(
     #   required=False, write_only=True, allow_null=True)

    class Meta:
        model = CallEmail
        fields = (
            'id',
            'status',
            'entangled',
            'entangled_other',
            'gender',
            'baby_kangaroo',
            'age',
            'assigned_to_id',
            #'allocated_group_id',
            'location_id',
            'classification_id',
            'call_type_id',
            'wildcare_species_type_id',
            'wildcare_species_sub_type_id',
            'species_name',
            'brief_nature_of_call',
            'lodgement_date',
            'caller',
            'report_type_id',
            'caller_phone_number',
            'anonymous_call',
            'caller_wishes_to_remain_anonymous',
            'occurrence_from_to',
            'occurrence_date_from',
            'occurrence_time_start',
            'occurrence_date_to',
            'occurrence_time_end',
            'advice_given',
            'advice_details',
            #'region_id',
            #'district_id',
            'dead',
            'euthanise',
            'number_of_animals'
        )
        read_only_fields = (
            'id', 
            )


class CallEmailUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')

    class Meta:
        model = CallEmailUserAction
        fields = '__all__'


class CallEmailLogEntrySerializer(CommunicationLogEntrySerializer):
        documents = serializers.SerializerMethodField()

        class Meta:
            model = CallEmailLogEntry
            fields = '__all__'
            #read_only_fields = (
             #                   'customer',
              #                  )

        def get_documents(self, obj):
            return [[d.name, d._file.url] for d in obj.documents.all()]


class MapLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapLayer
        fields = (
            'display_name',
            'layer_name',
        )

