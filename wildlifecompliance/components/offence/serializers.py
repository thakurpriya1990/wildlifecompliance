from django.db.models import Q
from rest_framework import serializers
from wildlifecompliance.components.organisations.models import Organisation
from wildlifecompliance.components.call_email.serializers import LocationSerializer, EmailUserSerializer, \
    LocationSerializerOptimized
from wildlifecompliance.components.main.fields import CustomChoiceField
from wildlifecompliance.components.main.related_item import get_related_items
from wildlifecompliance.components.offence.models import Offence, SectionRegulation, Offender, AllegedOffence
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, AllegedCommittedOffence
from wildlifecompliance.components.users.serializers import CompliancePermissionGroupMembersSerializer


class OrganisationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organisation
        fields = (
            'id',
            'organisation_id',
            'abn',
            'name',
        )
        read_only_fields = ()


class SectionRegulationSerializer(serializers.ModelSerializer):

    class Meta:
        model = SectionRegulation
        fields = (
            'id',
            'act',
            'name',
            'offence_text',
        )
        read_only_fields = ()


class OffenderSerializer(serializers.ModelSerializer):
    person = EmailUserSerializer(read_only=True,)
    organisation = OrganisationSerializer(read_only=True,)
    number_linked_sanction_outcomes_total = serializers.SerializerMethodField(read_only=True)
    number_linked_sanction_outcomes_active = serializers.SerializerMethodField(read_only=True)
    can_user_action = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Offender
        fields = (
            'id',
            'person',
            'organisation',
            'removed',
            'reason_for_removal',
            'number_linked_sanction_outcomes_total',
            'number_linked_sanction_outcomes_active',
            'can_user_action',
        )

    def get_number_linked_sanction_outcomes_total(self, obj):
        return SanctionOutcome.objects.filter(offender=obj).count()

    def get_number_linked_sanction_outcomes_active(self, obj):
        return SanctionOutcome.objects_active.filter(offender=obj).count()

    def get_can_user_action(self, obj):
        # if obj.removed:
        #     return False
        return True


class UpdateAssignedToIdSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = Offence
        fields = (
            'assigned_to_id',
        )


class OffenceDatatableSerializer(serializers.ModelSerializer):
    status = CustomChoiceField(read_only=True)
    user_action = serializers.SerializerMethodField()
    alleged_offences = SectionRegulationSerializer(read_only=True, many=True)
    offenders = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Offence
        fields = (
            'id',
            'identifier',
            'status',
            'lodgement_number',
            # 'region',
            # 'district',
            # 'offence',
            'offenders',
            'alleged_offences',
            # 'issued_on_paper',
            # 'paper_id',
            'occurrence_from_to',
            'occurrence_date_from',
            'occurrence_time_from',
            'occurrence_date_to',
            'occurrence_time_to',
            'details',
            'user_action',
        )
        read_only_fields = ()

    def get_user_action(self, obj):
        user_id = self.context.get('request', {}).user.id
        view_url = '<a href=/internal/offence/' + str(obj.id) + '>View</a>'
        process_url = '<a href=/internal/offence/' + str(obj.id) + '>Process</a>'
        returned_url = ''

        if obj.status == Offence.STATUS_CLOSED:
            returned_url = view_url
        elif user_id == obj.assigned_to_id:
            returned_url = process_url
        elif (obj.allocated_group and not obj.assigned_to_id):
            if user_id in [member.id for member in obj.allocated_group.members]:
                returned_url = process_url

        if not returned_url:
            returned_url = view_url

        return returned_url

    def get_offenders(self, obj):
        offenders = Offender.active_offenders.filter(offence__exact=obj)
        return [ OffenderSerializer(offender).data for offender in offenders ]


# class AllegedOffenceSerializer(serializers.ModelSerializer):
#     section_regulation = SectionRegulationSerializer(read_only=True)
#     removed_by_id = serializers.IntegerField(read_only=True)
#     number_linked_sanction_outcomes = serializers.SerializerMethodField(read_only=True)
#     number_linked_sanction_outcomes_active = serializers.SerializerMethodField(read_only=True)
#
#     class Meta:
#         model = AllegedOffence
#         fields = (
#             'id',
#             'section_regulation',
#             'removed',
#             'removed_by_id',
#             'reason_for_removal',
#             'number_linked_sanction_outcomes',
#             'number_linked_sanction_outcomes_active',
#         )
#
#     def get_number_linked_sanction_outcomes(self, alleged_offence):
#         temp =  AllegedCommittedOffence.objects.filter(alleged_offence=alleged_offence)
#         return temp.count()
#
#     def get_number_linked_sanction_outcomes_active(self, alleged_offence):
#         return AllegedCommittedOffence.objects_active.filter(alleged_offence=alleged_offence).filter(sanction_outcome__in=SanctionOutcome.objects_active.all()).count()


