from __future__ import unicode_literals
from concurrency.exceptions import RecordModifiedError
from concurrency.fields import IntegerVersionField
from django.db import models, transaction
from django.db.utils import IntegrityError
from django.contrib.postgres.fields.jsonb import JSONField
from django.utils import timezone
from ledger.accounts.models import EmailUser, RevisionedMixin
from ledger.payments.invoice.models import Invoice
from wildlifecompliance.components.applications.models import (
    ApplicationCondition,
    Application,
    ApplicationFormDataRecord,
)
from wildlifecompliance.components.main.models import (
    CommunicationsLogEntry,
    UserAction,
    Document
)
from wildlifecompliance.components.returns.email import (
    send_external_submit_email_notification,
    send_return_accept_email_notification,
)

import logging
import reversion

logger = logging.getLogger(__name__)


def template_directory_path(instance, filename):
    """
    Static location for Returns template.
    :param instance: Request.
    :param filename: Name of file.
    :return: file path.
    """
    return 'wildlifecompliance/returns/template/{0}'.format(filename)


def update_returns_comms_log_filename(instance, filename):
    return 'wildlifecompliance/returns/{}/communications/{}/{}'.format(
        instance.log_entry.return_obj.id, instance.id, filename)


class ReturnType(models.Model):
    """
    A definition to identify the format used to facilitate Return.
    """
    FORMAT_SHEET = 'sheet'
    FORMAT_QUESTION = 'question'
    FORMAT_DATA = 'data'
    FORMAT_CHOICES = (
        (FORMAT_SHEET, 'Sheet'),
        (FORMAT_QUESTION, 'Question'),
        (FORMAT_DATA, 'Data')
    )
    # Species list for this Return Type can be regulated, application-based or
    # none.
    SPECIES_LIST_REGULATED = 'regulated'
    SPECIES_LIST_APPLICATION = 'application'
    SPECIES_LIST_NONE = 'none'
    SPECIES_LIST_CHOICES = (
        (SPECIES_LIST_REGULATED, 'Regulated Species List'),
        (SPECIES_LIST_APPLICATION, 'Application Species List'),
        (SPECIES_LIST_NONE, 'No Species List')
    )
    name = models.CharField(null=True, blank=True, max_length=100)
    description = models.TextField(null=True, blank=True, max_length=256)
    data_descriptor = JSONField()
    data_format = models.CharField(
        'Data format',
        max_length=30,
        choices=FORMAT_CHOICES,
        default=FORMAT_DATA)
    # data_template is only used by ReturnData Format for upload.
    data_template = models.FileField(
        upload_to=template_directory_path,
        null=True,
        blank=True)
    fee_required = models.BooleanField(default=False)
    # fee_amount is a base amount required for the Return Type.
    fee_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default='0')
    # fee_name is an optional field for fee and can be used to correspond to
    # JSON property.
    fee_name = models.CharField(null=True, blank=True, max_length=50)
    oracle_account_code = models.CharField(max_length=100, default='')
    replaced_by = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        blank=True,
        null=True)
    version = models.SmallIntegerField(default=1, blank=False, null=False)
    # species_list is the type of species associated with this Return Type.
    species_list = models.CharField(
        'Species List',
        max_length=30,
        choices=SPECIES_LIST_CHOICES,
        default=SPECIES_LIST_NONE)

    def __str__(self):
        return '{0} - v{1}'.format(self.name, self.version)

    class Meta:
        app_label = 'wildlifecompliance'
        unique_together = ('name', 'version')

    @property
    def resources(self):
        return self.data_descriptor.get('resources', [])

    @property
    def with_application_species(self):
        '''
        Boolean property to indicate that this return type is for a list of
        species selected when applying for licence.
        '''
        with_application_species = False

        if self.species_list == self.SPECIES_LIST_APPLICATION:
            with_application_species = True

        return with_application_species

    @property
    def with_regulated_species(self):
        '''
        Boolean property to indicate that this return type is for a list of
        regulated species applied from the questions answered when applying.
        '''
        with_regulated_species = False

        if self.species_list == self.SPECIES_LIST_REGULATED:
            with_regulated_species = True

        return with_regulated_species

    @property
    def with_no_species(self):
        '''
        Boolean property to indicate that this return type has no species
        associated.
        '''
        no_species = False

        if self.species_list == self.SPECIES_LIST_NONE:
            no_species = True

        return no_species

    def get_resource_by_name(self, name):
        for resource in self.resources:
            if resource.get('name') == name:
                return resource
        return None

    def get_schema_by_name(self, name):
        resource = self.get_resource_by_name(name)
        return resource.get('schema', {}) if resource else None


