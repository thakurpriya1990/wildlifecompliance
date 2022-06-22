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
        Region,
        District
        )
#from wildlifecompliance.components.users.models import CompliancePermissionGroup
from wildlifecompliance.components.offence.models import Offence, Offender
from wildlifecompliance.components.legal_case.models import (
        LegalCase,
        BriefOfEvidence,
        ProsecutionBrief
        )
from wildlifecompliance.components.artifact.email import (
    send_mail)
from wildlifecompliance.components.main.email import prepare_mail
from django.core.exceptions import ValidationError
from wildlifecompliance.components.main.utils import FakeRequest

logger = logging.getLogger(__name__)


class Artifact(RevisionedMixin):
    STATUS_ACTIVE = 'active'
    STATUS_WAITING_FOR_DISPOSAL = 'waiting_for_disposal'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = (
            (STATUS_ACTIVE, 'Active'),
            (STATUS_WAITING_FOR_DISPOSAL, 'Waiting For Disposal'),
            (STATUS_CLOSED,  'Closed'),
            )
    identifier = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    artifact_date = models.DateField(null=True)
    artifact_time = models.TimeField(blank=True, null=True)
    number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(
            max_length=100,
            choices=STATUS_CHOICES,
            default='active'
            )

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
        object_type = None
        pa = PhysicalArtifact.objects.filter(artifact_ptr_id=self.id)
        da = DocumentArtifact.objects.filter(artifact_ptr_id=self.id)
        if pa:
            object_type = 'document_artifact'
        elif da:
            object_type = 'physical_artifact'
        return object_type

    @property
    def artifact_type(self):
        pa = PhysicalArtifact.objects.filter(artifact_ptr_id=self.id)
        if pa and pa.first().physical_artifact_type and pa.first().physical_artifact_type.artifact_type:
            return pa.first().physical_artifact_type.artifact_type

        da = DocumentArtifact.objects.filter(artifact_ptr_id=self.id)
        if da and da.first().document_type:
            document_type = da.first().document_type
            display_name = ''
            for choice in DocumentArtifact.DOCUMENT_TYPE_CHOICES:
                if document_type == choice[0]:
                    display_name = choice[1]
            return display_name
        return '---'

    @property
    def get_related_items_identifier(self):
        return self.number

    @property
    def get_related_items_descriptor(self):
        return self.identifier

    def log_user_action(self, action, request=None):
        user_name = None
        if not request:
            return ArtifactUserAction.log_action(self, action)
        else:
            return ArtifactUserAction.log_action(self, action, request.user)


# TODO - no longer required
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
    FOUND_OBJECT = 'found_object'
    SEIZED_OBJECT = 'seized_object'
    SURRENDERED_OBJECT = 'surrendered_object'
    TYPE_CHOICES = (
            (FOUND_OBJECT, 'Found Object'),
            (SEIZED_OBJECT, 'Seized Object'),
            (SURRENDERED_OBJECT,  'Surrendered Object'),
            )
    artifact_type = models.CharField(max_length=50, choices=TYPE_CHOICES, blank=False, null=False, unique=True)
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
        display_name = ''
        for choice in PhysicalArtifactType.TYPE_CHOICES:
            if self.artifact_type == choice[0]:
                display_name = choice[1]
        return display_name


class PhysicalArtifactDisposalMethod(models.Model):
    disposal_method = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_PhysicalArtifactDisposalMethod'
        verbose_name_plural = 'CM_PhysicalArtifactDisposalMethods'
        #unique_together = ('artifact_type', 'version')

    def __str__(self):
        return '{}, {}'.format(self.disposal_method, self.description)


