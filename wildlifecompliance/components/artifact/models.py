from __future__ import unicode_literals
import logging
from django.db import models
from django.contrib.gis.db import models
from django.contrib.postgres.fields.jsonb import JSONField
from django.db.models import Max
from django.utils.encoding import python_2_unicode_compatible
from ledger.accounts.models import EmailUser, RevisionedMixin
from wildlifecompliance.components.organisations.models import Organisation
from wildlifecompliance.components.call_email.models import CallEmail, Location
from wildlifecompliance.components.main.models import (
        CommunicationsLogEntry,
        UserAction, 
        Document,
        )
from wildlifecompliance.components.main.related_item import can_close_record
from wildlifecompliance.components.users.models import RegionDistrict, CompliancePermissionGroup
from wildlifecompliance.components.offence.models import Offence
from wildlifecompliance.components.legal_case.models import LegalCase
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class Artifact(RevisionedMixin):
    # _file - document or seizure notice
    #_file = models.FileField(max_length=255, null=True)
    identifier = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    artifact_date = models.DateField(null=True)
    artifact_time = models.TimeField(blank=True, null=True)
    number = models.CharField(max_length=50, blank=True, null=True)
    #custodian = models.ForeignKey(
    #        EmailUser,
    #        related_name='artifact_custodian',
    #        null=True,
    #        )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Artifact'
        verbose_name_plural = 'CM_Artifacts'

    # Prefix "OB" char to DocumentArtifact number.
    def save(self, *args, **kwargs):
        
        super(Artifact, self).save(*args,**kwargs)
        if self.number is None:
            new_number_id = 'OB{0:06d}'.format(self.pk)
            self.number = new_number_id
            self.save()

    @property
    def object_type(self):
        return 'object_type'

    @property
    def custodian(self):
        return 'custodian'

    @property
    def get_related_items_identifier(self):
        return self.number

    @property
    def get_related_items_descriptor(self):
        #return '{0}, {1}'.format(self.title, self.details)
        return self.identifier
    #def log_user_action(self, action, request):
     #   return ArtifactUserAction.log_action(self, action, request.user)