class ReturnTypeRegulatedSpecies(models.Model):
    '''
    Model object representation of Regulated Species applicable for a Return
    Type.
    '''
    return_type = models.ForeignKey(
        ReturnType,
        related_name='regulated_species',
    )
    species_name = models.CharField(max_length=100)
    species_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default='0',
    )

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'Regulated Species'
        verbose_name_plural = 'Regulated Species'

    def __str__(self):
        return '{} - {}'.format(
            self.return_type,
            self.id
        )


class Return(models.Model):
    """
    A number of requirements relating to a Licence condition recorded during
    the Licence period.
    """
    RETURN_PROCESSING_STATUS_DUE = 'due'
    RETURN_PROCESSING_STATUS_OVERDUE = 'overdue'
    RETURN_PROCESSING_STATUS_DRAFT = 'draft'
    RETURN_PROCESSING_STATUS_FUTURE = 'future'
    RETURN_PROCESSING_STATUS_WITH_CURATOR = 'with_curator'
    RETURN_PROCESSING_STATUS_ACCEPTED = 'accepted'
    RETURN_PROCESSING_STATUS_PAYMENT = 'payment'
    PROCESSING_STATUS_CHOICES = (
        (RETURN_PROCESSING_STATUS_DUE, 'Due'),
        (RETURN_PROCESSING_STATUS_OVERDUE, 'Overdue'),
        (RETURN_PROCESSING_STATUS_DRAFT, 'Draft'),
        (RETURN_PROCESSING_STATUS_FUTURE, 'Future'),
        (RETURN_PROCESSING_STATUS_WITH_CURATOR, 'With Curator'),
        (RETURN_PROCESSING_STATUS_ACCEPTED, 'Accepted'),
        (RETURN_PROCESSING_STATUS_PAYMENT, 'Awaiting Payment')
    )

    RETURN_CUSTOMER_STATUS_DUE = 'due'
    RETURN_CUSTOMER_STATUS_OVERDUE = 'overdue'
    RETURN_CUSTOMER_STATUS_DRAFT = 'draft'
    RETURN_CUSTOMER_STATUS_FUTURE = 'future'
    RETURN_CUSTOMER_STATUS_UNDER_REVIEW = 'under_review'
    RETURN_CUSTOMER_STATUS_ACCEPTED = 'accepted'
    RETURN_CUSTOMER_STATUS_DISCARD = 'discard'
    RETURN_CUSTOMER_STATUS_PAYMENT = 'payment'

    # Displayable choices for customer status.
    CUSTOMER_DISPLAYABLE_STATE = {
        RETURN_CUSTOMER_STATUS_DUE: 'Due',
        RETURN_CUSTOMER_STATUS_OVERDUE: 'Overdue',
        RETURN_CUSTOMER_STATUS_DRAFT: 'Draft',
        RETURN_CUSTOMER_STATUS_FUTURE: 'Future Submission',
        RETURN_CUSTOMER_STATUS_UNDER_REVIEW: 'Under Review',
        RETURN_CUSTOMER_STATUS_ACCEPTED: 'Accepted',
        RETURN_CUSTOMER_STATUS_DISCARD: 'Discarded',
        RETURN_CUSTOMER_STATUS_PAYMENT: 'Awaiting Payment',
    }

    # status that allow a customer to edit a Return.
    CUSTOMER_EDITABLE_STATE = [
        RETURN_PROCESSING_STATUS_DRAFT,
        RETURN_PROCESSING_STATUS_PAYMENT,
    ]

    # List of statuses from above that allow a customer to view a Return.
    # (read-only)
    CUSTOMER_VIEWABLE_STATE = [
        RETURN_PROCESSING_STATUS_WITH_CURATOR,
        RETURN_PROCESSING_STATUS_ACCEPTED
    ]

    lodgement_number = models.CharField(
        max_length=9,
        blank=True,
        default='')
    application = models.ForeignKey(
        Application,
        related_name='returns_application')
    licence = models.ForeignKey(
        'wildlifecompliance.WildlifeLicence',
        related_name='returns_licence')
    due_date = models.DateField()
    processing_status = models.CharField(
        choices=PROCESSING_STATUS_CHOICES,
        max_length=20,
        default=RETURN_PROCESSING_STATUS_FUTURE)
    assigned_to = models.ForeignKey(
        EmailUser,
        related_name='returns_curator',
        null=True,
        blank=True)
    condition = models.ForeignKey(
        ApplicationCondition,
        blank=True,
        null=True,
        related_name='returns_condition',
        on_delete=models.SET_NULL)
    lodgement_date = models.DateTimeField(blank=True, null=True)
    submitter = models.ForeignKey(
        EmailUser,
        blank=True,
        null=True,
        related_name='returns_submitter')
    reminder_sent = models.BooleanField(default=False)
    post_reminder_sent = models.BooleanField(default=False)
    return_type = models.ForeignKey(ReturnType, null=True)
    nil_return = models.BooleanField(default=False)
    comments = models.TextField(blank=True, null=True)
    return_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default='0')
    property_cache = JSONField(null=True, blank=True, default={})

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return self.lodgement_number

    def save(self, *args, **kwargs):
        self.update_property_cache(False)
        super(Return, self).save(*args, **kwargs)
        '''
        Append 'R' to Return id to generate Return lodgement number.
        '''
        if self.lodgement_number == '':
            new_lodgement_id = 'R{0:06d}'.format(self.pk)
            self.lodgement_number = new_lodgement_id
            self.save()

    def get_property_cache(self):
        '''
        Get properties which were previously resolved.
        '''
        if len(self.property_cache) == 0:
            self.update_property_cache()

        return self.property_cache

    def update_property_cache(self, save=True):
        '''
        Refresh cached properties with updated properties.
        '''
        # self.property_cache['payment_status'] = self.payment_status

        if save is True:
            self.save()

        return self.property_cache

    def get_property_cache_key(self, key):
        '''
        Get properties which were previously resolved with key.
        '''
        try:

            self.property_cache[key]

        except KeyError:
            self.update_property_cache()

        return self.property_cache

    @property
    def activity(self):
        return self.application.activity

    @property
    def title(self):
        return self.application.title

    @property
    def holder(self):
        return self.application.applicant

    @property
    def resources(self):
        return self.return_type.data_descriptor.get('resources', [])

    @property
    def format(self):
        return self.return_type.data_format

    @property
    def template(self):
        """
        Return data spreadsheet template for uploading information.
        :return: spreadsheet template format.
        """
        template = self.return_type.data_template
        return self.return_type.data_template.url if template else None

    @property
    def has_question(self):
        """
        Property defining if the Return is Question based.
        :return: Boolean
        """
        return True if self.format == ReturnType.FORMAT_QUESTION else False

    @property
    def has_data(self):
        """
        Property defining if the Return is Data based.
        :return: Boolean
        """
        return True if self.format == ReturnType.FORMAT_DATA else False

    @property
    def has_sheet(self):
        """
        Property defining if the Return is Running Sheet based.
        :return: Boolean
        """
        return True if self.format == ReturnType.FORMAT_SHEET else False

    @property
    def has_species_list(self):
        """
        Boolean Property defining if the Return has an associated species list.
        """
        return False if self.return_type.with_no_species else True

    @property
    def customer_status(self):
        """
        Property defining external status in relation to processing status.
        :return: External Status.
        """
        DUE = self.RETURN_CUSTOMER_STATUS_DUE
        OVERDUE = self.RETURN_CUSTOMER_STATUS_OVERDUE
        DRAFT = self.RETURN_CUSTOMER_STATUS_DRAFT
        FUTURE = self.RETURN_CUSTOMER_STATUS_FUTURE
        UNDER_REVIEW = self.RETURN_CUSTOMER_STATUS_UNDER_REVIEW
        ACCEPTED = self.RETURN_CUSTOMER_STATUS_ACCEPTED

        workflow_mapper = {
            self.RETURN_PROCESSING_STATUS_DUE: DUE,
            self.RETURN_PROCESSING_STATUS_OVERDUE: OVERDUE,
            self.RETURN_PROCESSING_STATUS_DRAFT: DRAFT,
            self.RETURN_PROCESSING_STATUS_FUTURE: DRAFT,
            self.RETURN_PROCESSING_STATUS_WITH_CURATOR: UNDER_REVIEW,
            self.RETURN_PROCESSING_STATUS_ACCEPTED: ACCEPTED,
            self.RETURN_PROCESSING_STATUS_PAYMENT: UNDER_REVIEW
        }

        return workflow_mapper.get(self.processing_status, FUTURE)

    @property
    def payment_status(self):
        """
        Property defining fee status for this Return.
        :return:
        """
        if not self.return_type.fee_required:
            return ReturnInvoice.PAYMENT_STATUS_NOT_REQUIRED
        else:
            if self.invoices.count() == 0:
                return ReturnInvoice.PAYMENT_STATUS_UNPAID
            else:
                try:
                    latest_invoice = Invoice.objects.get(
                        reference=self.invoices.latest('id').invoice_reference)
                except ReturnInvoice.DoesNotExist:
                    return ReturnInvoice.PAYMENT_STATUS_UNPAID
                return latest_invoice.payment_status

    @property
    def return_fee_paid(self):
        return self.payment_status in [
            ReturnInvoice.PAYMENT_STATUS_NOT_REQUIRED,
            ReturnInvoice.PAYMENT_STATUS_PAID,
            ReturnInvoice.PAYMENT_STATUS_OVERPAID,
        ]

    @property
    def has_payment(self):
        """
        Property defining if payment is required for this Return.
        :return:
        """
        has_payment = False
        if self.get_latest_invoice():
            has_payment = True

        return has_payment

    @property
    def total_paid_amount(self):
        '''
        Property defining the total fees already paid for this licence Return.
        '''
        amount = 0
        if self.invoices.count() > 0:
            for invoice in self.invoices.all():
                detail = Invoice.objects.get(
                    reference=invoice.invoice_reference
                )
                amount += detail.payment_amount
                amount -= detail.refund_amount

        return amount

    @property
    def activity_curators(self):
        '''
        QuerySet of authorised licence activity curators for this return.
        '''
        groups = self.get_permission_groups('return_curator').values_list(
            'id', flat=True
        )

        return EmailUser.objects.filter(groups__id__in=groups).distinct()

    @transaction.atomic
    def set_submitted(self, request):
        '''
        TODO:AYN This is redundant. ReturnService.
        '''
        try:
            submit_status = [
                Return.RETURN_PROCESSING_STATUS_FUTURE,
                Return.RETURN_PROCESSING_STATUS_DUE,
                Return.RETURN_PROCESSING_STATUS_OVERDUE,
                Return.RETURN_PROCESSING_STATUS_DRAFT,
            ]
            CURATOR = Return.RETURN_PROCESSING_STATUS_WITH_CURATOR
            if self.processing_status in submit_status:
                self.processing_status = CURATOR
                self.submitter = request.user
                self.save()

            # code for amendment returns is still to be added, so
            # lodgement_date is set outside if statement
            self.lodgement_date = timezone.now()
            self.save()
            # this below code needs to be reviewed
            # self.save(version_comment='Return submitted:{}'.format(self.id))
            # self.application.save(
            #   version_comment='Return submitted:{}'.format(self.id))
            self.log_user_action(
                ReturnUserAction.ACTION_SUBMIT_REQUEST.format(self), request)
            send_external_submit_email_notification(request, self)
            # send_submit_email_notification(request,self)
        except BaseException:
            raise

    def set_return_species(self):
        '''
        Set the species available for this return.
        '''
        try:
            return_table = []
            specie_names = []

            if self.return_type.with_application_species:
                specie_names = self.get_application_return_species()

            elif self.return_type.with_regulated_species:
                specie_names = self.get_regulated_return_species()

            for name in specie_names:
                return_table.append(
                    ReturnTable(name=name, ret_id=str(self.id))
                )

            if return_table:
                ReturnTable.objects.bulk_create(return_table)

        except BaseException as e:
            logger.error('set_return_speces() ID: {0} - {1}'.format(
                self.id, e
            ))

    def get_application_return_species(self):
        '''
        Set the species available for this return.
        '''
        species = []

        return species

    def get_regulated_return_species(self):
        '''
        Set the species available for this return.
        '''
        species = []

        return species

    def set_future_return_species(self):
        '''
        Set the species available for this return.
        '''
        SPECIES = ApplicationFormDataRecord.COMPONENT_TYPE_SELECT_SPECIES
        STATUS = [
            # Return.RETURN_PROCESSING_STATUS_FUTURE
            'NO SPECIES ALLOWED'
        ]

        if self.processing_status not in STATUS:
            '''
            Species are only set for FUTURE processing status.
            '''
            return

        species_qs = ApplicationFormDataRecord.objects.values(
            'value',
        ).filter(
            licence_activity_id=self.condition.licence_activity_id,
            licence_purpose_id=self.condition.licence_purpose_id,
            application_id=self.condition.application_id,
            component_type=SPECIES,
        )
        return_table = []
        specie_ids = []
        for specie_id in species_qs:
            specie_ids += specie_id['value']

        for id_name in specie_ids:
            return_table.append(
                ReturnTable(name=id_name, ret_id=str(self.id))
            )

        if return_table:
            ReturnTable.objects.bulk_create(return_table)

    def set_processing_status(self, status):
        '''
        Set the processing status for this Return.
        '''
        self.processing_status = status
        self.save()

    def set_return_fee(self, fee):
        '''
        Set the submission fee for this return.
        '''
        self.return_fee = fee
        self.save()

    def get_customer_status(self):
        '''
        Get displayable customer status.
        '''
        return self.CUSTOMER_DISPLAYABLE_STATE.get(self.customer_status)

    def get_latest_invoice(self):
        '''
        Get latest invoice for this Return.
        '''
        latest_invoice = None
        if self.invoices.count() > 0:
            try:
                latest_invoice = Invoice.objects.get(
                    reference=self.invoices.latest('id').invoice_reference)
            except Invoice.DoesNotExist:
                return None

        return latest_invoice

    def get_permission_groups(self, codename):
        '''
        Get the queryset of ActivityPermissionGroups matching this return based
        on licence activity.
        '''
        from wildlifecompliance.components.applications.models import (
            ActivityPermissionGroup
        )
        selected_activity_ids = ApplicationCondition.objects.filter(
            id=self.condition_id,
            licence_activity__isnull=False
        ).values_list('licence_activity__id', flat=True)

        if not selected_activity_ids:
            return ActivityPermissionGroup.objects.none()

        return ActivityPermissionGroup.get_groups_for_activities(
            selected_activity_ids, codename)

    @transaction.atomic
    def accept(self, request):
        '''
        TODO:AYN This is redundant. ReturnService.
        '''
        try:
            self.processing_status = Return.RETURN_PROCESSING_STATUS_ACCEPTED
            self.save()
            self.log_user_action(
                ReturnUserAction.ACTION_ACCEPT_REQUEST.format(self), request)
            send_return_accept_email_notification(self, request)
        except BaseException:
            raise

    def save_return_table(self, table_name, table_rows, request):
        """
        Persist Return Table of data to database.
        :param table_name:
        :param table_rows:
        :param request:
        :return:
        """
        try:
            # wrap atomic context here to allow natural handling of a Record
            # Modified concurrent error. (optimistic lock)
            # get the Return Table record and save immediately to check if
            # it has been concurrently modified.
            return_table, created = ReturnTable.objects.get_or_create(
                name=table_name, ret=self)
            return_table.save()
            # delete any existing rows as they will all be recreated
            return_table.returnrow_set.all().delete()
            return_rows = [
                ReturnRow(
                    return_table=return_table,
                    data=row) for row in table_rows]

            ReturnRow.objects.bulk_create(return_rows)

            # log transaction
            self.log_user_action(
                ReturnUserAction.ACTION_SAVE_REQUEST.format(self), request)

        except RecordModifiedError:
            raise IntegrityError(
                'A concurrent save occurred please refresh page details.')
        except BaseException:
            raise

    def log_user_action(self, action, request):
        return ReturnUserAction.log_action(self, action, request.user)