class DocumentArtifact(Artifact):
    WITNESS_STATEMENT = 'witness_statement'
    RECORD_OF_INTERVIEW = 'record_of_interview'
    OFFICER_STATEMENT = 'officer_statement'
    EXPERT_STATEMENT = 'expert_statement'
    PHOTOGRAPH = 'photograph'
    VIDEO = 'video'
    SOUND = 'sound'
    OTHER = 'other'
    DOCUMENT_TYPE_CHOICES = (
            (WITNESS_STATEMENT, 'Witness Statement'),
            (RECORD_OF_INTERVIEW, 'Record of Interview'),
            (OFFICER_STATEMENT, 'Officer Statement'),
            (EXPERT_STATEMENT, 'Expert Statement'),
            (PHOTOGRAPH, 'Photograph'),
            (VIDEO, 'Video'),
            (SOUND, 'Sound'),
            (OTHER, 'Other')
            )
    document_type = models.CharField(
            max_length=30,
            choices=DOCUMENT_TYPE_CHOICES,
            )
    legal_cases = models.ManyToManyField(
            LegalCase,
            through='DocumentArtifactLegalCases',
            through_fields=('document_artifact', 'legal_case'),
            related_name='legal_case_document_artifacts',
            )

    statement = models.ForeignKey(
        'self', 
        related_name='document_artifact_statement',
        on_delete=models.PROTECT,
        blank=True,
        null=True
        )
    person_providing_statement = models.ForeignKey(
            EmailUser,
            related_name='document_artifact_person_providing_statement',
            null=True,
            )
    officer_interviewer = models.ForeignKey(
            EmailUser,
            related_name='document_artifact_officer_interviewer',
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
    offender = models.ForeignKey(
            Offender,
            related_name='document_artifact_offender',
            null=True,
            )
    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_DocumentArtifact'
        verbose_name_plural = 'CM_DocumentArtifacts'


    @property
    def primary_legal_case(self):
        primary_case = None
        for legal_case in self.documentartifactlegalcases_set.all():
            if legal_case.primary:
                primary_case = legal_case
        return primary_case

    @property
    def primary_legal_case_id(self):
        primary_case = None
        for legal_case in self.documentartifactlegalcases_set.all():
            if legal_case.primary:
                primary_case = legal_case
        if primary_case:
            return primary_case.legal_case_id
        else:
            return None

    def close(self, request=None):
        # NOTE: close_record logic moved to can_close_legal_case
        self.status = self.STATUS_CLOSED
        self.log_user_action(
                ArtifactUserAction.ACTION_CLOSE.format(self.number),
                request)
        self.save()


class DocumentArtifactLegalCasesManager(models.Manager):
    def create_with_primary(self, legal_case_id, document_artifact_id):
        qs = DocumentArtifactLegalCases.objects.filter(document_artifact_id=document_artifact_id)
        set_primary = True
        for doc in qs:
            if doc.primary:
                set_primary = False
        link = self.create(legal_case_id=legal_case_id, document_artifact_id=document_artifact_id, primary=set_primary)
        return link


class DocumentArtifactLegalCases(models.Model):
    document_artifact = models.ForeignKey(
            DocumentArtifact,
            null=False)
    legal_case = models.ForeignKey(
            LegalCase,
            null=False)
    primary = models.BooleanField(default=False)
    objects = DocumentArtifactLegalCasesManager()

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_DocumentArtifactLegalCases'
        unique_together = ('document_artifact', 'legal_case')


class BriefOfEvidenceDocumentArtifacts(models.Model):
    legal_case = models.ForeignKey(
            LegalCase, 
            )
    document_artifact = models.ForeignKey(
            DocumentArtifact, 
            )
    ticked = models.BooleanField(default=False)

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = ('document_artifact', 'legal_case')

    @property
    def label(self):
        return self.__str__()

    def __str__(self):
        label_text = ''
        if self.document_artifact.identifier:
            label_text = self.document_artifact.identifier
        else:
            label_text = self.document_artifact.number
        return label_text

    @property
    def hyperlink(self):
        hyperlink = '/internal/object/' + str(self.document_artifact.id)
        return hyperlink


class ProsecutionBriefDocumentArtifacts(models.Model):
    legal_case = models.ForeignKey(
            LegalCase, 
            )
    document_artifact = models.ForeignKey(
            DocumentArtifact, 
            )
    ticked = models.BooleanField(default=False)

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = ('document_artifact', 'legal_case')

    @property
    def label(self):
        return self.__str__()

    def __str__(self):
        label_text = ''
        if self.document_artifact.identifier:
            label_text = self.document_artifact.identifier
        else:
            label_text = self.document_artifact.number
        return label_text

    @property
    def hyperlink(self):
        hyperlink = '/internal/object/' + str(self.document_artifact.id)
        return hyperlink


class PhysicalArtifact(Artifact):
    physical_artifact_type = models.ForeignKey(
            PhysicalArtifactType,
            null=True
            )
    legal_cases = models.ManyToManyField(
            LegalCase,
            through='PhysicalArtifactLegalCases',
            through_fields=('physical_artifact', 'legal_case'),
            related_name='legal_case_physical_artifacts',
            )
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
    custodian = models.ForeignKey(
            EmailUser,
            related_name='physical_artifact_custodian',
            null=True,
            )
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

    def add_legal_case(self, legal_case_id):
        try:
            legal_case_id_int = int(legal_case_id)
        except Exception as e:
            raise e
        legal_case = LegalCase.objects.get(id=legal_case_id_int)
        if legal_case:
            if not self.legal_case:
                self.legal_case = legal_case
                self.save()
            elif self.legal_case != legal_case:
                self.associated_legal_cases.add(legal_case)

    def dispose(self, request=None):
        print("dispose")
        disposal_date = request.data.get('disposal_date')
        disposal_method_id = request.data.get('disposal_method_id')
        disposal_details = request.data.get('disposal_details')
        self.disposal_date = disposal_date
        self.disposal_method_id = disposal_method_id
        self.disposal_details = disposal_details
        self.close(request)

    def close(self, request):
        # TODO: add logic to check for disposal date
        # NOTE: close_record logic moved to can_close_legal_case
        if not self.disposal_date:
            self.status = self.STATUS_WAITING_FOR_DISPOSAL
            email_data = prepare_mail(request=request, instance=self, workflow_entry=None, send_mail=send_mail, recipient_address=self.custodian_email)
            #prepare_mail(request=request, instance=self, workflow_entry=None, send_mail=send_mail)
            # write comms log based on email_data
            print("email_data")
            print(email_data)
            to = email_data.get('to', '')
            fromm = email_data.get('fromm', '')
            cc = email_data.get('cc', '')
            log_type = 'email'
            reference = email_data.get('reference', '')
            subject = email_data.get('subject', '')
            text = email_data.get('text', '')
            ArtifactCommsLogEntry.objects.create(
                    artifact=self,
                    to=to,
                    fromm=fromm,
                    cc=cc,
                    log_type=log_type,
                    reference=reference,
                    subject=subject,
                    text=text
                    )
            # action log
            self.log_user_action(
                    ArtifactUserAction.ACTION_WAITING_FOR_DISPOSAL.format(self.number),
                    request)
        else:
            self.status = self.STATUS_CLOSED
            # attempt to close parent
            ##
            self.log_user_action(
                    ArtifactUserAction.ACTION_CLOSE.format(self.number),
                    request)
        self.save()

    @property
    def data(self):
        """ returns a queryset of form data records attached to PhysicalArtifact (shortcut to PhysicalArtifactFormDataRecord related_name). """
        return self.form_data_records.all()

    @property
    def details_schema(self):
        if self.physical_artifact_type:
            return self.physical_artifact_type.details_schema

    @property
    def storage_schema(self):
        if self.physical_artifact_type:
            return self.physical_artifact_type.storage_schema


class PhysicalArtifactLegalCasesManager(models.Manager):
    def create_with_primary(self, legal_case_id, physical_artifact_id):
        qs = PhysicalArtifactLegalCases.objects.filter(physical_artifact_id=physical_artifact_id)
        set_primary = True
        for doc in qs:
            if doc.primary:
                set_primary = False
        link = self.create(legal_case_id=legal_case_id, physical_artifact_id=physical_artifact_id, primary=set_primary)
        return link


class PhysicalArtifactLegalCases(models.Model):
    physical_artifact = models.ForeignKey(
            PhysicalArtifact,
            null=False)
    legal_case = models.ForeignKey(
            LegalCase,
            null=False)
    primary = models.BooleanField(default=False)
    used_within_case = models.BooleanField(default=False)
    sensitive_non_disclosable = models.BooleanField(default=False)
    objects = PhysicalArtifactLegalCasesManager()

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_PhysicalArtifactLegalCases'
        unique_together = ('physical_artifact', 'legal_case')


class BriefOfEvidencePhysicalArtifacts(models.Model):
    legal_case = models.ForeignKey(
            LegalCase, 
            )
    physical_artifact = models.ForeignKey(
            PhysicalArtifact, 
            )
    ticked = models.BooleanField(default=False)
    reason_sensitive_non_disclosable = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = ('physical_artifact', 'legal_case')

    @property
    def label(self):
        return self.__str__()

    def __str__(self):
        label_text = ''
        if self.physical_artifact.identifier:
            label_text = self.physical_artifact.identifier
        else:
            label_text = self.physical_artifact.number
        return label_text

    @property
    def hyperlink(self):
        hyperlink = '/internal/object/' + str(self.physical_artifact.id)
        return hyperlink


class ProsecutionBriefPhysicalArtifacts(models.Model):
    legal_case = models.ForeignKey(
            LegalCase, 
            )
    physical_artifact = models.ForeignKey(
            PhysicalArtifact, 
            )
    ticked = models.BooleanField(default=False)
    reason_sensitive_non_disclosable = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = ('physical_artifact', 'legal_case')

    @property
    def label(self):
        return self.__str__()

    def __str__(self):
        label_text = ''
        if self.physical_artifact.identifier:
            label_text = self.physical_artifact.identifier
        else:
            label_text = self.physical_artifact.number
        return label_text

    @property
    def hyperlink(self):
        hyperlink = '/internal/object/' + str(self.physical_artifact.id)
        return hyperlink

    
@python_2_unicode_compatible
class PhysicalArtifactFormDataRecord(models.Model):

    INSTANCE_ID_SEPARATOR = "__instance-"

    ACTION_TYPE_ASSIGN_VALUE = 'value'
    ACTION_TYPE_ASSIGN_COMMENT = 'comment'

    COMPONENT_TYPE_TEXT = 'text'
    COMPONENT_TYPE_TAB = 'tab'
    COMPONENT_TYPE_SECTION = 'section'
    COMPONENT_TYPE_GROUP = 'group'
    COMPONENT_TYPE_NUMBER = 'number'
    COMPONENT_TYPE_EMAIL = 'email'
    COMPONENT_TYPE_SELECT = 'select'
    COMPONENT_TYPE_MULTI_SELECT = 'multi-select'
    COMPONENT_TYPE_TEXT_AREA = 'text_area'
    COMPONENT_TYPE_TABLE = 'table'
    COMPONENT_TYPE_EXPANDER_TABLE = 'expander_table'
    COMPONENT_TYPE_LABEL = 'label'
    COMPONENT_TYPE_RADIO = 'radiobuttons'
    COMPONENT_TYPE_CHECKBOX = 'checkbox'
    COMPONENT_TYPE_DECLARATION = 'declaration'
    COMPONENT_TYPE_FILE = 'file'
    COMPONENT_TYPE_DATE = 'date'
    COMPONENT_TYPE_CHOICES = (
        (COMPONENT_TYPE_TEXT, 'Text'),
        (COMPONENT_TYPE_TAB, 'Tab'),
        (COMPONENT_TYPE_SECTION, 'Section'),
        (COMPONENT_TYPE_GROUP, 'Group'),
        (COMPONENT_TYPE_NUMBER, 'Number'),
        (COMPONENT_TYPE_EMAIL, 'Email'),
        (COMPONENT_TYPE_SELECT, 'Select'),
        (COMPONENT_TYPE_MULTI_SELECT, 'Multi-Select'),
        (COMPONENT_TYPE_TEXT_AREA, 'Text Area'),
        (COMPONENT_TYPE_TABLE, 'Table'),
        (COMPONENT_TYPE_EXPANDER_TABLE, 'Expander Table'),
        (COMPONENT_TYPE_LABEL, 'Label'),
        (COMPONENT_TYPE_RADIO, 'Radio'),
        (COMPONENT_TYPE_CHECKBOX, 'Checkbox'),
        (COMPONENT_TYPE_DECLARATION, 'Declaration'),
        (COMPONENT_TYPE_FILE, 'File'),
        (COMPONENT_TYPE_DATE, 'Date'),
    )

    physical_artifact = models.ForeignKey(PhysicalArtifact, related_name='form_data_records')
    field_name = models.CharField(max_length=512, blank=True, null=True)
    schema_name = models.CharField(max_length=256, blank=True, null=True)
    instance_name = models.CharField(max_length=256, blank=True, null=True)
    component_type = models.CharField(
        max_length=64,
        choices=COMPONENT_TYPE_CHOICES,
        default=COMPONENT_TYPE_TEXT)
    value = JSONField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    deficiency = models.TextField(blank=True, null=True)

    def __str__(self):
        return "Physical Artifact {id} record {field}: {value}".format(
            id=self.physical_artifact_id,
            field=self.field_name,
            value=self.value[:8]
        )

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = ('physical_artifact', 'field_name',)

    @staticmethod
    def process_form(PhysicalArtifact, form_data, action=ACTION_TYPE_ASSIGN_VALUE):

        if action == PhysicalArtifactFormDataRecord.ACTION_TYPE_ASSIGN_COMMENT and\
                not can_edit_comments and not can_edit_deficiencies:
            raise Exception(
                'You are not authorised to perform this action!')
        for field_name, field_data in form_data.items():
            schema_name = field_data.get('schema_name', '')
            component_type = field_data.get('component_type', '')
            value = field_data.get('value', '')
            comment = field_data.get('comment_value', '')
            deficiency = field_data.get('deficiency_value', '')
            instance_name = ''

            if PhysicalArtifactFormDataRecord.INSTANCE_ID_SEPARATOR in field_name:
                [parsed_schema_name, instance_name] = field_name.split(
                    PhysicalArtifactFormDataRecord.INSTANCE_ID_SEPARATOR
                )
                schema_name = schema_name if schema_name else parsed_schema_name

            form_data_record, created = PhysicalArtifactFormDataRecord.objects.get_or_create(
                physical_artifact_id=PhysicalArtifact.id,
                field_name=field_name
            )
            if created:
                form_data_record.schema_name = schema_name
                form_data_record.instance_name = instance_name
                form_data_record.component_type = component_type
            if action == PhysicalArtifactFormDataRecord.ACTION_TYPE_ASSIGN_VALUE:
                form_data_record.value = value
            elif action == PhysicalArtifactFormDataRecord.ACTION_TYPE_ASSIGN_COMMENT:
                if can_edit_comments:
                    form_data_record.comment = comment
                if can_edit_deficiencies:
                    form_data_record.deficiency = deficiency
            form_data_record.save()


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


class ArtifactUserAction(models.Model):
    ACTION_CREATE_ARTIFACT = "Create object {}"
    ACTION_SAVE_ARTIFACT = "Save object {}"
    ACTION_CLOSE = "Close object {}"
    ACTION_WAITING_FOR_DISPOSAL = "Mark object {} as waiting for disposal"
    ACTION_ADD_WEAK_LINK = "Create manual link between {}: {} and {}: {}"
    ACTION_REMOVE_WEAK_LINK = "Remove manual link between {}: {} and {}: {}"
    who = models.ForeignKey(EmailUser, null=True, blank=True)
    when = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    what = models.TextField(blank=False)
    artifact = models.ForeignKey(Artifact, related_name='action_logs')
    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, artifact, action, user=None):
        return cls.objects.create(
            artifact=artifact,
            who=user,
            what=str(action)
        )



    def __str__(self):
        return "{what} ({who} at {when})".format(
            what=self.what,
            who=self.who,
            when=self.when
        )

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


