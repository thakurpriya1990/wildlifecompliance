from __future__ import unicode_literals
import logging
from django.db import models
from django.contrib.gis.db import models
from django.contrib.postgres.fields.jsonb import JSONField
from django.db.models import Max
from django.utils.encoding import python_2_unicode_compatible
from ledger.accounts.models import EmailUser, RevisionedMixin
from ledger.licence.models import LicenceType
from wildlifecompliance.components.organisations.models import Organisation
from wildlifecompliance.components.call_email.models import CallEmail, Location
#from wildlifecompliance.components.artifact.utils import build_legal_case_hierarchy
#from wildlifecompliance.components.artifact.utils import BriefOfEvidenceRecordOfInterview
from wildlifecompliance.components.main.models import (
        CommunicationsLogEntry,
        UserAction, 
        Document,
        )
from wildlifecompliance.components.main.related_item import can_close_legal_case
#from wildlifecompliance.components.users.models import CompliancePermissionGroup
from wildlifecompliance.components.users.models import Region, District
from django.core.exceptions import ValidationError
from treebeard.mp_tree import MP_Node
from datetime import datetime, timedelta, date
from django.utils import timezone

logger = logging.getLogger(__name__)


class LegalCasePriority(models.Model):
    case_priority = models.CharField(max_length=50)
    #schema = JSONField(null=True)
    #version = models.SmallIntegerField(default=1, blank=False, null=False)
    #description = models.CharField(max_length=255, blank=True, null=True)
    #replaced_by = models.ForeignKey(
     #   'self', on_delete=models.PROTECT, blank=True, null=True)
    #date_created = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_CasePriority'
        verbose_name_plural = 'CM_CasePriorities'
        #unique_together = ('case_priority', 'version')

    def __str__(self):
        #return '{0}, v.{1}'.format(self.case_priority, self.version)
        return self.case_priority


class CourtProceedings(models.Model):
    legal_case = models.OneToOneField(
        'LegalCase',
        null=True,
        blank=True,
        related_name="court_proceedings",
    )
    court_outcome_details = models.TextField(blank=True)
    court_outcome_type = models.ForeignKey('CourtOutcomeType', null=True, blank=True)
    court_outcome_fines = models.DecimalField(
        verbose_name="Fines",
        decimal_places=2,
        max_digits=12,
        blank=True,
        null=True)
    court_outcome_costs = models.DecimalField(
        verbose_name="Costs",
        decimal_places=2,
        max_digits=12,
        blank=True,
        null=True)

    class Meta:
        app_label = 'wildlifecompliance'


