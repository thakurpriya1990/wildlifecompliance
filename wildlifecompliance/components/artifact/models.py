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
from wildlifecompliance.components.main.models import (
        CommunicationsLogEntry,
        UserAction, 
        Document,
        )
from wildlifecompliance.components.main.related_item import can_close_record
from wildlifecompliance.components.users.models import RegionDistrict, CompliancePermissionGroup
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class DocumentArtifact(models.Model):
    doc_type = models.CharField(max_length=50)
    _file = models.FileField(max_length=255)
    identifier = models.CharField(max_length=200, blank=True, null=True)
    




class Artifact(RevisionedMixin):
    document = 


import reversion
reversion.register(LegalCaseRunningSheetEntry, follow=['user'])
reversion.register(LegalCase)
reversion.register(EmailUser)