class RendererDocument(Document):
    physical_artifact = models.ForeignKey(
        PhysicalArtifact,
        related_name='renderer_documents')
    _file = models.FileField(max_length=255)
    input_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        app_label = 'wildlifecompliance'


class BriefOfEvidenceOtherStatements(models.Model):
    legal_case = models.ForeignKey(
            LegalCase, 
            related_name='legal_case_boe_other_statements')
    person = models.ForeignKey(
            EmailUser,
            related_name='email_user_boe_other_statements',
            )
    statement = models.ForeignKey(
            DocumentArtifact, 
            related_name='statement_boe_other_statements',
            blank=True,
            null=True
            )
    associated_doc_artifact = models.ForeignKey(
            DocumentArtifact, 
            related_name='document_artifact_boe_other_statements', 
            blank=True, 
            null=True)
    ticked = models.BooleanField(default=False)
    children = models.ManyToManyField(
            'self',
            related_name='parents',
            symmetrical=False)


    class Meta:
        app_label = 'wildlifecompliance'

    @property
    def label(self):
        return self.__str__()

    @property
    def hyperlink(self):
        if self.associated_doc_artifact:
            hyperlink = '/internal/object/' + str(self.associated_doc_artifact.id)
        elif self.statement:
            hyperlink = '/internal/object/' + str(self.statement.id)
        else:
            hyperlink = '/internal/users/' + str(self.person.id)
        return hyperlink

    @property
    def show(self):
        show = False
        # person
        if self.children.count():
            # statement
            for child in self.children.all():
                if child.children.count():
                    # associated_doc_artifact
                    for grandchild in child.children.all():
                        if grandchild.ticked:
                            show = True
                else:
                    if child.ticked:
                        show = True
        else:
            show = self.ticked
        return show

    def __str__(self):
        label_text = ''
        if not self.statement and not self.associated_doc_artifact:
            full_name = self.person.get_full_name()
            label_text = 'Person: ' + full_name
        elif not self.associated_doc_artifact:
            if self.statement.identifier:
                label_text = self.statement.artifact_type + ': ' + self.statement.identifier
            else:
                label_text = self.statement.artifact_type + ': ' + self.statement.number
        else:
            if self.associated_doc_artifact.identifier:
                label_text = 'Associated Document Object: ' + self.associated_doc_artifact.identifier
            else:
                label_text = 'Associated Document Object: ' + self.associated_doc_artifact.number
        return label_text