class LegalCase(RevisionedMixin):
    STATUS_OPEN = 'open'
    STATUS_WITH_MANAGER = 'with_manager'
    STATUS_WITH_PROSECUTION_COORDINATOR = 'with_prosecution_coordinator'
    STATUS_WITH_PROSECUTION_COUNCIL = 'with_prosecution_council'
    STATUS_WITH_PROSECUTION_MANAGER = 'with_prosecution_manager'
    STATUS_AWAIT_ENDORSEMENT = 'await_endorsement'
    STATUS_BRIEF_OF_EVIDENCE = 'brief_of_evidence'
    STATUS_WITH_PROSECUTION_COORDINATOR_PROSECUTION_BRIEF = 'with_prosecution_coordinator_prosecution_brief'
    STATUS_WITH_PROSECUTION_COORDINATOR_COURT = 'with_prosecution_coordinator_court'
    STATUS_DISCARDED = 'discarded'
    STATUS_CLOSED = 'closed'
    STATUS_PENDING_CLOSURE = 'pending_closure'
    STATUS_CHOICES = (
            (STATUS_OPEN, 'Open'),
            (STATUS_WITH_MANAGER, 'With Manager'),
            (STATUS_WITH_PROSECUTION_COORDINATOR, 'With Prosecution Coordinator'),
            (STATUS_WITH_PROSECUTION_COORDINATOR_PROSECUTION_BRIEF, 'With Prosecution Coordinator (Prosecution Brief)'),
            (STATUS_WITH_PROSECUTION_COORDINATOR_COURT, 'With Prosecution Coordinator (Court)'),
            (STATUS_WITH_PROSECUTION_COUNCIL, 'With Prosecution Council'),
            (STATUS_WITH_PROSECUTION_MANAGER, 'With Prosecution Manager'),
            (STATUS_AWAIT_ENDORSEMENT, 'Awaiting Endorsement'),
            (STATUS_DISCARDED, 'Discarded'),
            (STATUS_BRIEF_OF_EVIDENCE, 'Brief of Evidence'),
            (STATUS_CLOSED, 'Closed'),
            (STATUS_PENDING_CLOSURE, 'Pending Closure')
            )

    title = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(
            max_length=100,
            choices=STATUS_CHOICES,
            default='open'
            )
    details = models.TextField(blank=True, null=True)
    number = models.CharField(max_length=50, blank=True, null=True)
    case_created_date = models.DateField(auto_now_add=True, blank=True, null=True)
    case_created_time = models.TimeField(auto_now_add=True, blank=True, null=True)
    call_email = models.ForeignKey(
        CallEmail, 
        related_name='legal_case_call_email',
        null=True
        )
    assigned_to = models.ForeignKey(
        EmailUser, 
        related_name='legal_case_assigned_to',
        null=True
        )
    #allocated_group = models.ForeignKey(
    #    CompliancePermissionGroup,
    #    related_name='legal_case_allocated_group', 
    #    null=True
    #    )
    #region = models.ForeignKey(
    #    Region, 
    #    related_name='legal_case_region', 
    #    null=True
    #)
    #district = models.ForeignKey(
    #    District, 
    #    related_name='legal_case_district', 
    #    null=True
    #)
    legal_case_priority = models.ForeignKey(
            LegalCasePriority,
            null=True
            )
    associated_persons = models.ManyToManyField(
            EmailUser,
            related_name='legal_case_associated_persons',
            )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_LegalCase'
        verbose_name_plural = 'CM_LegalCases'

    def __str__(self):
        return 'ID: {}, Title: {}'.format(self.number, self.title)

    # Prefix "CS" char to LegalCase number.
    def save(self, *args, **kwargs):
        super(LegalCase, self).save(*args,**kwargs)

        if self.number is None:
            new_number_id = 'CS{0:06d}'.format(self.pk)
            self.number = new_number_id
            self.save()

        if not hasattr(self, 'court_proceedings'):
            cp = CourtProceedings.objects.create(legal_case=self)
            cp.save()

    def log_user_action(self, action, request):
        # return LegalCaseUserAction.log_action(self, action, request.user)
        if request:
            return LegalCaseUserAction.log_action(self, action, request.user)
        else:
            return LegalCaseUserAction.log_action(self, action)

    @property
    def get_related_items_identifier(self):
        return self.number

    @property
    def get_related_items_descriptor(self):
        #return '{0}, {1}'.format(self.title, self.details)
        return self.title

    def close(self, request=None):
        close_record, parents = can_close_legal_case(self, request)
        if close_record:
            self.status = self.STATUS_CLOSED
            self.log_user_action(
                    LegalCaseUserAction.ACTION_CLOSE.format(self.number),
                    request)
        else:
            self.status = self.STATUS_PENDING_CLOSURE
            self.log_user_action(
                    LegalCaseUserAction.ACTION_PENDING_CLOSURE.format(self.number), 
                    request)
        self.save()
        # Call close() on any parent with pending_closure status
        if parents and self.status == 'closed':
            for parent in parents:
                if parent.status == 'pending_closure':
                    parent.close(request)

    def set_status_brief_of_evidence(self, request):
        self.assigned_to = None
        self.status = self.STATUS_BRIEF_OF_EVIDENCE
        self.log_user_action(
            LegalCaseUserAction.ACTION_STATUS_BRIEF_OF_EVIDENCE.format(self.number), 
            request)
        self.save()

    def set_status_generate_prosecution_brief(self, request):
        self.assigned_to = None
        self.status = self.STATUS_WITH_PROSECUTION_COORDINATOR_PROSECUTION_BRIEF
        self.log_user_action(
            LegalCaseUserAction.ACTION_GENERATE_PROSECUTION_BRIEF.format(self.number), 
            request)
        self.save()

    def send_to_prosecution_coordinator(self, request):
        self.assigned_to = None
        self.status = self.STATUS_WITH_PROSECUTION_COORDINATOR
        self.log_user_action(
            LegalCaseUserAction.ACTION_STATUS_WITH_PROSECUTION_COORDINATOR.format(self.number), 
            request)
        # set allocated group to 
        self.allocated_group = CompliancePermissionGroup.objects.get(permissions__codename="prosecution_coordinator")
        self.save()

    def back_to_prosecution_coordinator(self, request):
        self.assigned_to = None
        self.status = self.STATUS_WITH_PROSECUTION_COORDINATOR_PROSECUTION_BRIEF
        self.log_user_action(
            LegalCaseUserAction.ACTION_STATUS_WITH_PROSECUTION_COORDINATOR_PROSECUTION_BRIEF.format(self.number), 
            request)
        # set allocated group to 
        self.allocated_group = CompliancePermissionGroup.objects.get(permissions__codename="prosecution_coordinator")
        self.save()

    def send_to_prosecution_council(self, request):
        self.assigned_to = None
        self.status = self.STATUS_WITH_PROSECUTION_COUNCIL
        self.log_user_action(
            LegalCaseUserAction.ACTION_STATUS_WITH_PROSECUTION_COUNCIL.format(self.number), 
            request)
        # set allocated group to 
        self.allocated_group = CompliancePermissionGroup.objects.get(permissions__codename="prosecution_council")
        self.save()

    def approve_for_court(self, request):
        self.assigned_to = None
        self.status = self.STATUS_WITH_PROSECUTION_COORDINATOR_COURT
        self.log_user_action(
            LegalCaseUserAction.ACTION_APPROVE_FOR_COURT.format(self.number), 
            request)
        # set allocated group to 
        self.allocated_group = CompliancePermissionGroup.objects.get(permissions__codename="prosecution_council")
        self.save()

    def send_to_prosecution_manager(self, request):
        self.assigned_to = None
        self.status = self.STATUS_WITH_PROSECUTION_MANAGER
        self.log_user_action(
            LegalCaseUserAction.ACTION_STATUS_WITH_PROSECUTION_MANAGER.format(self.number), 
            request)
        # set allocated group to 
        self.allocated_group = CompliancePermissionGroup.objects.get(permissions__codename="prosecution_manager")
        self.save()

    def send_to_manager(self, request):
        self.assigned_to = None
        self.status = self.STATUS_WITH_MANAGER
        self.log_user_action(
            LegalCaseUserAction.ACTION_SEND_TO_MANAGER.format(self.number), 
            request)
        # set allocated group to 
        #region_district_id = self.district_id if self.district_id else self.region_id
        #region_district = Region.objects.get(id=region_district_id)
        region_district = self.allocated_group.region_district
        if type(region_district) is District:
            self.allocated_group = CompliancePermissionGroup.district_groups.get(district=region_district, permissions__codename="manager")
        elif type(region_district) is Region:
            self.allocated_group = CompliancePermissionGroup.district_groups.get(region=region_district, permissions__codename="manager")
        #self.allocated_group = CompliancePermissionGroup.objects.get(region_district=region_district, permissions__codename="manager")
        self.save()

    def back_to_case(self, request):
        self.assigned_to = None
        self.status = self.STATUS_OPEN
        self.log_user_action(
            LegalCaseUserAction.ACTION_BACK_TO_CASE.format(self.number), 
            request)
        self.save()

    def back_to_officer(self, request):
        self.assigned_to = None
        self.status = self.STATUS_BRIEF_OF_EVIDENCE
        self.log_user_action(
            LegalCaseUserAction.ACTION_BACK_TO_OFFICER.format(self.number), 
            request)
        # set allocated group to 
        #region_district_id = self.district_id if self.district_id else self.region_id
        #region_district = RegionDistrict.objects.get(id=region_district_id)
        #self.allocated_group = CompliancePermissionGroup.objects.get(region_district=region_district, permissions__codename="officer")
        region_district = self.allocated_group.region_district
        if type(region_district) is District:
            self.allocated_group = CompliancePermissionGroup.district_groups.get(district=region_district, permissions__codename="officer")
        elif type(region_district) is Region:
            self.allocated_group = CompliancePermissionGroup.district_groups.get(region=region_district, permissions__codename="officer")
        self.save()