class ReturnActivity(models.Model):
    '''
    A model representation of a licensed stock movement activity that has
    occured on a licence return.
    '''
    from wildlifecompliance.components.licences.models import (
        WildlifeLicence,
    )
    # Activity Workflow.
    PROCESSING_STATUS_CREATE = 'create'
    PROCESSING_STATUS_TRANSFER = 'transfer'
    PROCESSING_STATUS_PAYMENT = 'payment'
    PROCESSING_STATUS_CHOICES = (
        (PROCESSING_STATUS_CREATE, 'Created'),
        (PROCESSING_STATUS_TRANSFER, 'Transferred'),
        (PROCESSING_STATUS_PAYMENT, 'Pay Transfer'),
    )
    # Activity Status.
    STATUS_COMPLETE = 'complete'
    STATUS_DECLINED = 'decline'
    STATUS_ACCEPTED = 'accept'
    STATUS_NOTIFIED = 'notify'
    STATUS_AWAITING = 'awaiting'
    STATUS_CHOICES = (
        (STATUS_COMPLETE, 'Completed'),
        (STATUS_DECLINED, 'Transfer Declined'),
        (STATUS_ACCEPTED, 'Transfer Accepted'),
        (STATUS_NOTIFIED, 'Notified Licensee'),
        (STATUS_AWAITING, 'Awaiting Payment'),
    )
    # Activity Type.
    TYPE_IN_STOCK = 'stock'
    TYPE_IN_ACQUISITION = 'in_import'
    TYPE_IN_BIRTH = 'in_birth'
    TYPE_IN_TRANSFER = 'in_transfer'
    TYPE_OUT_DISPOSAL = 'out_export'
    TYPE_OUT_DEATH = 'out_death'
    TYPE_OUT_OTHER = 'out_other'
    TYPE_OUT_DEALER = 'out_dealer'

    TYPE_DESC = {
        TYPE_IN_STOCK: 'Stock',
        TYPE_IN_BIRTH: 'In through birth',
        TYPE_IN_TRANSFER: 'In through transfer',
        TYPE_IN_ACQUISITION: 'In through acquisition',
        TYPE_OUT_DEATH: 'Out through death',
        TYPE_OUT_OTHER: 'Out through transfer',
        TYPE_OUT_DEALER: 'Out through dealer transfer',
        TYPE_OUT_DISPOSAL: 'Out through disposal',
    }

    TYPE_CHOICES = (
        (TYPE_IN_STOCK, TYPE_DESC.get(TYPE_IN_STOCK)),
        (TYPE_IN_ACQUISITION, TYPE_DESC.get(TYPE_IN_ACQUISITION)),
        (TYPE_IN_BIRTH, TYPE_DESC.get(TYPE_IN_BIRTH)),
        (TYPE_IN_TRANSFER, TYPE_DESC.get(TYPE_IN_TRANSFER)),
        (TYPE_OUT_DEATH, TYPE_DESC.get(TYPE_OUT_DEATH)),
        (TYPE_OUT_DISPOSAL, TYPE_DESC.get(TYPE_OUT_DISPOSAL)),
    )
    # Activity Type requiring fee.
    FEE_ACTIVITY_TYPE = [
        TYPE_OUT_OTHER,
    ]

    licence_return = models.ForeignKey(
        Return,
        related_name='stock_activities'
    )
    processing_status = models.CharField(
        choices=PROCESSING_STATUS_CHOICES,
        max_length=20,
        default=PROCESSING_STATUS_CREATE)
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=20,
        default=STATUS_COMPLETE)
    activity_datetime = models.DateTimeField(auto_now=True)
    activity_type = models.CharField(
        choices=TYPE_CHOICES,
        max_length=20,
        default=TYPE_IN_STOCK)
    comment = models.TextField(blank=True, null=True)
    licence = models.ForeignKey(
        WildlifeLicence,
        blank=True,
        null=True,
        related_name='receiving_licences'
    )
    stock_id = models.IntegerField(default='0')
    stock_name = models.TextField(blank=True, null=True)
    stock_quantity = models.IntegerField(default='0')
    fee = models.DecimalField(max_digits=8, decimal_places=2, default='0')

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return str('ReturnActivity {0}'.format(self.id))

    @property
    def payment_status(self):
        '''
        Property defining fee status for this return activity.
        :return: Invoice payment status.
        '''
        if self.activity_type not in self.FEE_ACTIVITY_TYPE:
            return ReturnInvoice.PAYMENT_STATUS_NOT_REQUIRED
        else:
            if self.invoices.count() == 0:
                return ReturnInvoice.PAYMENT_STATUS_UNPAID
            else:
                try:
                    latest_invoice = Invoice.objects.get(
                        reference=self.invoices.latest('id').invoice_reference)
                except ReturnInvoice.DoesNotExist:
                    return ReturnInvoice.PAYMENT_STATUS_UNPAID
                return latest_invoice.payment_status

    @property
    def activity_fee_paid(self):
        '''
        Property to indicate this activity fee has been paid.
        :return: Boolean.
        '''
        return self.payment_status in [
            ReturnInvoice.PAYMENT_STATUS_NOT_REQUIRED,
            ReturnInvoice.PAYMENT_STATUS_PAID,
            ReturnInvoice.PAYMENT_STATUS_OVERPAID,
        ]