class BriefOfEvidenceRecordOfInterview(models.Model):
    legal_case = models.ForeignKey(
            LegalCase, 
            related_name='legal_case_boe_roi')
    offence = models.ForeignKey(
            Offence, 
            related_name='offence_boe_roi')
    offender = models.ForeignKey(
            Offender, 
            related_name='offender_boe_roi', 
            blank=True, 
            null=True)
    record_of_interview = models.ForeignKey(
            DocumentArtifact, 
            related_name='record_of_interview_boe_roi', 
            blank=True, 
            null=True)
    associated_doc_artifact = models.ForeignKey(
            DocumentArtifact, 
            related_name='document_artifact_boe_roi', 
            blank=True, 
            null=True)
    ticked = models.BooleanField(default=False)
    children = models.ManyToManyField(
            'self',
            related_name='parents',
            symmetrical=False)

    class Meta:
        app_label = 'wildlifecompliance'

    @property
    def show(self):
        show = False
        # offence
        if self.children.count():
            # offender
            for child in self.children.all():
                if child.children.count():
                    # record_of_interview
                    for grandchild in child.children.all():
                        if grandchild.children.count():
                            # associated_doc_artifact
                            for greatgrandchild in grandchild.children.all():
                                if greatgrandchild.ticked:
                                    show = True
                        else:
                            if grandchild.ticked:
                                show = True
                else:
                    if child.ticked:
                        show = True
        else:
            show = self.ticked
        return show

    @property
    def hyperlink(self):
        hyperlink = ''
        if not self.offender and not self.record_of_interview and not self.associated_doc_artifact:
            hyperlink = '/internal/offence/' + str(self.offence.id)
        elif not self.record_of_interview and not self.associated_doc_artifact:
            if self.offender.person:
                hyperlink = '/internal/users/' + str(self.offender.person.id)
        elif not self.associated_doc_artifact:
            hyperlink = '/internal/object/' + str(self.record_of_interview.id)
        else:
            hyperlink = '/internal/object/' + str(self.associated_doc_artifact.id)
        return hyperlink

    @property
    def label(self):
        return self.__str__()

    def __str__(self):
        label_text = ''
        if not self.offender and not self.record_of_interview and not self.associated_doc_artifact:
            if self.offence.identifier:
                label_text = 'Offence: ' + self.offence.identifier
            else:
                label_text = 'Offence: ' + self.offence.lodgement_number
        elif not self.record_of_interview and not self.associated_doc_artifact:
            label_text = 'Offender: ' + str(self.offender)
        elif not self.associated_doc_artifact:
            if self.record_of_interview.identifier:
                label_text = 'Record of Interview: ' + self.record_of_interview.identifier
            else:
                label_text = 'Record of Interview: ' + self.record_of_interview.number
        else:
            if self.associated_doc_artifact.identifier:
                label_text = 'Associated Document Object: ' + self.associated_doc_artifact.identifier
            else:
                label_text = 'Associated Document Object: ' + self.associated_doc_artifact.number
        return label_text