class BriefOfEvidence(models.Model):
    legal_case = models.OneToOneField(
            LegalCase,
            null=True,
            blank=True,
            related_name="brief_of_evidence",
            )
    statement_of_facts = models.TextField(blank=True, null=True)
    victim_impact_statement_taken = models.BooleanField(default=False)
    statements_pending = models.BooleanField(default=False)
    vulnerable_hostile_witnesses = models.BooleanField(default=False)
    witness_refusing_statement = models.BooleanField(default=False)
    problems_needs_prosecution_witnesses = models.BooleanField(default=False)
    accused_bad_character = models.BooleanField(default=False)
    further_persons_interviews_pending = models.BooleanField(default=False)
    other_interviews = models.BooleanField(default=False)
    relevant_persons_pending_charges = models.BooleanField(default=False)
    other_persons_receiving_sanction_outcome = models.BooleanField(default=False)
    local_public_interest = models.BooleanField(default=False)
    applications_orders_requests = models.BooleanField(default=False)
    applications_orders_required = models.BooleanField(default=False)
    other_legal_matters = models.BooleanField(default=False)

    victim_impact_statement_taken_details = models.TextField(blank=True, null=True)
    statements_pending_details = models.TextField(blank=True, null=True)
    vulnerable_hostile_witnesses_details = models.TextField(blank=True, null=True)
    witness_refusing_statement_details = models.TextField(blank=True, null=True)
    problems_needs_prosecution_witnesses_details = models.TextField(blank=True, null=True)
    accused_bad_character_details = models.TextField(blank=True, null=True)
    further_persons_interviews_pending_details = models.TextField(blank=True, null=True)
    other_interviews_details = models.TextField(blank=True, null=True)
    relevant_persons_pending_charges_details = models.TextField(blank=True, null=True)
    other_persons_receiving_sanction_outcome_details = models.TextField(blank=True, null=True)
    local_public_interest_details = models.TextField(blank=True, null=True)
    applications_orders_requests_details = models.TextField(blank=True, null=True)
    applications_orders_required_details = models.TextField(blank=True, null=True)
    other_legal_matters_details = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'


