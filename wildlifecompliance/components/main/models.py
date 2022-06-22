from __future__ import unicode_literals
import logging
from datetime import datetime

from django.db import models
from django.conf import settings
from django.contrib.gis.db.models import MultiPolygonField
from django.db.models.query import QuerySet
from django.core.exceptions import ValidationError
from django.utils.encoding import python_2_unicode_compatible
from ledger.accounts.models import EmailUser
import os
from django.utils.translation import ugettext_lazy as _

from wildlifecompliance.components.section_regulation.models import Act
from wildlifecompliance.settings import SO_TYPE_CHOICES
from smart_selects.db_fields import ChainedForeignKey

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class SystemMaintenance(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def duration(self):
        """ Duration of system maintenance (in mins) """
        return int(
            (self.end_date - self.start_date).total_seconds()/60.
        ) if self.end_date and self.start_date else ''

    duration.short_description = 'Duration (mins)'

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name_plural = "System maintenance"

    def __str__(self):
        return 'System Maintenance: {} ({}) - starting {}, ending {}'.format(
            self.name, self.description, self.start_date, self.end_date
        )


@python_2_unicode_compatible
class Sequence(models.Model):

    name = models.CharField(
        verbose_name=_("name"),
        max_length=100,
        primary_key=True,
    )

    last = models.PositiveIntegerField(
        verbose_name=_("last value"),
    )

    class Meta:
        verbose_name = _("sequence")
        verbose_name_plural = _("sequences")

    def __str__(self):
        return "Sequence(name={}, last={})".format(
            repr(self.name), repr(self.last))


class Region(models.Model):
    name = models.CharField(max_length=255, unique=True)
    cddp_name = models.CharField(max_length=255, unique=True)
    head_office = models.BooleanField(default=False)
    #abbreviation = models.CharField(max_length=16, null=True, unique=True)
    #ratis_id = models.IntegerField(default=-1)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Region'
        verbose_name_plural = 'CM_Regions'


class District(models.Model):
    name = models.CharField(max_length=255, unique=True)
    cddp_name = models.CharField(max_length=255, unique=True)
    #abbreviation = models.CharField(max_length=16, null=True, unique=True)
    region = models.ForeignKey(Region, on_delete=models.PROTECT)
    #ratis_id = models.IntegerField(default=-1)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_District'
        verbose_name_plural = 'CM_Districts'


@python_2_unicode_compatible
class UserAction(models.Model):
    who = models.ForeignKey(EmailUser, null=False, blank=False)
    when = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    what = models.TextField(blank=False)

    def __str__(self):
        logger.debug('UserAction.__str__()')
        return "{what} ({who} at {when})".format(
            what=self.what,
            who=self.who,
            when=self.when
        )

    class Meta:
        abstract = True
        app_label = 'wildlifecompliance'


class CommunicationsLogEntry(models.Model):
    COMMUNICATIONS_LOG_TYPE_EMAIL = 'email'
    COMMUNICATIONS_LOG_TYPE_PHONE = 'phone'
    COMMUNICATIONS_LOG_TYPE_MAIL = 'mail'
    COMMUNICATIONS_LOG_TYPE_PERSON = 'person'
    COMMUNICATIONS_LOG_TYPE_FILE = 'file_note'
    TYPE_CHOICES = (
        (COMMUNICATIONS_LOG_TYPE_EMAIL, 'Email'),
        (COMMUNICATIONS_LOG_TYPE_PHONE, 'Phone Call'),
        (COMMUNICATIONS_LOG_TYPE_MAIL, 'Mail'),
        (COMMUNICATIONS_LOG_TYPE_PERSON, 'In Person'),
        (COMMUNICATIONS_LOG_TYPE_FILE, 'File Note')
    )

    to = models.TextField(blank=True, verbose_name="To")
    fromm = models.CharField(max_length=200, blank=True, verbose_name="From")
    cc = models.TextField(blank=True, verbose_name="cc")
    log_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=COMMUNICATIONS_LOG_TYPE_EMAIL)
    reference = models.CharField(max_length=100, blank=True)
    subject = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Subject / Description")
    text = models.TextField(blank=True)
    customer = models.ForeignKey(EmailUser, null=True, related_name='+')
    staff = models.ForeignKey(EmailUser, null=True, related_name='+')
    created = models.DateTimeField(auto_now_add=True, null=False, blank=False)

    class Meta:
        app_label = 'wildlifecompliance'


