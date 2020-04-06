import traceback

from rest_framework.fields import CharField

from ledger.accounts.models import EmailUser, Address
from wildlifecompliance.components.legal_case.models import (
    LegalCase,
    LegalCaseUserAction,
    LegalCaseCommsLogEntry,
    LegalCasePriority,
    LegalCaseRunningSheetEntry,
    LegalCasePerson,
    CourtProceedingsJournalEntry,
    CourtProceedings,
    BriefOfEvidence,
    ProsecutionBrief,
    CourtDate)
from wildlifecompliance.components.call_email.serializers import EmailUserSerializer
from wildlifecompliance.components.main.related_item import get_related_items
from wildlifecompliance.components.main.serializers import CommunicationLogEntrySerializer
from wildlifecompliance.components.users.serializers import (
    ComplianceUserDetailsOptimisedSerializer,
    CompliancePermissionGroupMembersSerializer
)
from rest_framework import serializers
from django.core.exceptions import ValidationError
from wildlifecompliance.components.main.fields import CustomChoiceField

from wildlifecompliance.components.offence.serializers import OffenceSerializer
from wildlifecompliance.components.users.serializers import (
    ComplianceUserDetailsOptimisedSerializer,
    CompliancePermissionGroupMembersSerializer,
    UserAddressSerializer,
)
from wildlifecompliance.components.artifact.serializers import (
        DocumentArtifactStatementSerializer,
        PhysicalArtifactSerializer,
        BriefOfEvidenceRecordOfInterviewSerializer,
        BriefOfEvidenceOtherStatementsSerializer,
        BriefOfEvidenceDocumentArtifactsSerializer,
        BriefOfEvidencePhysicalArtifactsSerializer,
        ProsecutionBriefRecordOfInterviewSerializer,
        ProsecutionBriefOtherStatementsSerializer,
        ProsecutionBriefDocumentArtifactsSerializer,
        ProsecutionBriefPhysicalArtifactsSerializer,
        )
from reversion.models import Version
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
                'legal_case_id',
                )
        read_only_fields = (
                'id',
                'legal_case_id',
                )


class CreateLegalCasePersonSerializer(serializers.ModelSerializer):
    legal_case_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    class Meta:
        model = LegalCasePerson
        fields = (
                'id',
                'legal_case_id',
                )
        read_only_fields = (
                'id',
                )


class VersionSerializer(serializers.ModelSerializer):
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


class JournalEntryHistorySerializer(serializers.ModelSerializer):
    versions = serializers.SerializerMethodField()
    class Meta:
        model = CourtProceedingsJournalEntry
        fields = (
                'id',
                'versions',
                )
    def get_versions(self, obj):
        entry_versions = VersionSerializer(
                Version.objects.get_for_object(obj),
                many=True)
        return entry_versions.data


class CourtProceedingsJournalEntrySerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()
    date_mod = serializers.SerializerMethodField()
    time_mod = serializers.SerializerMethodField()

    class Meta:
        model = CourtProceedingsJournalEntry
        fields = (
                'id',
                'court_proceedings_id',
                'number',
                'date_modified',
                'date_mod',
                'time_mod',
                'user_full_name',
                'user_id',
                'description',
                'deleted',
                )
        read_only_fields = (
                'id',
                )

    def get_date_mod(self, obj):
        date_modified_loc = timezone.localtime(obj.date_modified)
        return date_modified_loc.strftime('%d/%m/%Y')

    def get_time_mod(self, obj):
        date_modified_loc = timezone.localtime(obj.date_modified)
        return date_modified_loc.strftime('%I:%M:%S %p')

    def get_user_full_name(self, obj):
        user_full_name = ''
        if obj.user:
            user_full_name = obj.user.get_full_name()
        return user_full_name


class SaveCourtDateEntrySerializer(serializers.ModelSerializer):
    court_proceedings_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = CourtDate
        fields = (
            'court_proceedings_id',
            'court_datetime',
            'comments',
        )


class SaveCourtProceedingsJournalEntrySerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = CourtProceedingsJournalEntry
        fields = (
            'id',
            'number',
            'court_proceedings_id',
            'user_id',
            'description',
        )
        read_only_fields = (
            'id',
            'number',
            'court_proceedings_id',
        )


class DeleteReinstateCourtProceedingsJournalEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = CourtProceedingsJournalEntry
        fields = (
                'id',
                'number',
                'court_proceedings_id',
                'deleted',
                )
        read_only_fields = (
                'id',
                'number',
                'court_proceedings_id',
                )


class CreateCourtProceedingsJournalEntrySerializer(serializers.ModelSerializer):
    court_proceedings_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    user_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)

    class Meta:
        model = CourtProceedingsJournalEntry
        fields = (
                'court_proceedings_id',
                'user_id',
                )

    def create(self, validated_data):
        court_proceedings_id = validated_data.get('court_proceedings_id')
        user_id = validated_data.get('user_id')
        new_entry = CourtProceedingsJournalEntry.objects.create_journal_entry(
                court_proceedings_id=court_proceedings_id,
                user_id=user_id)
        return new_entry


class CourtProceedingsCourtDateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CourtDate
        fields = (
            'id',
            'court_datetime',
            'comments',
        )


class CourtProceedingsJournalSerializer(serializers.ModelSerializer):
    journal_entries = CourtProceedingsJournalEntrySerializer(many=True, read_only=True)
    court_dates = CourtProceedingsCourtDateSerializer(many=True, read_only=True)

    class Meta:
        model = CourtProceedings
        fields = (
                'id',
                'court_outcome_details',
                'journal_entries',
                'court_dates',
                )
        read_only_fields = (
                'id',
        )

    def validate(self, attrs):
        return attrs

class RunningSheetEntryHistorySerializer(serializers.ModelSerializer):
    versions = serializers.SerializerMethodField()
    class Meta:
        model = LegalCaseRunningSheetEntry
        fields = (
                'id',
                'versions',
                )
    def get_versions(self, obj):
        entry_versions = VersionSerializer(
                Version.objects.get_for_object(obj),
                many=True)
        return entry_versions.data


class LegalCaseRunningSheetEntrySerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()
    date_mod = serializers.SerializerMethodField()
    time_mod = serializers.SerializerMethodField()

    class Meta:
        model = LegalCaseRunningSheetEntry
        fields = (
                'id',
                'legal_case_id',
                'number',
                'date_modified',
                'date_mod',
                'time_mod',
                'user_full_name',
                'user_id',
                'description',
                'deleted',
                )
        read_only_fields = (
                'id',
                )

    def get_date_mod(self, obj):
        date_modified_loc = timezone.localtime(obj.date_modified)
        return date_modified_loc.strftime('%d/%m/%Y')

    def get_time_mod(self, obj):
        date_modified_loc = timezone.localtime(obj.date_modified)
        return date_modified_loc.strftime('%I:%M:%S %p')

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
                'legal_case_id',
                'user_id',
                'description',
                )
        read_only_fields = (
                'id',
                'number',
                'legal_case_id',
                )


class DeleteReinstateLegalCaseRunningSheetEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = LegalCaseRunningSheetEntry
        fields = (
                'id',
                'number',
                'legal_case_id',
                'deleted',
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
                'legal_case_id',
                'user_id',
                )

    def create(self, validated_data):
        legal_case_id = validated_data.get('legal_case_id')
        user_id = validated_data.get('user_id')
        new_entry = LegalCaseRunningSheetEntry.objects.create_running_sheet_entry(
                legal_case_id=legal_case_id, 
                user_id=user_id)
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


class BriefOfEvidenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = BriefOfEvidence
        fields = (
                'id',
                'legal_case_id',
                'statement_of_facts',
                'victim_impact_statement_taken',
                'statements_pending',
                'vulnerable_hostile_witnesses',
                'witness_refusing_statement',
                'problems_needs_prosecution_witnesses',
                'accused_bad_character',
                'further_persons_interviews_pending',
                'other_interviews',
                'relevant_persons_pending_charges',
                'other_persons_receiving_sanction_outcome',
                'local_public_interest',
                'applications_orders_requests',
                'applications_orders_required',
                'other_legal_matters',

                'victim_impact_statement_taken_details',
                'statements_pending_details',
                'vulnerable_hostile_witnesses_details',
                'witness_refusing_statement_details',
                'problems_needs_prosecution_witnesses_details',
                'accused_bad_character_details',
                'further_persons_interviews_pending_details',
                'other_interviews_details',
                'relevant_persons_pending_charges_details',
                'other_persons_receiving_sanction_outcome_details',
                'local_public_interest_details',
                'applications_orders_requests_details',
                'applications_orders_required_details',
                'other_legal_matters_details',
                )
        read_only_fields = (
                'id',
                'legal_case_id',
                )


class ProsecutionBriefSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProsecutionBrief
        fields = (
                'id',
                'legal_case_id',
                'statement_of_facts',
                'victim_impact_statement_taken',
                'statements_pending',
                'vulnerable_hostile_witnesses',
                'witness_refusing_statement',
                'problems_needs_prosecution_witnesses',
                'accused_bad_character',
                'further_persons_interviews_pending',
                'other_interviews',
                'relevant_persons_pending_charges',
                'other_persons_receiving_sanction_outcome',
                'local_public_interest',
                'applications_orders_requests',
                'applications_orders_required',
                'other_legal_matters',

                'victim_impact_statement_taken_details',
                'statements_pending_details',
                'vulnerable_hostile_witnesses_details',
                'witness_refusing_statement_details',
                'problems_needs_prosecution_witnesses_details',
                'accused_bad_character_details',
                'further_persons_interviews_pending_details',
                'other_interviews_details',
                'relevant_persons_pending_charges_details',
                'other_persons_receiving_sanction_outcome_details',
                'local_public_interest_details',
                'applications_orders_requests_details',
                'applications_orders_required_details',
                'other_legal_matters_details',
                )
        read_only_fields = (
                'id',
                'legal_case_id',
                )


class BaseLegalCaseSerializer(serializers.ModelSerializer):
    running_sheet_entries = LegalCaseRunningSheetEntrySerializer(many=True)
    legal_case_person = EmailUserSerializer(many=True)
    allocated_group = serializers.SerializerMethodField()
    user_in_group = serializers.SerializerMethodField()
    can_user_action = serializers.SerializerMethodField()
    user_is_assignee = serializers.SerializerMethodField()
    status = CustomChoiceField(read_only=True)
    related_items = serializers.SerializerMethodField()
    statement_artifacts = serializers.SerializerMethodField()
    legal_case_priority = LegalCasePrioritySerializer()
    offence_list = serializers.SerializerMethodField()
    brief_of_evidence = BriefOfEvidenceSerializer()
    prosecution_brief = ProsecutionBriefSerializer()
    court_proceedings = CourtProceedingsJournalSerializer()

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
                'statement_artifacts',
                'legal_case_person',
                'offence_list',
                'brief_of_evidence',
                'prosecution_brief',
                'court_proceedings',

                )
        read_only_fields = (
                'id',
                )

    def get_offence_list(self, obj):
        offence_list = [{
            'id': '',
            'lodgement_number': '',
            'identifier': '',
            }]
        offence_queryset = obj.offence_legal_case.all()
        if offence_queryset and offence_queryset.first().id:
            serializer = OffenceSerializer(offence_queryset, many=True, context=self.context)
            offence_list.extend(serializer.data)
        return offence_list

    def get_statement_artifacts(self, obj):
        artifact_list = []
        for link in obj.documentartifactlegalcases_set.all():
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