class ProsecutionBriefOtherStatements(models.Model):
    legal_case = models.ForeignKey(
            LegalCase, 
            related_name='legal_case_pb_other_statements')
    person = models.ForeignKey(
            EmailUser,
            related_name='email_user_pb_other_statements',
            )
    statement = models.ForeignKey(
            DocumentArtifact, 
            related_name='statement_pb_other_statements',
            blank=True,
            null=True
            )
    associated_doc_artifact = models.ForeignKey(
            DocumentArtifact, 
            related_name='document_artifact_pb_other_statements', 
            blank=True, 
            null=True)
    ticked = models.BooleanField(default=False)
    children = models.ManyToManyField(
            'self',
            related_name='parents',
            symmetrical=False)


    class Meta:
        app_label = 'wildlifecompliance'

    @property
    def show(self):
        show = False
        # person
        if self.children.count():
            # statement
            for child in self.children.all():
                if child.children.count():
                    # associated_doc_artifact
                    for grandchild in child.children.all():
                        if grandchild.ticked:
                            show = True
                else:
                    if child.ticked:
                        show = True
        else:
            show = self.ticked
        return show

    @property
    def hyperlink(self):
        if self.associated_doc_artifact:
            hyperlink = '/internal/object/' + str(self.associated_doc_artifact.id)
        elif self.statement:
            hyperlink = '/internal/object/' + str(self.statement.id)
        else:
            hyperlink = '/internal/users/' + str(self.person.id)
        return hyperlink

    @property
    def label(self):
        return self.__str__()

    def __str__(self):
        label_text = ''
        if not self.statement and not self.associated_doc_artifact:
            full_name = self.person.get_full_name()
            label_text = 'Person: ' + full_name
        elif not self.associated_doc_artifact:
            if self.statement.identifier:
                label_text = self.statement.artifact_type + ': ' + self.statement.identifier
            else:
                label_text = self.statement.artifact_type + ': ' + self.statement.number
        else:
            if self.associated_doc_artifact.identifier:
                label_text = 'Associated Document Object: ' + self.associated_doc_artifact.identifier
            else:
                label_text = 'Associated Document Object: ' + self.associated_doc_artifact.number
        return label_text