class DocumentArtifactType(models.Model):
    artifact_type = models.CharField(max_length=50)
    #schema = JSONField(null=True)
    version = models.SmallIntegerField(default=1, blank=False, null=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    replaced_by = models.ForeignKey(
        'self', on_delete=models.PROTECT, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_DocumentArtifactType'
        verbose_name_plural = 'CM_DocumentArtifactTypes'
        unique_together = ('artifact_type', 'version')

    def __str__(self):
        return self.artifact_type


class PhysicalArtifactType(models.Model):
    artifact_type = models.CharField(max_length=50)
    details_schema = JSONField(default=[{}])
    storage_schema = JSONField(default=[{}])
    version = models.SmallIntegerField(default=1, blank=False, null=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    replaced_by = models.ForeignKey(
        'self', 
        on_delete=models.PROTECT, 
        blank=True, 
        null=True
        )
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_PhysicalArtifactType'
        verbose_name_plural = 'CM_PhysicalArtifactTypes'
        unique_together = ('artifact_type', 'version')

    def __str__(self):
        return self.artifact_type


class PhysicalArtifactDisposalMethod(models.Model):
    disposal_method = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_PhysicalArtifactDisposalMethod'
        verbose_name_plural = 'CM_PhysicalArtifactDisposalMethods'
        #unique_together = ('artifact_type', 'version')


class DocumentArtifact(Artifact):
    document_type = models.ForeignKey(
            DocumentArtifactType,
            null=True
            )
    #_file = models.FileField(max_length=255)
    #identifier = models.CharField(max_length=255, blank=True, null=True)
    #description = models.TextField(blank=True, null=True)
    legal_case = models.ForeignKey(
            LegalCase,
            related_name='legal_case_document_artifacts',
            null=True,
            )
    statement = models.ForeignKey(
        'self', 
        related_name='document_artifact_statement',
        on_delete=models.PROTECT, 
        blank=True, 
        null=True
        )
    #custodian = models.ForeignKey(
    #        EmailUser,
    #        related_name='document_artifact_custodian',
    #        null=True,
    #        )
    #document_created_date = models.DateField(null=True)
    #document_created_time = models.TimeField(blank=True, null=True)
    person_providing_statement = models.ForeignKey(
            EmailUser,
            related_name='document_artifact_person_providing_statement',
            null=True,
            )
    interviewer = models.ForeignKey(
            EmailUser,
            related_name='document_artifact_interviewer',
            null=True,
            )
    people_attending = models.ManyToManyField(
            EmailUser,
            related_name='document_artifact_people_attending',
            )
    offence = models.ForeignKey(
            Offence,
            related_name='document_artifact_offence',
            null=True,
            )
    
    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_DocumentArtifact'
        verbose_name_plural = 'CM_DocumentArtifacts'

    def log_user_action(self, action, request):
        return ArtifactUserAction.log_action(self, action, request.user)

    #def send_to_manager(self, request):
    ## Prefix "DO" char to DocumentArtifact number.
    #def save(self, *args, **kwargs):
    #    
    #    super(DocumentArtifact, self).save(*args,**kwargs)
    #    if self.number is None:
    #        new_number_id = 'DO{0:06d}'.format(self.pk)
    #        self.number = new_number_id
    #        self.save()
        

class PhysicalArtifact(Artifact):
    physical_artifact_type = models.ForeignKey(
            PhysicalArtifactType,
            null=True
            )
    legal_case = models.ForeignKey(
            LegalCase,
            related_name='legal_case_physical_artifacts',
            null=True,
            )
    #_file = models.FileField(max_length=255)
    #identifier = models.CharField(max_length=255, blank=True, null=True)
    #description = models.TextField(blank=True, null=True)
    used_within_case = models.BooleanField(default=False)
    sensitive_non_disclosable = models.BooleanField(default=False)
    officer = models.ForeignKey(
            EmailUser,
            related_name='physical_artifact_officer',
            null=True,
            )
    statement = models.ForeignKey(
        DocumentArtifact, 
        related_name='physical_artifact_statement',
        on_delete=models.PROTECT, 
        blank=True, 
        null=True
        )
    #custodian = models.ForeignKey(
    #        EmailUser,
    #        related_name='physical_artifact_custodian',
    #        null=True,
    #        )
    #artifact_created_date = models.DateField(null=True)
    #artifact_created_time = models.TimeField(blank=True, null=True)
    disposal_date = models.DateField(null=True)
    disposal_details = models.TextField(blank=True, null=True)
    disposal_method = models.ForeignKey(
            PhysicalArtifactDisposalMethod,
            null=True
            )
    
    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_PhysicalArtifact'
        verbose_name_plural = 'CM_PhysicalArtifacts'

    def log_user_action(self, action, request):
        return ArtifactUserAction.log_action(self, action, request.user)

    #def send_to_manager(self, request):
    ## Prefix "PO" char to DocumentArtifact number.
    #def save(self, *args, **kwargs):
    #    
    #    super(PhysicalArtifact, self).save(*args,**kwargs)
    #    if self.number is None:
    #        new_number_id = 'PO{0:06d}'.format(self.pk)
    #        self.number = new_number_id
    #        self.save()


class ArtifactCommsLogEntry(CommunicationsLogEntry):
    artifact = models.ForeignKey(Artifact, related_name='comms_logs')

    class Meta:
        app_label = 'wildlifecompliance'


class ArtifactCommsLogDocument(Document):
    log_entry = models.ForeignKey(
        ArtifactCommsLogEntry,
        related_name='documents')
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'


class ArtifactUserAction(UserAction):
    ACTION_CREATE_ARTIFACT = "Create artifact {}"
    ACTION_SAVE_ARTIFACT = "Save artifact {}"
    #ACTION_OFFENCE = "Create Offence {}"
    #ACTION_SANCTION_OUTCOME = "Create Sanction Outcome {}"
    #ACTION_SEND_TO_MANAGER = "Send Inspection {} to Manager"
    #ACTION_CLOSE = "Close Inspection {}"
    #ACTION_PENDING_CLOSURE = "Mark Inspection {} as pending closure"
    #ACTION_REQUEST_AMENDMENT = "Request amendment for {}"
    #ACTION_ENDORSEMENT = "Inspection {} has been endorsed by {}"
    ACTION_ADD_WEAK_LINK = "Create manual link between {}: {} and {}: {}"
    ACTION_REMOVE_WEAK_LINK = "Remove manual link between {}: {} and {}: {}"
    #ACTION_MAKE_TEAM_LEAD = "Make {} team lead"
    #ACTION_ADD_TEAM_MEMBER = "Add {} to team"
    #ACTION_REMOVE_TEAM_MEMBER = "Remove {} from team"
    #ACTION_UPLOAD_INSPECTION_REPORT = "Upload Inspection Report '{}'"
    #ACTION_CHANGE_INDIVIDUAL_INSPECTED = "Change individual inspected from {} to {}"
    #ACTION_CHANGE_ORGANISATION_INSPECTED = "Change organisation inspected from {} to {}"

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, artifact, action, user):
        return cls.objects.create(
            artifact=artifact,
            who=user,
            what=str(action)
        )

    artifact = models.ForeignKey(Artifact, related_name='action_logs')


class ArtifactDocument(Document):
    artifact = models.ForeignKey(
            Artifact, 
            related_name='documents')
    _file = models.FileField(max_length=255)
    input_name = models.CharField(max_length=255, blank=True, null=True)
    # after initial submit prevent document from being deleted
    can_delete = models.BooleanField(default=True)
    version_comment = models.CharField(max_length=255, blank=True, null=True)

    def delete(self):
        if self.can_delete:
            return super(ArtifactDocument, self).delete()

    class Meta:
        app_label = 'wildlifecompliance'


class DetailsDocument(Document):
    log_entry = models.ForeignKey(
        PhysicalArtifact,
        related_name='details_documents')
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'


class StorageDocument(Document):
    log_entry = models.ForeignKey(
        PhysicalArtifact,
        related_name='storage_documents')
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'


#class LegalCaseRunningSheetArtifacts(models.Model):
#    legal_case = models.OneToOneField(
#            LegalCase,
#            related_name='running_sheet_artifacts'
#            )
#    document_artifacts = models.ManyToManyField(
#            DocumentArtifact,
#            related_name='running_sheet_document_artifacts',
#            )
#    physical_artifacts = models.ManyToManyField(
#            PhysicalArtifact,
#            related_name='running_sheet_physical_artifacts',
#            )
#
#    class Meta:
#        app_label = 'wildlifecompliance'

#import reversion
#reversion.register(LegalCaseRunningSheetEntry, follow=['user'])
#reversion.register(LegalCase)
#reversion.register(EmailUser)