class LegalCaseBriefOfEvidenceSerializer(BaseLegalCaseSerializer):
    running_sheet_entries = LegalCaseRunningSheetEntrySerializer(many=True)
    allocated_group = serializers.SerializerMethodField()
    user_in_group = serializers.SerializerMethodField()
    can_user_action = serializers.SerializerMethodField()
    user_is_assignee = serializers.SerializerMethodField()
    status = CustomChoiceField(read_only=True)
    related_items = serializers.SerializerMethodField()
    statement_artifacts = serializers.SerializerMethodField()
    legal_case_priority = LegalCasePrioritySerializer()
    offence_list = serializers.SerializerMethodField()
    brief_of_evidence = BriefOfEvidenceSerializer()
    prosecution_brief = ProsecutionBriefSerializer()
    court_proceedings = CourtProceedingsJournalSerializer()

    boe_roi_ticked = serializers.SerializerMethodField()
    boe_roi_options = serializers.SerializerMethodField()
    boe_other_statements_ticked = serializers.SerializerMethodField()
    boe_other_statements_options = serializers.SerializerMethodField()
    legal_case_boe_other_statements = BriefOfEvidenceOtherStatementsSerializer(many=True)
    legal_case_boe_roi = BriefOfEvidenceRecordOfInterviewSerializer(many=True)
    brief_of_evidence = BriefOfEvidenceSerializer()
    boe_physical_artifacts_used = serializers.SerializerMethodField()
    boe_physical_artifacts_sensitive_unused = serializers.SerializerMethodField()
    boe_physical_artifacts_non_sensitive_unused = serializers.SerializerMethodField()
    boe_document_artifacts = serializers.SerializerMethodField()

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
                'statement_artifacts',
                'legal_case_person',
                'offence_list',
                'brief_of_evidence',
                'prosecution_brief',
                'court_proceedings',

                #'id',
                #'running_sheet_entries',
                ##'legal_case_person',
                #'allocated_group',
                #'allocated_group_id',
                #'user_in_group',
                #'can_user_action',
                #'user_is_assignee',
                #'status',
                #'related_items',
                #'statement_artifacts',
                #'legal_case_priority',
                #'offence_list',
                #'brief_of_evidence',
                #'prosecution_brief',
                #'court_proceedings',
                #'district_id',
                #'region_id',

                'boe_roi_ticked',
                'boe_roi_options',
                'legal_case_boe_roi',
                'boe_other_statements_ticked',
                'boe_other_statements_options',
                'legal_case_boe_other_statements',

                'boe_physical_artifacts_used',
                'boe_physical_artifacts_sensitive_unused',
                'boe_physical_artifacts_non_sensitive_unused',
                'boe_document_artifacts',

                )
        read_only_fields = (
                'id',
                )

    def get_boe_document_artifacts(self, obj):
        artifact_list = []
        for artifact in obj.briefofevidencedocumentartifacts_set.all():
            artifact_serializer = BriefOfEvidenceDocumentArtifactsSerializer(artifact)
            serialized_artifact = artifact_serializer.data
            artifact_list.append(serialized_artifact)
        return artifact_list
    # used physical artifacts
    def get_boe_physical_artifacts_used(self, obj):
        artifact_list = []
        for record in obj.briefofevidencephysicalartifacts_set.all():
            legal_case_physical_artifact_link = obj.physicalartifactlegalcases_set.get(
                    legal_case_id=obj.id,
                    physical_artifact_id=record.physical_artifact.id)
            if legal_case_physical_artifact_link.used_within_case:
                artifact_serializer = BriefOfEvidencePhysicalArtifactsSerializer(record)
                serialized_artifact = artifact_serializer.data
                artifact_list.append(serialized_artifact)
        return artifact_list
    # sensitive unused physical artifacts
    def get_boe_physical_artifacts_sensitive_unused(self, obj):
        artifact_list = []
        for record in obj.briefofevidencephysicalartifacts_set.all():
            legal_case_physical_artifact_link = obj.physicalartifactlegalcases_set.get(
                    legal_case_id=obj.id,
                    physical_artifact_id=record.physical_artifact.id)
            if (not legal_case_physical_artifact_link.used_within_case and 
                    legal_case_physical_artifact_link.sensitive_non_disclosable
                    ):
                artifact_serializer = BriefOfEvidencePhysicalArtifactsSerializer(record)
                serialized_artifact = artifact_serializer.data
                artifact_list.append(serialized_artifact)
        return artifact_list
    # non sensitive unused physical artifacts
    def get_boe_physical_artifacts_non_sensitive_unused(self, obj):
        artifact_list = []
        for record in obj.briefofevidencephysicalartifacts_set.all():
            legal_case_physical_artifact_link = obj.physicalartifactlegalcases_set.get(
                    legal_case_id=obj.id,
                    physical_artifact_id=record.physical_artifact.id)
            if (not legal_case_physical_artifact_link.used_within_case and not
                    legal_case_physical_artifact_link.sensitive_non_disclosable
                    ):
                artifact_serializer = BriefOfEvidencePhysicalArtifactsSerializer(record)
                serialized_artifact = artifact_serializer.data
                artifact_list.append(serialized_artifact)
        return artifact_list

    def get_boe_other_statements_ticked(self, obj):
        ticked_list = []
        for record in obj.legal_case_boe_other_statements.all():
            if record.ticked:
                ticked_list.append(record.id)
        return ticked_list

    def get_boe_other_statements_options(self, obj):
        person_list = []

        for person_level_record in obj.legal_case_boe_other_statements.filter(statement=None):
            person_serializer = BriefOfEvidenceOtherStatementsSerializer(
                    person_level_record)
            serialized_person = person_serializer.data
            person_children = []
            for statement_level_record in person_level_record.children.all():
                statement_serializer = BriefOfEvidenceOtherStatementsSerializer(
                        statement_level_record)
                serialized_statement = statement_serializer.data
                statement_children = []
                for doc_level_record in statement_level_record.children.all():
                    doc_serializer = BriefOfEvidenceOtherStatementsSerializer(
                            doc_level_record)
                    serialized_doc = doc_serializer.data
                    if serialized_doc:
                        statement_children.append(serialized_doc)
                serialized_statement['children'] = statement_children
                if serialized_statement:
                    person_children.append(serialized_statement)
            serialized_person['children'] = person_children
            person_list.append(serialized_person)
        return person_list

    def get_boe_roi_ticked(self, obj):
        ticked_list = []
        for record in obj.legal_case_boe_roi.all():
            if record.ticked:
                ticked_list.append(record.id)
        return ticked_list

    def get_boe_roi_options(self, obj):
        offence_list = []

        for offence_level_record in obj.legal_case_boe_roi.filter(offender=None):
            offence_serializer = BriefOfEvidenceRecordOfInterviewSerializer(
                    offence_level_record)
            serialized_offence = offence_serializer.data
            offence_children = []
            for offender_level_record in offence_level_record.children.all():
                offender_serializer = BriefOfEvidenceRecordOfInterviewSerializer(
                            offender_level_record)
                serialized_offender = offender_serializer.data
                offender_children = []
                for roi_level_record in offender_level_record.children.all():
                    roi_serializer = BriefOfEvidenceRecordOfInterviewSerializer(
                            roi_level_record)
                    serialized_roi = roi_serializer.data
                    roi_children = []
                    for doc_artifact_level_record in roi_level_record.children.all():
                        # check for associated docs and add to serialized_roi
                        doc_serializer = BriefOfEvidenceRecordOfInterviewSerializer(
                                doc_artifact_level_record)
                        serialized_doc_artifact = doc_serializer.data
                        if serialized_doc_artifact:
                            roi_children.append(serialized_doc_artifact)
                    serialized_roi['children'] = roi_children
                    # add roi to offender_children
                    if serialized_roi:
                        #serialized_offender['children'] = serialized_roi
                        offender_children.append(serialized_roi)
                # add roi list to offender
                serialized_offender['children'] = offender_children
                ## add offender to offence_list
                # add offender to offence
                if serialized_offender:
                    offence_children.append(serialized_offender)
            serialized_offence['children'] = offence_children
            offence_list.append(serialized_offence)
        return offence_list