class ProsecutionBrief(models.Model):
    legal_case = models.OneToOneField(
            LegalCase,
            null=True,
            blank=True,
            related_name="prosecution_brief",
            )
    statement_of_facts = models.TextField(blank=True, null=True)
    victim_impact_statement_taken = models.BooleanField(default=False)
    statements_pending = models.BooleanField(default=False)
    vulnerable_hostile_witnesses = models.BooleanField(default=False)
    witness_refusing_statement = models.BooleanField(default=False)
    problems_needs_prosecution_witnesses = models.BooleanField(default=False)
    accused_bad_character = models.BooleanField(default=False)
    further_persons_interviews_pending = models.BooleanField(default=False)
    other_interviews = models.BooleanField(default=False)
    relevant_persons_pending_charges = models.BooleanField(default=False)
    other_persons_receiving_sanction_outcome = models.BooleanField(default=False)
    local_public_interest = models.BooleanField(default=False)
    applications_orders_requests = models.BooleanField(default=False)
    applications_orders_required = models.BooleanField(default=False)
    other_legal_matters = models.BooleanField(default=False)

    victim_impact_statement_taken_details = models.TextField(blank=True, null=True)
    statements_pending_details = models.TextField(blank=True, null=True)
    vulnerable_hostile_witnesses_details = models.TextField(blank=True, null=True)
    witness_refusing_statement_details = models.TextField(blank=True, null=True)
    problems_needs_prosecution_witnesses_details = models.TextField(blank=True, null=True)
    accused_bad_character_details = models.TextField(blank=True, null=True)
    further_persons_interviews_pending_details = models.TextField(blank=True, null=True)
    other_interviews_details = models.TextField(blank=True, null=True)
    relevant_persons_pending_charges_details = models.TextField(blank=True, null=True)
    other_persons_receiving_sanction_outcome_details = models.TextField(blank=True, null=True)
    local_public_interest_details = models.TextField(blank=True, null=True)
    applications_orders_requests_details = models.TextField(blank=True, null=True)
    applications_orders_required_details = models.TextField(blank=True, null=True)
    other_legal_matters_details = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'


