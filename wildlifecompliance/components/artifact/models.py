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
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class Artifact(RevisionedMixin):
    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Artifact'
        verbose_name_plural = 'CM_Artifacts'
        #unique_together = ('document_type', 'version')
    #document = 

    # prop looks at doc or phys fk to determine type

    # save should prevent doc and phys fk


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


class PhysicalArtifactType(models.Model):
    artifact_type = models.CharField(max_length=50)
    details_schema = JSONField(null=True)
    storage_schema = JSONField(null=True)
    version = models.SmallIntegerField(default=1, blank=False, null=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    replaced_by = models.ForeignKey(
        'self', on_delete=models.PROTECT, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_PhysicalArtifactType'
        verbose_name_plural = 'CM_PhysicalArtifactTypes'
        unique_together = ('artifact_type', 'version')


class DocumentArtifact(Artifact):
    document_type = models.ForeignKey(
            DocumentArtifactType,
            null=True
            )
    _file = models.FileField(max_length=255)
    identifier = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    # statement??
    custodian = models.ForeignKey(
            EmailUser,
            null=True,
            )
    document_created_date = models.DateField(null=True)
    document_created_time = models.TimeField(blank=True, null=True)
    witness = models.ForeignKey(
            EmailUser,
            null=True,
            )
    # officer_taking_statement - req?
    interviewer = models.ForeignKey(
            EmailUser,
            null=True,
            )
    people_attending = models.ManyToManyField(
            EmailUser,
            null=True,
            )
    offence = models.ForeignKey(
            Offence,
            null=True,
            )
    # for officer statement
    officer = models.ForeignKey(
            EmailUser,
            null=True,
            )
    expert = models.ForeignKey(
            EmailUser,
            null=True,
            )
    
    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_DocumentArtifact'
        verbose_name_plural = 'CM_DocumentArtifacts'


class PhysicalArtifact(Artifact):
    physical_artifact_type = models.ForeignKey(
            DocumentArtifactType,
            null=True
            )
    #_file = models.FileField(max_length=255)
    identifier = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    used_within_case = models.BooleanField(default=False)
    sensitive_non_disclosable = models.BooleanField(default=False)
    officer_seizing = models.ForeignKey(
            EmailUser,
            null=True,
            )
    # statement ??
    custodian = models.ForeignKey(
            EmailUser,
            null=True,
            )
    artifact_created_date = models.DateField(null=True)
    artifact_created_time = models.TimeField(blank=True, null=True)
    # seizure notice
    _file = models.FileField(max_length=255)
    disposal_date = models.DateField(null=True)
    disposal_details = models.TextField(blank=True, null=True)
    # disposal_method = fk def in admin - simple char


    
    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_DocumentArtifact'
        verbose_name_plural = 'CM_DocumentArtifacts'

    

#import reversion
#reversion.register(LegalCaseRunningSheetEntry, follow=['user'])
#reversion.register(LegalCase)
#reversion.register(EmailUser)