#class LegalCaseProsecutionBriefSerializer(BaseLegalCaseSerializer):
class LegalCaseProsecutionBriefSerializer(LegalCaseBriefOfEvidenceSerializer):
    running_sheet_entries = LegalCaseRunningSheetEntrySerializer(many=True)
    allocated_group = serializers.SerializerMethodField()
    user_in_group = serializers.SerializerMethodField()
    can_user_action = serializers.SerializerMethodField()
    user_is_assignee = serializers.SerializerMethodField()
    status = CustomChoiceField(read_only=True)
    related_items = serializers.SerializerMethodField()
    statement_artifacts = serializers.SerializerMethodField()
    legal_case_priority = LegalCasePrioritySerializer()
    offence_list = serializers.SerializerMethodField()
    brief_of_evidence = BriefOfEvidenceSerializer()
    prosecution_brief = ProsecutionBriefSerializer()
    court_proceedings = CourtProceedingsJournalSerializer()

    pb_roi_ticked = serializers.SerializerMethodField()
    pb_roi_options = serializers.SerializerMethodField()
    pb_other_statements_ticked = serializers.SerializerMethodField()
    pb_other_statements_options = serializers.SerializerMethodField()
    legal_case_pb_other_statements = BriefOfEvidenceOtherStatementsSerializer(many=True)
    legal_case_pb_roi = BriefOfEvidenceRecordOfInterviewSerializer(many=True)
    brief_of_evidence = BriefOfEvidenceSerializer()
    pb_physical_artifacts_used = serializers.SerializerMethodField()
    pb_physical_artifacts_sensitive_unused = serializers.SerializerMethodField()
    pb_physical_artifacts_non_sensitive_unused = serializers.SerializerMethodField()
    pb_document_artifacts = serializers.SerializerMethodField()

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
                'statement_artifacts',
                'legal_case_person',
                'offence_list',
                'brief_of_evidence',
                'prosecution_brief',
                'court_proceedings',

                #'id',
                #'running_sheet_entries',
                ##'legal_case_person',
                #'allocated_group',
                #'allocated_group_id',
                #'user_in_group',
                #'can_user_action',
                #'user_is_assignee',
                #'status',
                #'related_items',
                #'statement_artifacts',
                #'legal_case_priority',
                #'offence_list',
                #'brief_of_evidence',
                #'prosecution_brief',
                #'court_proceedings',
                #'district_id',
                #'region_id',

                'pb_roi_ticked',
                'pb_roi_options',
                'legal_case_pb_roi',
                'pb_other_statements_ticked',
                'pb_other_statements_options',
                'legal_case_pb_other_statements',

                'pb_physical_artifacts_used',
                'pb_physical_artifacts_sensitive_unused',
                'pb_physical_artifacts_non_sensitive_unused',
                'pb_document_artifacts',
                'boe_roi_ticked',
                'boe_roi_options',
                'legal_case_boe_roi',
                'boe_other_statements_ticked',
                'boe_other_statements_options',
                'legal_case_boe_other_statements',

                'boe_physical_artifacts_used',
                'boe_physical_artifacts_sensitive_unused',
                'boe_physical_artifacts_non_sensitive_unused',
                'boe_document_artifacts',

                )
        read_only_fields = (
                'id',
                )

    def get_pb_document_artifacts(self, obj):
        artifact_list = []
        for artifact in obj.prosecutionbriefdocumentartifacts_set.all():
            artifact_serializer = ProsecutionBriefDocumentArtifactsSerializer(artifact)
            serialized_artifact = artifact_serializer.data
            artifact_list.append(serialized_artifact)
        return artifact_list
    # used physical artifacts
    def get_pb_physical_artifacts_used(self, obj):
        artifact_list = []
        for record in obj.prosecutionbriefphysicalartifacts_set.all():
            legal_case_physical_artifact_link = obj.physicalartifactlegalcases_set.get(
                    legal_case_id=obj.id,
                    physical_artifact_id=record.physical_artifact.id)
            if legal_case_physical_artifact_link.used_within_case:
                artifact_serializer = ProsecutionBriefPhysicalArtifactsSerializer(record)
                serialized_artifact = artifact_serializer.data
                artifact_list.append(serialized_artifact)
        return artifact_list
    # sensitive unused physical artifacts
    def get_pb_physical_artifacts_sensitive_unused(self, obj):
        artifact_list = []
        for record in obj.prosecutionbriefphysicalartifacts_set.all():
            legal_case_physical_artifact_link = obj.physicalartifactlegalcases_set.get(
                    legal_case_id=obj.id,
                    physical_artifact_id=record.physical_artifact.id)
            if (not legal_case_physical_artifact_link.used_within_case and 
                    legal_case_physical_artifact_link.sensitive_non_disclosable
                    ):
                artifact_serializer = ProsecutionBriefPhysicalArtifactsSerializer(record)
                serialized_artifact = artifact_serializer.data
                artifact_list.append(serialized_artifact)
        return artifact_list
    # non sensitive unused physical artifacts
    def get_pb_physical_artifacts_non_sensitive_unused(self, obj):
        artifact_list = []
        for record in obj.prosecutionbriefphysicalartifacts_set.all():
            legal_case_physical_artifact_link = obj.physicalartifactlegalcases_set.get(
                    legal_case_id=obj.id,
                    physical_artifact_id=record.physical_artifact.id)
            if (not legal_case_physical_artifact_link.used_within_case and not
                    legal_case_physical_artifact_link.sensitive_non_disclosable
                    ):
                artifact_serializer = ProsecutionBriefPhysicalArtifactsSerializer(record)
                serialized_artifact = artifact_serializer.data
                artifact_list.append(serialized_artifact)
        return artifact_list

    def get_pb_other_statements_ticked(self, obj):
        ticked_list = []
        for record in obj.legal_case_pb_other_statements.all():
            if record.ticked:
                ticked_list.append(record.id)
        return ticked_list

    def get_pb_other_statements_options(self, obj):
        person_list = []

        for person_level_record in obj.legal_case_pb_other_statements.filter(statement=None):
            person_serializer = ProsecutionBriefOtherStatementsSerializer(
                    person_level_record)
            serialized_person = person_serializer.data
            person_children = []
            for statement_level_record in person_level_record.children.all():
                statement_serializer = ProsecutionBriefOtherStatementsSerializer(
                        statement_level_record)
                serialized_statement = statement_serializer.data
                statement_children = []
                for doc_level_record in statement_level_record.children.all():
                    doc_serializer = ProsecutionBriefOtherStatementsSerializer(
                            doc_level_record)
                    serialized_doc = doc_serializer.data
                    if serialized_doc:
                        statement_children.append(serialized_doc)
                serialized_statement['children'] = statement_children
                if serialized_statement:
                    person_children.append(serialized_statement)
            serialized_person['children'] = person_children
            person_list.append(serialized_person)
        return person_list

    def get_pb_roi_ticked(self, obj):
        ticked_list = []
        for record in obj.legal_case_pb_roi.all():
            if record.ticked:
                ticked_list.append(record.id)
        return ticked_list

    def get_pb_roi_options(self, obj):
        offence_list = []

        for offence_level_record in obj.legal_case_pb_roi.filter(offender=None):
            offence_serializer = ProsecutionBriefRecordOfInterviewSerializer(
                    offence_level_record)
            serialized_offence = offence_serializer.data
            offence_children = []
            for offender_level_record in offence_level_record.children.all():
                offender_serializer = ProsecutionBriefRecordOfInterviewSerializer(
                            offender_level_record)
                serialized_offender = offender_serializer.data
                offender_children = []
                for roi_level_record in offender_level_record.children.all():
                    roi_serializer = ProsecutionBriefRecordOfInterviewSerializer(
                            roi_level_record)
                    serialized_roi = roi_serializer.data
                    roi_children = []
                    for doc_artifact_level_record in roi_level_record.children.all():
                        # check for associated docs and add to serialized_roi
                        doc_serializer = ProsecutionBriefRecordOfInterviewSerializer(
                                doc_artifact_level_record)
                        serialized_doc_artifact = doc_serializer.data
                        if serialized_doc_artifact:
                            roi_children.append(serialized_doc_artifact)
                    serialized_roi['children'] = roi_children
                    # add roi to offender_children
                    if serialized_roi:
                        offender_children.append(serialized_roi)
                # add roi list to offender
                serialized_offender['children'] = offender_children
                ## add offender to offence_list
                # add offender to offence
                if serialized_offender:
                    offence_children.append(serialized_offender)
            serialized_offence['children'] = offence_children
            offence_list.append(serialized_offence)
        return offence_list


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

    def create(self, validated_data):
        instance = super(SaveLegalCaseSerializer, self).create(validated_data)
        return instance

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
    
    class Meta:
        model = LegalCase
        fields = (
                'number',
                'title',
                'status',
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