class CourtProceedingsJournalEntryManager(models.Manager):
    def create_journal_entry(self, court_proceedings_id, user_id):
        max_row_num_dict = CourtProceedingsJournalEntry.objects.filter(court_proceedings_id=court_proceedings_id).aggregate(Max('row_num'))
        # initial value for new LegalCase
        row_num = 1
        # increment initial value if other entries exist for LegalCase
        if max_row_num_dict.get('row_num__max'):
            max_row_num = int(max_row_num_dict.get('row_num__max'))
            row_num = max_row_num + 1
        journal_entry = self.create(row_num=row_num, court_proceedings_id=court_proceedings_id, user_id=user_id)

        return journal_entry


class CourtProceedingsJournalEntry(RevisionedMixin):
    court_proceedings = models.ForeignKey(CourtProceedings, related_name='journal_entries')
    #person = models.ManyToManyField(LegalCasePerson, related_name='journal_entry_person')
    date_modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(EmailUser, related_name='journal_entry_user')
    description = models.TextField(blank=True)
    row_num = models.SmallIntegerField(blank=False, null=False)
    deleted = models.BooleanField(default=False)
    objects = CourtProceedingsJournalEntryManager()

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = ('court_proceedings', 'row_num')

    def number(self):
        #return self.court_proceedings.number + '-' + str(self.row_num)
        number = ''
        if self.court_proceedings.legal_case:
            number = self.court_proceedings.legal_case.number + '-' + str(self.row_num)
        return number

    def delete_entry(self):
        is_deleted = False
        if not self.deleted:
            self.deleted = True
            is_deleted = True
        return is_deleted

    def reinstate_entry(self):
        is_reinstated = False
        if self.deleted:
            self.deleted = False
            is_reinstated = True
        return is_reinstated

class LegalCasePerson(EmailUser):
    legal_case = models.ForeignKey(LegalCase, related_name='legal_case_person')

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return "id:{}, legal_case_id:{}".format(
                self.id,
                self.legal_case_id,
                )

class LegalCaseRunningSheetEntryManager(models.Manager):
    def create_running_sheet_entry(self, legal_case_id, user_id):
        max_row_num_dict = LegalCaseRunningSheetEntry.objects.filter(legal_case_id=legal_case_id).aggregate(Max('row_num'))
        # initial value for new LegalCase
        row_num = 1
        # increment initial value if other entries exist for LegalCase
        if max_row_num_dict.get('row_num__max'):
            max_row_num = int(max_row_num_dict.get('row_num__max'))
            row_num = max_row_num + 1
        running_sheet_entry = self.create(row_num=row_num, legal_case_id=legal_case_id, user_id=user_id)

        return running_sheet_entry