class ProsecutionBriefRecordOfInterview(models.Model):
    legal_case = models.ForeignKey(
            LegalCase, 
            related_name='legal_case_pb_roi')
    offence = models.ForeignKey(
            Offence, 
            related_name='offence_pb_roi')
    offender = models.ForeignKey(
            Offender, 
            related_name='offender_pb_roi', 
            blank=True, 
            null=True)
    record_of_interview = models.ForeignKey(
            DocumentArtifact, 
            related_name='record_of_interview_pb_roi', 
            blank=True, 
            null=True)
    associated_doc_artifact = models.ForeignKey(
            DocumentArtifact, 
            related_name='document_artifact_pb_roi', 
            blank=True, 
            null=True)
    ticked = models.BooleanField(default=False)
    children = models.ManyToManyField(
            'self',
            related_name='parents',
            symmetrical=False)

    class Meta:
        app_label = 'wildlifecompliance'

    @property
    def label(self):
        return self.__str__()

    @property
    def show(self):
        show = False
        # offence
        if self.children.count():
            # offender
            for child in self.children.all():
                if child.children.count():
                    # record_of_interview
                    for grandchild in child.children.all():
                        if grandchild.children.count():
                            # associated_doc_artifact
                            for greatgrandchild in grandchild.children.all():
                                if greatgrandchild.ticked:
                                    show = True
                        else:
                            if grandchild.ticked:
                                show = True
                else:
                    if child.ticked:
                        show = True
        else:
            show = self.ticked
        return show

    @property
    def hyperlink(self):
        hyperlink = ''
        if not self.offender and not self.record_of_interview and not self.associated_doc_artifact:
            hyperlink = '/internal/offence/' + str(self.offence.id)
        elif not self.record_of_interview and not self.associated_doc_artifact:
            if self.offender.person:
                hyperlink = '/internal/users/' + str(self.offender.person.id)
        elif not self.associated_doc_artifact:
            hyperlink = '/internal/object/' + str(self.record_of_interview.id)
        else:
            hyperlink = '/internal/object/' + str(self.associated_doc_artifact.id)
        return hyperlink

    def __str__(self):
        label_text = ''
        if not self.offender and not self.record_of_interview and not self.associated_doc_artifact:
            if self.offence.identifier:
                label_text = 'Offence: ' + self.offence.identifier
            else:
                label_text = 'Offence: ' + self.offence.lodgement_number
        elif not self.record_of_interview and not self.associated_doc_artifact:
            label_text = 'Offender: ' + str(self.offender)
        elif not self.associated_doc_artifact:
            if self.record_of_interview.identifier:
                label_text = 'Record of Interview: ' + self.record_of_interview.identifier
            else:
                label_text = 'Record of Interview: ' + self.record_of_interview.number
        else:
            if self.associated_doc_artifact.identifier:
                label_text = 'Associated Document Object: ' + self.associated_doc_artifact.identifier
            else:
                label_text = 'Associated Document Object: ' + self.associated_doc_artifact.number
        return label_text