@python_2_unicode_compatible
class Document(models.Model):
    name = models.CharField(max_length=100, blank=True,
                            verbose_name='name', help_text='')
    description = models.TextField(blank=True,
                                   verbose_name='description', help_text='')
    uploaded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'wildlifecompliance'
        abstract = True

    @property
    def path(self):
        return self.file.path

    @property
    def filename(self):
        return os.path.basename(self.path)

    def __str__(self):
        return self.name or self.filename


# Extensions for Django's QuerySet

def computed_filter(self, **kwargs):
    kwargs['__filter'] = True
    return self.computed_filter_or_exclude(**kwargs)


def computed_exclude(self, **kwargs):
    kwargs['__filter'] = False
    return self.computed_filter_or_exclude(**kwargs)


def computed_filter_or_exclude(self, **kwargs):
    do_filter = kwargs.pop('__filter', True)
    matched_pk_list = [item.pk for item in self for (field, match) in map(
        lambda arg: (arg[0].replace('__in', ''),
                     arg[1] if isinstance(arg[1], (list, QuerySet)) else [arg[
                         1]]
                     ), kwargs.items()
    ) if getattr(item, field) in match]
    return self.filter(pk__in=matched_pk_list) if do_filter else self.exclude(
        pk__in=matched_pk_list)


queryset_methods = {
    'computed_filter': computed_filter,
    'computed_exclude': computed_exclude,
    'computed_filter_or_exclude': computed_filter_or_exclude,
}


for method_name, method in queryset_methods.items():
    setattr(QuerySet, method_name, method)


class TemporaryDocumentCollection(models.Model):
    # input_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        app_label = 'wildlifecompliance'


# temp document obj for generic file upload component
class TemporaryDocument(Document):
    temp_document_collection = models.ForeignKey(
        TemporaryDocumentCollection,
        related_name='documents')
    _file = models.FileField(max_length=255)
    # input_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        app_label = 'wildlifecompliance'


class GlobalSettings(models.Model):
    LICENCE_RENEW_DAYS = 'licence_renew_days'

    keys = (
        ('document_object_disposal_period', 'Document Object Disposal Period'),
        (LICENCE_RENEW_DAYS, 'Licence Renewal Period Days'),
        ('physical_object_disposal_period', 'Physical Object Disposal Period'),
    )

    key = models.CharField(
        max_length=255, choices=keys, blank=False, null=False, unique=True)
    value = models.CharField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name_plural = 'Global Settings'

    def __str__(self):
        return "{}, {}".format(self.key, self.value)


class ComplianceManagementEmailUser(EmailUser):
    class Meta:
        app_label = 'wildlifecompliance'
        proxy = True

    @property
    def get_related_items_identifier(self):
        return self.email

    @property
    def get_related_items_descriptor(self):
        return self.get_full_name()


def update_sanction_outcome_word_filename(instance, filename):
    cur_time = datetime.now().strftime('%Y%m%d_%H_%M') 
    new_filename = 'sanction_outcome_template_{}'.format(cur_time)
    return 'sanction_outcome_template/{}.docx'.format(new_filename)


class SanctionOutcomeWordTemplate(models.Model):
    sanction_outcome_type = models.CharField(max_length=30, choices=SO_TYPE_CHOICES, blank=True,)
    act = models.CharField(max_length=30, choices=Act.NAME_CHOICES, blank=True,)
    _file = models.FileField(upload_to=update_sanction_outcome_word_filename, max_length=255)
    uploaded_date = models.DateTimeField(auto_now_add=True, editable=False)
    description = models.TextField(blank=True, verbose_name='description', help_text='')

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name_plural = 'Wildlife Compliance Templates'
        ordering = ['-id']

    def __str__(self):
        return "Version: {}, {}".format(self.id, self._file.name)