class LegalCaseRunningSheetEntry(RevisionedMixin):
    legal_case = models.ForeignKey(LegalCase, related_name='running_sheet_entries')
    # TODO: person fk req?  Url links in description instead
    person = models.ManyToManyField(LegalCasePerson, related_name='running_sheet_entry_person')
    #number = models.CharField(max_length=50, blank=True)
    #date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(EmailUser, related_name='running_sheet_entry_user')
    #description = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    row_num = models.SmallIntegerField(blank=False, null=False)
    deleted = models.BooleanField(default=False)
    objects = LegalCaseRunningSheetEntryManager()

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = ('legal_case', 'row_num')

    def __str__(self):
        return "Number:{}, User:{}, Description:{}".format(
                self.number(),
                self.user,
                self.description)

    def legal_case_persons(self):
        persons = self.legal_case.legal_case_person.all()
        return persons

    def number(self):
        return self.legal_case.number + '-' + str(self.row_num)

    def delete_entry(self):
        is_deleted = False
        if not self.deleted:
            self.deleted = True
            is_deleted = True
        return is_deleted

    def reinstate_entry(self):
        is_reinstated = False
        if self.deleted:
            self.deleted = False
            is_reinstated = True
        return is_reinstated


class LegalCaseCommsLogEntry(CommunicationsLogEntry):
    legal_case = models.ForeignKey(LegalCase, related_name='comms_logs')

    class Meta:
        app_label = 'wildlifecompliance'


class LegalCaseCommsLogDocument(Document):
    log_entry = models.ForeignKey(
        LegalCaseCommsLogEntry,
        related_name='documents')
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'


# class LegalCaseUserAction(UserAction):
class LegalCaseUserAction(models.Model):
    ACTION_CREATE_LEGAL_CASE = "Create Case {}"
    ACTION_SAVE_LEGAL_CASE = "Save Case {}"
    ACTION_STATUS_BRIEF_OF_EVIDENCE = "Generate 'Brief of Evidence' for Case {}"
    ACTION_GENERATE_PROSECUTION_BRIEF = "Generate 'Prosecution Brief' for Case {}"
    ACTION_GENERATE_DOCUMENT = "Generate {} for Case {} with sections: {}"
    ACTION_STATUS_WITH_PROSECUTION_COORDINATOR = "Send Case {} to Prosecution Coordinator"
    ACTION_STATUS_WITH_PROSECUTION_COORDINATOR_PROSECUTION_BRIEF = "Change status of Case {} to Prosecution Coordinator (Prosecution Brief)"
    ACTION_STATUS_WITH_PROSECUTION_COUNCIL = "Send Case {} to Prosecution Council"
    ACTION_STATUS_WITH_PROSECUTION_MANAGER = "Send Case {} to Prosecution Manager"
    ACTION_APPROVE_FOR_COURT = "Approve Case {} for Court"
    ACTION_SEND_TO_MANAGER = "Send Case {} to Manager"
    ACTION_BACK_TO_CASE = "Return Case {} to Open status"
    ACTION_BACK_TO_OFFICER = "Return Case {} to Officer"
    ACTION_CLOSE = "Close Legal Case {}"
    ACTION_PENDING_CLOSURE = "Mark Inspection {} as pending closure"
    ACTION_ADD_WEAK_LINK = "Create manual link between {}: {} and {}: {}"
    ACTION_REMOVE_WEAK_LINK = "Remove manual link between {}: {} and {}: {}"

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, legal_case, action, user=None):
        return cls.objects.create(
            legal_case=legal_case,
            who=user,
            what=str(action)
        )

    who = models.ForeignKey(EmailUser, null=True, blank=True)
    when = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    what = models.TextField(blank=False)
    legal_case = models.ForeignKey(LegalCase, related_name='action_logs')


class LegalCaseDocument(Document):
    legal_case = models.ForeignKey(LegalCase, related_name='documents')
    _file = models.FileField(max_length=255)
    input_name = models.CharField(max_length=255, blank=True, null=True)
    # after initial submit prevent document from being deleted
    can_delete = models.BooleanField(default=True)
    version_comment = models.CharField(max_length=255, blank=True, null=True)

    def delete(self):
        if self.can_delete:
            return super(LegalCaseDocument, self).delete()

    class Meta:
        app_label = 'wildlifecompliance'


class ProsecutionNoticeDocument(Document):
    legal_case = models.ForeignKey(LegalCase, related_name='prosecution_notices')
    _file = models.FileField(max_length=255,)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_ProsecutionNoticeDocument'
        verbose_name_plural = 'CM_ProsecutionNoticeDocuments'