import reversion
reversion.register(Artifact, follow=['comms_logs', 'action_logs', 'documents'])
reversion.register(DocumentArtifactType, follow=['documentartifacttype_set'])
reversion.register(PhysicalArtifactType, follow=['physicalartifacttype_set', 'physicalartifact_set'])
reversion.register(PhysicalArtifactDisposalMethod, follow=['physicalartifact_set'])
#reversion.register(DocumentArtifact_people_attending, follow=[])
reversion.register(DocumentArtifact, follow=['comms_logs', 'action_logs', 'documents', 'document_artifact_statement', 'documentartifactlegalcases_set', 'briefofevidencedocumentartifacts_set', 'prosecutionbriefdocumentartifacts_set', 'physical_artifact_statement', 'statement_boe_other_statements', 'document_artifact_boe_other_statements', 'record_of_interview_boe_roi', 'document_artifact_boe_roi', 'statement_pb_other_statements', 'document_artifact_pb_other_statements', 'record_of_interview_pb_roi', 'document_artifact_pb_roi'])
reversion.register(DocumentArtifactLegalCases, follow=[])
reversion.register(BriefOfEvidenceDocumentArtifacts, follow=[])
reversion.register(ProsecutionBriefDocumentArtifacts, follow=[])
reversion.register(PhysicalArtifact, follow=['comms_logs', 'action_logs', 'documents', 'physicalartifactlegalcases_set', 'briefofevidencephysicalartifacts_set', 'prosecutionbriefphysicalartifacts_set', 'form_data_records', 'renderer_documents'])
reversion.register(PhysicalArtifactLegalCases, follow=['physical_artifact', 'legal_case'])
reversion.register(BriefOfEvidencePhysicalArtifacts, follow=[])
reversion.register(ProsecutionBriefPhysicalArtifacts, follow=[])
reversion.register(PhysicalArtifactFormDataRecord, follow=[])
reversion.register(ArtifactCommsLogEntry, follow=['documents'])
reversion.register(ArtifactCommsLogDocument, follow=[])
reversion.register(ArtifactUserAction, follow=[])
reversion.register(ArtifactDocument, follow=[])
reversion.register(RendererDocument, follow=[])
#reversion.register(BriefOfEvidenceOtherStatements_children, follow=[])
reversion.register(BriefOfEvidenceOtherStatements, follow=['parents'])
#reversion.register(BriefOfEvidenceRecordOfInterview_children, follow=[])
reversion.register(BriefOfEvidenceRecordOfInterview, follow=['parents'])
#reversion.register(ProsecutionBriefOtherStatements_children, follow=[])
reversion.register(ProsecutionBriefOtherStatements, follow=['parents'])
#reversion.register(ProsecutionBriefRecordOfInterview_children, follow=[])
reversion.register(ProsecutionBriefRecordOfInterview, follow=['parents'])