class ReturnTable(RevisionedMixin):
    ret = models.ForeignKey(Return)
    name = models.CharField(max_length=100)
    version = IntegerVersionField()

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return str('ReturnTable {0}'.format(self.id))

    def has_rows(self):
        '''
        ::return:: boolean
        '''
        return ReturnRow.objects.filter(return_table=self).count()


class ReturnRow(RevisionedMixin):
    return_table = models.ForeignKey(ReturnTable)

    data = JSONField(blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return str('ReturnRow {0}'.format(self.id))


class ReturnUserAction(UserAction):
    ACTION_CREATE = "Lodge Return {}"
    ACTION_SUBMIT_REQUEST = "Submit Return {}"
    ACTION_ACCEPT_REQUEST = "Accept Return {}"
    ACTION_SAVE_REQUEST = "Save Return {}"
    ACTION_SUBMIT_TRANSFER = "Submit transfer of species stock from Return {}"
    ACTION_ACCEPT_TRANSFER = "Accept transfer of species stock to Return {}"
    ACTION_DECLINE_TRANSFER = "Decline transfer of species stock to Return {}"
    ACTION_ASSIGN_TO = "Assign to {}"
    ACTION_UNASSIGN = "Unassign"
    ACTION_DECLINE_REQUEST = "Decline request"
    ACTION_ID_REQUEST_AMENDMENTS = "Request amendments"
    ACTION_REMINDER_SENT = "Reminder sent for return {}"
    ACTION_STATUS_CHANGE = "Change status to Due for return {}"

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, return_obj, action, user):
        return cls.objects.create(
            return_obj=return_obj,
            who=user,
            what=str(action)
        )

    return_obj = models.ForeignKey(Return, related_name='action_logs')