class CourtHearingNoticeDocument(Document):
    legal_case = models.ForeignKey(LegalCase, related_name='court_hearing_notices')
    _file = models.FileField(max_length=255,)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_CourtHearingNoticeDocument'
        verbose_name_plural = 'CM_CourtHearingNoticeDocuments'


class BriefOfEvidenceDocument(Document):
    brief_of_evidence = models.ForeignKey(BriefOfEvidence, related_name='documents')
    _file = models.FileField(max_length=255)
    input_name = models.CharField(max_length=255, blank=True, null=True)
    # after initial submit prevent document from being deleted
    can_delete = models.BooleanField(default=True)
    version_comment = models.CharField(max_length=255, blank=True, null=True)

    def delete(self):
        if self.can_delete:
            return super(BriefOfEvidenceDocument, self).delete()
    class Meta:
        app_label = 'wildlifecompliance'

class ProsecutionBriefDocument(Document):
    prosecution_brief = models.ForeignKey(ProsecutionBrief, related_name='documents')
    _file = models.FileField(max_length=255)
    input_name = models.CharField(max_length=255, blank=True, null=True)
    # after initial submit prevent document from being deleted
    can_delete = models.BooleanField(default=True)
    version_comment = models.CharField(max_length=255, blank=True, null=True)

    def delete(self):
        if self.can_delete:
            return super(ProsecutionBriefDocument, self).delete()
    class Meta:
        app_label = 'wildlifecompliance'


class LegalCaseGeneratedDocument(Document):
    legal_case = models.ForeignKey(LegalCase, related_name='generated_documents')
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_LegalCaseGeneratedDocument'
        verbose_name_plural = 'CM_LegalCaseGeneratedDocuments'


def update_court_outcome_doc_filename(instance, filename):
    return 'wildlifecompliance/legal_case/{}/court_outcome_documents/{}'.format(instance.legal_case.id, filename)


class CourtOutcomeDocument(Document):
    court_proceedings = models.ForeignKey(CourtProceedings, related_name='court_outcome_documents')
    _file = models.FileField(max_length=255, upload_to=update_court_outcome_doc_filename)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_CourtOutcomeDocument'
        verbose_name_plural = 'CM_CourtOutcomeDocuments'


class Court(models.Model):
    identifier = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Court'
        verbose_name_plural = 'CM_Courts'

    def __str__(self):
        return self.identifier + ' ({})'.format(self.location)


class CourtOutcomeType(models.Model):
    identifier = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_CourtOutcomeType'
        verbose_name_plural = 'CM_CourtOutcomeTypes'

    def __str__(self):
        return self.identifier