class DistrictGIS(models.Model):
    wkb_geometry = MultiPolygonField(srid=4326, blank=True, null=True)
    district_name = models.CharField(max_length=200, blank=True, null=True)
    office = models.CharField(max_length=200, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['object_id', ]
        app_label = 'wildlifecompliance'

    def __str__(self):
        return "{}: {}".format(self.id, self.district_name)


class RegionGIS(models.Model):
    wkb_geometry = MultiPolygonField(srid=4326, blank=True, null=True)
    region_name = models.CharField(max_length=200, blank=True, null=True)
    office = models.CharField(max_length=200, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['object_id', ]
        app_label = 'wildlifecompliance'

    def __str__(self):
        return "{}: {}".format(self.id, self.region_name)


class ComplianceManagementSystemGroup(models.Model):

    #name = models.CharField(max_length=150, unique=True)
    name = models.CharField(
        max_length=200,
        choices=settings.GROUP_NAME_CHOICES)
    region = models.ForeignKey(Region, null=True, on_delete=models.PROTECT)
    district = ChainedForeignKey(
            District, 
            on_delete=models.PROTECT,
            chained_field='region',
            chained_model_field='region',
            show_all=False,
            null=True,
            )
    group_email = models.CharField(max_length=100, blank=True)

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = [['name', 'region', 'district']]
        verbose_name = 'CM_Compliance Management System Group'
        verbose_name_plural = 'CM_Compliance Management System Groups'

    def __str__(self):
        return "{}, {}, {}".format(self.get_name_display(), self.region, self.district)

    def get_members(self):
        return [perm.emailuser for perm in self.compliancemanagementsystemgrouppermission_set.all()]

    def add_member(self, user):
        ComplianceManagementSystemGroupPermission.objects.create(group=self,emailuser=user)


class ComplianceManagementSystemGroupPermission(models.Model):
    group = models.ForeignKey(ComplianceManagementSystemGroup, on_delete=models.PROTECT)
    emailuser = models.ForeignKey(EmailUser, on_delete=models.PROTECT, blank=True, null=True, db_constraint=False)
    active = models.BooleanField(default=True)

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return str(self.group)


def get_group_members(workflow_type, region_id=None, district_id=None):
    if workflow_type == 'forward_to_regions':
        #return CallEmailTriageGroup.objects.get(region_id=region_id, district_id=district_id).members
        return ComplianceManagementSystemGroup.objects.get(name=settings.GROUP_CALL_EMAIL_TRIAGE, region_id=region_id, district_id=district_id).get_members()
    elif workflow_type == 'forward_to_wildlife_protection_branch':
        return ComplianceManagementSystemGroup.objects.get(name=settings.GROUP_CALL_EMAIL_TRIAGE, region=Region.objects.get(head_office=True)).get_members()
    #elif workflow_type == 'allocate_for_follow_up':
    #    return OfficerGroup.objects.get(region_id=region_id, district_id=district_id).members
    #elif workflow_type == 'allocate_for_inspection':
    #    return OfficerGroup.objects.get(region_id=region_id, district_id=district_id).members
    #elif workflow_type == 'allocate_for_case':
    #    return OfficerGroup.objects.get(region_id=region_id, district_id=district_id).members


import reversion
reversion.register(SystemMaintenance, follow=[])
reversion.register(Region, follow=[])
reversion.register(CommunicationsLogEntry, follow=[])
reversion.register(TemporaryDocumentCollection, follow=['documents'])
reversion.register(TemporaryDocument, follow=[])
reversion.register(GlobalSettings, follow=[])
reversion.register(SanctionOutcomeWordTemplate, follow=[])