class OffenceSerializer(serializers.ModelSerializer):
    status = CustomChoiceField(read_only=True)
    location = LocationSerializer(read_only=True)
    alleged_offences = serializers.SerializerMethodField(read_only=True)
    # alleged_offences = AllegedOffenceSerializer(read_only=True, many=True)
    offenders = serializers.SerializerMethodField(read_only=True)
    allocated_group = serializers.SerializerMethodField()
    user_in_group = serializers.SerializerMethodField()
    can_user_action = serializers.SerializerMethodField()
    user_is_assignee = serializers.SerializerMethodField()
    related_items = serializers.SerializerMethodField()
    in_editable_status = serializers.SerializerMethodField()

    class Meta:
        model = Offence
        fields = (
            'id',
            'identifier',
            'lodgement_number',
            'status',
            'call_email',
            'region_id',
            'district_id',
            'assigned_to_id',
            'allocated_group',
            'allocated_group_id',
            'user_in_group',
            'can_user_action',
            'user_is_assignee',
            'related_items',
            'district',
            'inspection_id',
            'occurrence_from_to',
            'occurrence_date_from',
            'occurrence_time_from',
            'occurrence_date_to',
            'occurrence_time_to',
            'details',
            'location',
            'alleged_offences',
            'offenders',
            'in_editable_status',
        )
        read_only_fields = (

        )

    def get_in_editable_status(self, obj):
        return obj.status in (Offence.STATUS_DRAFT, Offence.STATUS_OPEN)

    def get_alleged_offences(self, obj):
        alleged_offences = AllegedOffence.objects.filter(offence=obj)
        ret_list = []
        for alleged_offence in alleged_offences:
            ret_obj = {}

            section_regulation_serializer = SectionRegulationSerializer(alleged_offence.section_regulation)
            ret_obj['section_regulation'] = section_regulation_serializer.data
            ret_obj['id'] = alleged_offence.id
            ret_obj['removed'] = alleged_offence.removed
            ret_obj['removed_by_id'] = alleged_offence.removed_by.id if alleged_offence.removed_by else None
            ret_obj['reason_for_removal'] = alleged_offence.reason_for_removal

            # number_linked_to_sanction_outcomes
            ret_obj['number_linked_sanction_outcomes_total'] = AllegedCommittedOffence.objects.filter(
                Q(alleged_offence=alleged_offence)
            ).count()

            # number_linked_to_sanction_outcomes_active
            ret_obj['number_linked_sanction_outcomes_active'] = AllegedCommittedOffence.objects_active.filter(
                Q(alleged_offence=alleged_offence) &
                Q(sanction_outcome__in=SanctionOutcome.objects_active.all())
            ).count()

            ret_list.append(ret_obj)
        return ret_list

    def get_offenders(self, obj):
        offenders = Offender.objects.filter(offence__exact=obj)
        offenders_list =  [ OffenderSerializer(offender).data for offender in offenders ]
        return offenders_list

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

    def get_user_in_group(self, obj):
        user_id = self.context.get('request', {}).user.id

        if obj.allocated_group:
            for member in obj.allocated_group.members:
                if user_id == member.id:
                    return True
        return False

    def get_can_user_action(self, obj):
        # User can have action buttons
        # when user is assigned to the target object or
        # when user is a member of the allocated group and no one is assigned to the target object
        user_id = self.context.get('request', {}).user.id
        if user_id == obj.assigned_to_id:
            return True
        elif obj.allocated_group and not obj.assigned_to_id:
            if user_id in [member.id for member in obj.allocated_group.members]:
                return True

        return False

    def get_user_is_assignee(self, obj):
        user_id = self.context.get('request', {}).user.id
        if user_id == obj.assigned_to_id:
            return True

        return False

    def get_related_items(self, obj):
        return get_related_items(obj)


class UpdateAllegedOffenceAttributeSerializer(serializers.ModelSerializer):
    removed_by_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = AllegedOffence
        fields = (
            'removed',
            'reason_for_removal',
            'removed_by_id',
        )

    def validate(self, data):
        if data['removed']:
            if not data['reason_for_removal']:
                raise serializers.ValidationError('To remove a record, you need a reason to remove.')
            if not data['removed_by_id']:
                raise serializers.ValidationError('To remove a record, you need a person to remove.')
        return data


class UpdateOffenderAttributeSerializer(serializers.ModelSerializer):
    removed_by_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Offender
        fields = (
            'removed',
            'reason_for_removal',
            'removed_by_id',
        )

    def validate(self, data):
        if data['removed']:
            if not data['reason_for_removal']:
                raise serializers.ValidationError('To remove a record, you need a reason to remove.')
            if not data['removed_by_id']:
                raise serializers.ValidationError('To remove a record, you need a person to remove.')
        return data


class OffenceOptimisedSerializer(serializers.ModelSerializer):
    location = LocationSerializerOptimized()

    class Meta:
        model = Offence
        fields = (
            'id',
            'status',
            'location',
            'lodgement_number',
        )
        read_only_fields = ('id', )


class SaveOffenceSerializer(serializers.ModelSerializer):
    location_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    call_email_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    inspection_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    region_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    district_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    allocated_group_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = Offence
        fields = (
            'id',
            'identifier',
            'status',
            'location_id',
            'call_email_id',
            'inspection_id',
            'occurrence_from_to',
            'occurrence_date_from',
            'occurrence_time_from',
            'occurrence_date_to',
            'occurrence_time_to',
            'details',
            'region_id',
            'district_id',
            'allocated_group_id',
        )
        read_only_fields = ()

    def validate(self, data):
        # Add object level validation here if needed
        return data


class SaveOffenderSerializer(serializers.ModelSerializer):
    offence_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    person_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    organisation_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = Offender
        fields = (
            'id',
            'offence_id',
            'person_id',
            'organisation_id',
        )
        read_only_fields = ()