class CourtDate(models.Model):
    court_proceedings = models.ForeignKey(CourtProceedings, related_name='court_dates')
    court_datetime = models.DateTimeField(blank=True, null=True,)
    comments = models.TextField(blank=True)
    court = models.ForeignKey(Court, blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_CourtDate'
        verbose_name_plural = 'CM_CourtDates'


import reversion
#reversion.register(LegalCaseRunningSheetEntry, follow=['user'])
#reversion.register(CourtProceedingsJournalEntry, follow=['user'])
#reversion.register(LegalCase)
reversion.register(EmailUser)

reversion.register(LegalCasePriority, follow=['legalcase_set'])
reversion.register(CourtProceedings, follow=['journal_entries', 'court_outcome_documents', 'court_dates'])
#reversion.register(LegalCase_associated_persons, follow=[])
reversion.register(LegalCase, follow=['court_proceedings', 'brief_of_evidence', 'prosecution_brief', 'legal_case_person', 'running_sheet_entries', 'comms_logs', 'action_logs', 'documents', 'prosecution_notices', 'court_hearing_notices', 'generated_documents', 'inspection_legal_case', 'offence_legal_case', 'legal_case_document_artifacts', 'documentartifactlegalcases_set', 'briefofevidencedocumentartifacts_set', 'prosecutionbriefdocumentartifacts_set', 'legal_case_physical_artifacts', 'physicalartifactlegalcases_set', 'briefofevidencephysicalartifacts_set', 'prosecutionbriefphysicalartifacts_set', 'legal_case_boe_other_statements', 'legal_case_boe_roi', 'legal_case_pb_other_statements', 'legal_case_pb_roi'])
reversion.register(BriefOfEvidence, follow=['documents'])
reversion.register(ProsecutionBrief, follow=['documents'])
reversion.register(CourtProceedingsJournalEntry, follow=[])
reversion.register(LegalCasePerson, follow=['logentry_set', 'social_auth', 'revision_set', 'userrecord_set', 'userproductview_set', 'usersearch_set', 'addresses', 'reviews', 'review_votes', 'partners', 'baskets', 'bankcards', 'rangeproductfileupload_set', 'orders', 'ordernote_set', 'emails', 'notifications', 'notification_set', 'alerts', 'voucherapplication_set', 'wishlists', 'profile_addresses', 'emailidentity_set', 'emailuseraction_set', 'action_logs', 'comms_logs', 'profiles', 'holder', 'issuer', 'trackrefund_set', 'stored_cards', 'wildlifecompliance_organisations', 'organisationcontactaction_set', 'organisationcontactdeclineddetails_set', 'userdelegation_set', 'organisationaction_set', 'organisationrequest_set', 'org_request_assignee', 'organisationrequestuseraction_set', 'organisationrequestdeclineddetails_set', 'compliancemanagementuserpreferences_set', 'intelligence_documents', 'callemail_assigned_to', 'callemail_volunteer', 'callemail_set', 'callemailuseraction_set', 'legal_case_assigned_to', 'legal_case_associated_persons', 'journal_entry_user', 'running_sheet_entry_user', 'legalcaseuseraction_set', 'individual_inspected', 'inspection_assigned_to', 'inspection_team_lead', 'inspection_set', 'inspectionuseraction_set', 'licenceuseraction_set', 'wildlifecompliance_proxy', 'wildlifecompliance_applications', 'wildlifecompliance_assessor', 'applicationselectedactivity_set', 'wildlifecompliance_officer_finalisation', 'wildlifecompliance_officer', 'applicationuseraction_set', 'returns_curator', 'returns_submitter', 'returnuseraction_set', 'offence_assigned_to', 'alleged_offence_removed_by', 'offender_removed_by', 'offender_person', 'offenceuseraction_set', 'sanctionoutcomeduedate_set', 'created_by_infringement_penalty', 'sanction_outcome_assigned_to', 'sanction_outcome_responsible_officer', 'sanction_outcome_registration_holder', 'sanction_outcome_driver', 'sanctionoutcomedocumentaccesslog_set', 'sanctionoutcomeuseraction_set', 'document_artifact_person_providing_statement', 'document_artifact_officer_interviewer', 'document_artifact_people_attending', 'physical_artifact_officer', 'physical_artifact_custodian', 'artifactuseraction_set', 'email_user_boe_other_statements', 'email_user_pb_other_statements', 'running_sheet_entry_person'])
#reversion.register(LegalCaseRunningSheetEntry_person, follow=[])
reversion.register(LegalCaseRunningSheetEntry, follow=[])
reversion.register(LegalCaseCommsLogEntry, follow=['documents'])
reversion.register(LegalCaseCommsLogDocument, follow=[])
reversion.register(LegalCaseUserAction, follow=[])
reversion.register(LegalCaseDocument, follow=[])
reversion.register(ProsecutionNoticeDocument, follow=[])
reversion.register(CourtHearingNoticeDocument, follow=[])
reversion.register(BriefOfEvidenceDocument, follow=[])
reversion.register(ProsecutionBriefDocument, follow=[])
reversion.register(LegalCaseGeneratedDocument, follow=[])
reversion.register(CourtOutcomeDocument, follow=[])
reversion.register(Court, follow=['courtdate_set'])
reversion.register(CourtOutcomeType, follow=['courtproceedings_set'])
reversion.register(CourtDate, follow=[])