class ReturnLogEntry(CommunicationsLogEntry):
    return_obj = models.ForeignKey(Return, related_name='comms_logs')

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return 'ReturnLogEntry.id: {0}'.format(self.id)

    def save(self, **kwargs):
        # save the application reference if the reference not provided
        if not self.reference:
            self.reference = self.return_obj.id
        super(ReturnLogEntry, self).save(**kwargs)


class ReturnLogDocument(Document):
    log_entry = models.ForeignKey('ReturnLogEntry', related_name='documents')
    _file = models.FileField(upload_to=update_returns_comms_log_filename)

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return 'ReturnLogDocument.id: {0}'.format(self.id)


class ReturnInvoice(models.Model):
    '''
    An model object representing an invoice for a return.
    '''
    PAYMENT_STATUS_NOT_REQUIRED = 'payment_not_required'
    PAYMENT_STATUS_UNPAID = 'unpaid'
    PAYMENT_STATUS_PARTIALLY_PAID = 'partially_paid'
    PAYMENT_STATUS_PAID = 'paid'
    PAYMENT_STATUS_OVERPAID = 'over_paid'

    invoice_return = models.ForeignKey(Return, related_name='invoices')
    invoice_reference = models.CharField(
        max_length=50, null=True, blank=True, default='')

    class Meta:
        app_label = 'wildlifecompliance'

    def __str__(self):
        return 'Return {} : Invoice #{}'.format(
            self.invoice_return.id, self.invoice_reference)

    # Properties
    # ==================
    @property
    def active(self):
        try:
            invoice = Invoice.objects.get(reference=self.invoice_reference)
            return False if invoice.voided else True
        except Invoice.DoesNotExist:
            pass
        return False


'''
NOTE: REGISTER MODELS FOR REVERSION HERE.
'''
reversion.register(
    Return,
    follow=[
        'application',
        'submitter',
        'assigned_to',
        'condition',
        'licence',
        'return_type',
        ]
    )
reversion.register(
    ReturnType,
    follow=[
        'replaced_by',
        ]
    )
reversion.register(
    ReturnTable,
    follow=[
        'ret',
        ]
    )
reversion.register(
    ReturnRow,
    follow=[
        'return_table',
        ]
    )
reversion.register(
    ReturnInvoice,
    follow=[
        'invoice_return',
        ]
    )
