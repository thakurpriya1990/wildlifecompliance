from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from ledger.accounts.models import RevisionedMixin, EmailUser
from wildlifecompliance.components.call_email.models import Location, CallEmail
from wildlifecompliance.components.inspection.models import Inspection
from wildlifecompliance.components.main.models import UserAction, Document, CommunicationsLogEntry
from wildlifecompliance.components.users.models import RegionDistrict, CompliancePermissionGroup
from wildlifecompliance.components.organisations.models import Organisation


class SectionRegulation(RevisionedMixin):
    act = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=50, blank=True, verbose_name='Regulation')
    offence_text = models.CharField(max_length=200, blank=True)
    amount =  models.DecimalField(max_digits=8, decimal_places=2, default='0.00')


    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Section/Regulation'
        verbose_name_plural = 'CM_Sections/Regulations'
        ordering = ('act', 'name')

    def __str__(self):
        return '{}:{}:{}'.format(self.act, self.name, self.offence_text)


class Offence(RevisionedMixin):
    WORKFLOW_CLOSE = 'close'

    STATUS_DRAFT = 'draft'
    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'
    STATUS_CLOSING = 'closing'
    STATUS_DISCARDED = 'discarded'

    EDITABLE_STATUSES = (STATUS_DRAFT, STATUS_OPEN)

    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_OPEN, 'Open'),
        (STATUS_CLOSING, 'Closing'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_DISCARDED, 'Discarded'),
    )

    identifier = models.CharField(
        max_length=50,
        blank=True,
    )
    status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default='open',
    )
    location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        related_name="offence_location",
    )
    call_email = models.ForeignKey(
        CallEmail,
        null=True,
        blank=True,
        related_name='offence_call_eamil',
    )
    inspection = models.ForeignKey(
        Inspection,
        null=True,
        blank=True,
        related_name='offence_inspection',
    )
    lodgement_number = models.CharField(max_length=50, blank=True,)
    occurrence_from_to = models.BooleanField(default=False)
    occurrence_date_from = models.DateField(null=True, blank=True)
    occurrence_time_from = models.TimeField(null=True, blank=True)
    occurrence_date_to = models.DateField(null=True, blank=True)
    occurrence_time_to = models.TimeField(null=True, blank=True)
    alleged_offences = models.ManyToManyField(
        SectionRegulation,
        blank=True,
        through='AllegedOffence',
    )
    details = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        EmailUser,
        related_name='offence_assigned_to',
        null=True
    )
    allocated_group = models.ForeignKey(
        CompliancePermissionGroup,
        related_name='offence_allocated_group',
        null=True
    )
    region = models.ForeignKey(RegionDistrict, related_name='offence_region', null=True,)
    district = models.ForeignKey(RegionDistrict, related_name='offence_district', null=True,)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Offence'
        verbose_name_plural = 'CM_Offences'

    def __str__(self):
        return 'ID: {}, Status: {}, Identifier: {}'.format(self.id, self.status, self.identifier)

    def save(self, *args, **kwargs):
        super(Offence, self).save(*args, **kwargs)
        if not self.lodgement_number:
            self.lodgement_number = 'OF{0:06d}'.format(self.pk)
            self.save()

    def log_user_action(self, action, request):
        return OffenceUserAction.log_action(self, action, request.user)

    @property
    def get_related_items_identifier(self):
        #return '{}'.format(self.identifier)
        return self.lodgement_number

    @staticmethod
    def get_compliance_permission_group(regionDistrictId, workflow_type):
        region_district = RegionDistrict.objects.filter(id=regionDistrictId)

        # 2. Determine which permission(s) is going to be apllied
        compliance_content_type = ContentType.objects.get(model="compliancepermissiongroup")
        codename = 'officer'
        if workflow_type == Offence.WORKFLOW_CLOSE:
            codename = 'officer'
            per_district = True
        else:
            # Should not reach here
            # instance.save()
            pass

        permissions = Permission.objects.filter(codename=codename, content_type_id=compliance_content_type.id)

        # 3. Find groups which has the permission(s) determined above in the regionDistrict.
        if per_district:
            groups = CompliancePermissionGroup.objects.filter(region_district__in=region_district, permissions__in=permissions)
        else:
            groups = CompliancePermissionGroup.objects.filter(permissions__in=permissions)

        return groups.first()

    @property
    def regionDistrictId(self):
        return self.district.id if self.district else self.region.id

    @property
    def get_related_items_descriptor(self):
        #return '{}, {}'.format(self.identifier, self.details)
        return self.identifier

    def close(self, request):
        self.status = self.STATUS_CLOSING
        new_group = Offence.get_compliance_permission_group(self.regionDistrictId, Offence.WORKFLOW_CLOSE)
        self.allocated_group = new_group
        self.assigned_to = None
        self.responsible_officer = request.user
        self.log_user_action(OffenceUserAction.ACTION_CLOSE.format(self.lodgement_number), request)
        self.save()


class AllegedOffence(RevisionedMixin):
    offence = models.ForeignKey(Offence, null=False,)
    section_regulation = models.ForeignKey(SectionRegulation, null=False,)
    reason_for_removal = models.TextField(blank=True)
    removed = models.BooleanField(default=False)
    removed_by = models.ForeignKey(
        EmailUser,
        null=True,
        related_name='alleged_offence_removed_by'
    )

    def __str__(self):
        return self.section_regulation.__str__()

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_AllegedOffence'
        verbose_name_plural = 'CM_AllegedOffences'


class ActiveOffenderManager(models.Manager):
    def get_queryset(self):
        return super(ActiveOffenderManager, self).get_queryset().filter(removed=False)


class Offender(models.Model):
    reason_for_removal = models.TextField(blank=True)
    removed = models.BooleanField(default=False)
    removed_by = models.ForeignKey(
        EmailUser,
        null=True,
        related_name='offender_removed_by'
    )
    person = models.ForeignKey(
        EmailUser,
        null=True,
        related_name='offender_person',
    )
    organisation = models.ForeignKey(
        Organisation,
        null=True,
        related_name='offender_organisation',
    )
    offence = models.ForeignKey(
        Offence,
        null=True,
        on_delete=models.SET_NULL,
    )
    active_offenders = ActiveOffenderManager()
    objects = models.Manager()

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Offender'
        verbose_name_plural = 'CM_Offenders'

    def __str__(self):
        if self.person:
            return 'First name: {}, Last name: {}'.format(self.person.first_name, self.person.last_name)
        else:
            return '---'

    def clean(self):
        if (self.person and self.organisation) or (not self.person and not self.organisation):
            raise ValidationError('An offender must be either a person or an organisation.')

        super(Offender, self).clean()


class OffenceUserAction(UserAction):
    ACTION_CLOSE = "Close offence: {}"
    ACTION_REMOVE_ALLEGED_OFFENCE = "Remove alleged offence: {}, Reason: {}"
    ACTION_REMOVE_OFFENDER = "Remove offender: {}, Reason: {}"
    ACTION_RESTORE_ALLEGED_OFFENCE = "Restore alleged offence: {}"
    ACTION_RESTORE_OFFENDER = "Restore offender: {}"

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, obj, action, user):
        return cls.objects.create(
            offence=obj,
            who=user,
            what=str(action)
        )

    offence = models.ForeignKey(Offence, related_name='action_logs')


class OffenceCommsLogDocument(Document):
    log_entry = models.ForeignKey('OffenceCommsLogEntry', related_name='documents')
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'


class OffenceCommsLogEntry(CommunicationsLogEntry):
    offence = models.ForeignKey(Offence, related_name='comms_logs')

    class Meta:
        app_label = 'wildlifecompliance'

