import datetime
import logging

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from ledger.accounts.models import EmailUser, RevisionedMixin
from rest_framework import serializers

from wildlifecompliance.components.main.models import Document, CommunicationsLogEntry, Region, District
from wildlifecompliance.components.main.related_item import can_close_record
from wildlifecompliance.components.offence.models import Offence, Offender, AllegedOffence
from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDateConfiguration
from wildlifecompliance.components.sanction_outcome_due.serializers import SaveSanctionOutcomeDueDateSerializer
from wildlifecompliance.components.section_regulation.models import SectionRegulation
#from wildlifecompliance.components.users.models import CompliancePermissionGroup
from wildlifecompliance.components.wc_payments.models import InfringementPenalty
from wildlifecompliance.management.classes.unpaid_infringement_file import UnpaidInfringementFileBody
from wildlifecompliance.settings import SO_TYPE_CHOICES, SO_TYPE_INFRINGEMENT_NOTICE, SO_TYPE_CAUTION_NOTICE, \
    SO_TYPE_LETTER_OF_ADVICE, SO_TYPE_REMEDIATION_NOTICE

logger = logging.getLogger(__name__)


class SanctionOutcomeActiveManager(models.Manager):
    def get_queryset(self):
        return super(SanctionOutcomeActiveManager, self).get_queryset().exclude(
            Q(status=SanctionOutcome.STATUS_CLOSED) |
            Q(status=SanctionOutcome.STATUS_WITHDRAWN) |
            Q(status=SanctionOutcome.STATUS_DECLINED)
        )


class SanctionOutcomeExternalManager(models.Manager):
    def get_queryset(self):
        return super(SanctionOutcomeExternalManager, self).get_queryset().filter(
            (
                (Q(offender__isnull=False) & Q(offender__removed=False) & Q(registration_holder__isnull=True) & Q(driver__isnull=True)) |
                (Q(offender__isnull=True) & Q(registration_holder__isnull=False) & Q(driver__isnull=True)) |
                (Q(offender__isnull=True) & Q(driver__isnull=False))
            ) &
            Q(status__in=SanctionOutcome.STATUSES_FOR_EXTERNAL))


class SanctionOutcome(models.Model):
    # Workflow
    WORKFLOW_SEND_TO_MANAGER = 'send_to_manager'
    WORKFLOW_ENDORSE = 'endorse'
    WORKFLOW_DECLINE = 'decline'
    WORKFLOW_WITHDRAW_BY_MANAGER = 'withdraw_by_manager'
    WORKFLOW_WITHDRAW_BY_BRANCH_MANAGER = 'withdraw_by_branch_manager'
    WORKFLOW_ESCALATE_FOR_WITHDRAWAL = 'escalate_for_withdrawal'  # INC: infringement notice coordinator
    WORKFLOW_RETURN_TO_OFFICER = 'return_to_officer'
    WORKFLOW_RETURN_TO_INFRINGEMENT_NOTICE_COORDINATOR = 'return_to_infringement_notice_coordinator'
    WORKFLOW_MARK_DOCUMENT_POSTED = 'mark_document_posted'
    WORKFLOW_CLOSE = 'close'

    PAYMENT_STATUS_PARTIALLY_PAID = 'partially_paid'
    PAYMENT_STATUS_UNPAID = 'unpaid'
    PAYMENT_STATUS_PAID = 'paid'
    PAYMENT_STATUS_OVER_PAID = 'over_paid'
    PAYMENT_STATUS_CHOICES = (
        (PAYMENT_STATUS_UNPAID, 'Unpaid'),
        (PAYMENT_STATUS_PARTIALLY_PAID, 'Partially Paid'),
        (PAYMENT_STATUS_PAID, 'Paid'),
        (PAYMENT_STATUS_OVER_PAID, 'Over Paid'),
    )

    # Status
    STATUS_DRAFT = 'draft'
    STATUS_AWAITING_ENDORSEMENT = 'awaiting_endorsement'
    STATUS_AWAITING_PAYMENT = 'awaiting_payment'
    STATUS_AWAITING_PRINT_AND_POST = 'awaiting_print_and_post'
    STATUS_AWAITING_REVIEW = 'awaiting_review'
    STATUS_AWAITING_REMEDIATION_ACTIONS = 'awaiting_remediation_actions'
    STATUS_ESCALATED_FOR_WITHDRAWAL = 'escalated_for_withdrawal'
    STATUS_DECLINED = 'declined'
    STATUS_OVERDUE = 'overdue'
    STATUS_WITHDRAWN = 'withdrawn'
    STATUS_PENDING_CLOSURE = 'pending_closure'
    STATUS_CLOSED = 'closed'
    STATUS_WITH_DOT = 'with_dot'
    STATUS_AWAITING_ISSUANCE = 'awaiting_issuance'
    STATUS_CHOICES_FOR_EXTERNAL = (
        (STATUS_AWAITING_PAYMENT, 'Awaiting Payment'),
        (STATUS_AWAITING_REMEDIATION_ACTIONS, 'Awaiting Remediation Actions'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_CLOSED, 'closed'),
    )
    FINAL_STATUSES = (STATUS_DECLINED,
                      STATUS_CLOSED,
                      STATUS_WITHDRAWN,)
    STATUSES_FOR_EXTERNAL = (STATUS_AWAITING_PAYMENT,
                             STATUS_AWAITING_REMEDIATION_ACTIONS,
                             STATUS_OVERDUE,
                             STATUS_CLOSED)
    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_AWAITING_ENDORSEMENT, 'Awaiting Endorsement'),
        (STATUS_AWAITING_PAYMENT, 'Awaiting Payment'),  # TODO: implement pending closuer of SanctionOutcome with type RemediationActions
                                                        # This is pending closure status
        (STATUS_AWAITING_PRINT_AND_POST, 'Awaiting Print and Post'),
        (STATUS_WITH_DOT, 'With Dep. of Transport'),
        (STATUS_AWAITING_ISSUANCE, 'Awaiting Issuance'),
        (STATUS_AWAITING_REVIEW, 'Awaiting Review'),
        (STATUS_AWAITING_ISSUANCE, 'Awaiting Issuance'),
        (STATUS_AWAITING_REMEDIATION_ACTIONS, 'Awaiting Remediation Actions'),  # TODO: implement pending closuer of SanctionOutcome with type RemediationActions
                                                                                # This is pending closure status
                                                                                # Once all the remediation actions are closed, this status should become closed...
        (STATUS_ESCALATED_FOR_WITHDRAWAL, 'Escalated for Withdrawal'),
        (STATUS_DECLINED, 'Declined'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_WITHDRAWN, 'Withdrawn'),
        (STATUS_CLOSED, 'Closed'),
    )

    __original_status = STATUS_DRAFT

    type = models.CharField(max_length=30, choices=SO_TYPE_CHOICES, blank=True,)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default=__original_status,)
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, blank=True,)  # This value should always reflect ledger invoice.payment_status
                                                                                                   # Ref: functions for endorsement and post_save function in the wc_payment/utils.py

    #region = models.ForeignKey(Region, related_name='sanction_outcome_region', null=True,)
    #district = models.ForeignKey(District, related_name='sanction_outcome_district', null=True,)

    identifier = models.CharField(max_length=50, blank=True,)
    lodgement_number = models.CharField(max_length=50, blank=True,)
    offence = models.ForeignKey(Offence, related_name='offence_sanction_outcomes', null=True, on_delete=models.SET_NULL,)
    offender = models.ForeignKey(Offender, related_name='sanction_outcome_offender', null=True, on_delete=models.SET_NULL,)  # This could be registration_holder...?

    # TODO: this field is probably not used anymore.
    alleged_offences = models.ManyToManyField(SectionRegulation, blank=True, related_name='sanction_outcome_alleged_offences')

    alleged_committed_offences = models.ManyToManyField(AllegedOffence, related_name='sanction_outcome_alleged_committed_offences', through='AllegedCommittedOffence')
    issued_on_paper = models.BooleanField(default=False) # This is always true when type is letter_of_advice
    paper_id = models.CharField(max_length=50, blank=True,)
    description = models.TextField(blank=True)

    assigned_to = models.ForeignKey(EmailUser, related_name='sanction_outcome_assigned_to', null=True)
    #allocated_group = models.ForeignKey(CompliancePermissionGroup, related_name='sanction_outcome_allocated_group', null=True)
    # This field is used as recipient when manager returns a sanction outcome for amendment
    # Updated whenever the sanction outcome is sent to the manager
    responsible_officer = models.ForeignKey(EmailUser, related_name='sanction_outcome_responsible_officer', null=True)

    registration_number = models.CharField(max_length=10, blank=True)
    registration_holder = models.ForeignKey(EmailUser, related_name='sanction_outcome_registration_holder', blank=True, null=True)
    driver = models.ForeignKey(EmailUser, related_name='sanction_outcome_driver', blank=True, null=True)

    # Only editable when issued on paper. Otherwise pre-filled with date/time when issuing electronically.
    date_of_issue = models.DateField(null=True, blank=True)
    time_of_issue = models.TimeField(null=True, blank=True)

    # Following attributes should be determined at the moment of issue
    penalty_amount_1st = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    penalty_amount_2nd = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    due_date_extended_max = models.DateField(null=True, blank=True)

    # This field is used once infringement notice gets overdue
    fer_case_number = models.CharField(max_length=11, blank=True)
    infringement_penalty = models.OneToOneField(InfringementPenalty, null=True, blank=True, related_name='sanction_outcome')

    objects = models.Manager()
    objects_active = SanctionOutcomeActiveManager()
    objects_for_external = SanctionOutcomeExternalManager()

    # @property
    # def payment_status(self):
    #     ret = ''
    #     if self.infringement_penalty:
    #         ipi = self.infringement_penalty.infringement_penalty_invoices.all().last()
    #         if ipi:
    #             if ipi.ledger_invoice:
    #                 ret = ipi.ledger_invoice.payment_status
    #
    #     # Update status if ledger invoice's payment_status is 'paid'
    #     if ret == 'paid' and self.status != SanctionOutcome.STATUS_CLOSED:
    #         self.status = SanctionOutcome.STATUS_CLOSED
    #         self.save()
    #
    #     if ret == '' and self.status == SanctionOutcome.STATUS_AWAITING_PAYMENT:
    #         ret = 'unpaid'
    #
    #     return ret

    def can_close_record(self):
        can_close_record = True

        for ra in self.remediation_actions.all():
            if ra.status not in RemediationAction.FINAL_STATUSES:
                can_close_record = False
                break

        return can_close_record

    def close(self, request=None):
        print('SanctionOutcome.close() called')
        if self.can_close_record():
            self.status = self.STATUS_CLOSED
            self.log_user_action(SanctionOutcomeUserAction.ACTION_CLOSE.format(self.lodgement_number), request)
        else:
            self.status = self.STATUS_PENDING_CLOSURE
            self.log_user_action(SanctionOutcomeUserAction.ACTION_PENDING_CLOSURE.format(self.lodgement_number), request)
        self.save()

    @property
    def is_parking_offence(self):
        is_parking_offence = False

        if self.type == SO_TYPE_INFRINGEMENT_NOTICE:
            qs_allegedCommittedOffences = AllegedCommittedOffence.objects.filter(sanction_outcome=self)
            for aco in qs_allegedCommittedOffences:
                if aco.included and aco.alleged_offence.section_regulation.is_parking_offence:
                    is_parking_offence = True

        return is_parking_offence

    def get_content_for_uin(self):
        offender = self.get_offender()[0]
        uin = UnpaidInfringementFileBody()
        uin.offenders_surname.set(offender.last_name)
        uin.offenders_other_names.set(offender.first_name)
        uin.offenders_date_of_birth.set(offender.dob)
        uin.offenders_sid.set('')
        uin.offenders_organisation_name.set(offender.organisation)
        uin.party_indicator.set('I')
        uin.offenders_gender.set('U')
        uin.offenders_address_line_1.set(offender.residential_address.line1) if offender.residential_address else uin.offenders_address_line_1.set('')
        uin.offenders_address_line_2.set(offender.residential_address.line2) if offender.residential_address else uin.offenders_address_line_2.set('')
        uin.offenders_address_line_3.set(offender.residential_address.line3) if offender.residential_address else uin.offenders_address_line_3.set('')
        uin.offenders_address_line_4.set('')
        uin.offenders_suburb.set(offender.residential_address.locality) if offender.residential_address else uin.offenders_suburb.set('')
        uin.offenders_state.set(offender.residential_address.state) if offender.residential_address else uin.offenders_state.set('')
        uin.offenders_postcode.set(offender.residential_address.postcode) if offender.residential_address else uin.offenders_postcode.set('')
        uin.offenders_country.set(offender.residential_address.country.name) if offender.residential_address else uin.offenders_country.set('')
        uin.date_address_known_to_be_current.set('')
        uin.acn.set('')
        uin.infringement_number.set(self.lodgement_number)
        uin.offence_datetime.set(self.offence_occurrence_datetime)
        uin.offence_location.set(self.offence.location.__str__())
        uin.drivers_licence_number.set('')
        uin.vehicle_registration_number.set('')
        uin.offence_code.set(self.dotag_offence_code)
        uin.penalty_amount.set(self.penalty_amount_2nd)
        uin.infringement_issue_date.set(self.date_of_issue)
        uin.final_demand_letter_date.set('')
        uin.zone_speed_limit.set('')
        uin.speed_reading.set('')
        uin.first_additional_cost_code.set('')
        uin.first_additional_amount.set('')
        uin.second_additional_cost_code.set('')
        uin.second_additional_amount.set('')

        ret_text = uin.get_content()

        return ret_text

    def retrieve_alleged_committed_offences(self):
        # Check if there are new alleged offences added to the offence which this sanction outcome belongs to.
        # If sanction outcome is in the draft status and new alleged offences have been added to the offence
        # those alleged offences should be added to the sanction outcome, too.
        if self.status == SanctionOutcome.STATUS_DRAFT:
            ao_ids_already_included = AllegedCommittedOffence.objects.filter(sanction_outcome=self).values_list(
                'alleged_offence__id', flat=True)
            # Only when sanction outcome is in draft status, newly added alleged offence should be added
            # Query newly added alleged offence which is not included yet
            # However whenever new alleged offence is added to the offence, it should be added to the sanction outcomes under the offence at the moment.
            qs_allegedOffences = AllegedOffence.objects.filter(Q(offence=self.offence) & Q(removed=False)).exclude(Q(id__in=ao_ids_already_included))
            for ao in qs_allegedOffences:
                aco = AllegedCommittedOffence.objects.create(included=False, alleged_offence=ao, sanction_outcome=self)

        return AllegedCommittedOffence.objects.filter(sanction_outcome=self)

    @property
    def ledger_invoice(self):
        try:
            infringement_penalty = self.infringement_penalties.all().last()
            if infringement_penalty:
                return infringement_penalty.invoice

        except Exception as e:
            return None

    def get_offender(self):
        # Priority driver > resigtration_holder > offender
        if self.driver:
            return self.driver, 'driver'
        elif self.registration_holder:
            return self.registration_holder, 'registration_holder'
        elif self.offender:
            return self.offender.person, 'offender'
        else:
            print('SanctionOutcome: ' + self.lodgement_number + ' has no offenders.')
            return None, ''

    @property
    def prefix_lodgement_nubmer(self):
        prefix_lodgement = ''
        if self.type == SO_TYPE_INFRINGEMENT_NOTICE:
            prefix_lodgement = 'IF'
        elif self.type == SO_TYPE_LETTER_OF_ADVICE:
            prefix_lodgement = 'LA'
        elif self.type == SO_TYPE_CAUTION_NOTICE:
            prefix_lodgement = 'CN'
        elif self.type == SO_TYPE_REMEDIATION_NOTICE:
            prefix_lodgement = 'RN'

        return prefix_lodgement

    def delete(self):
        if self.lodgement_number:
            raise ValidationError('Sanction outcome saved in the database with the logement number cannot be deleted.')

        raise ValidationError('Sanction outcome cannot be deleted.')
        # super(SanctionOutcome, self).delete()

    def log_user_action(self, action, request=None):
        if request:
            return SanctionOutcomeUserAction.log_action(self, action, request.user)
        else:
            return SanctionOutcomeUserAction.log_action(self, action)

    def save(self, *args, **kwargs):
        super(SanctionOutcome, self).save(*args, **kwargs)

        need_save = False

        # Construct lodgement_number
        if not self.lodgement_number:
            self.lodgement_number = self.prefix_lodgement_nubmer + '{0:06d}'.format(self.pk)
            need_save = True

        # No documents are attached when issued_on_paper=False
        if not self.issued_on_paper:
            if self.documents.all().count():
                print('[Warn] This sanction outcome has not been issued on paper, but has documents.')
                # self.documents.all().delete()
                # need_save = True

        if need_save:
            self.save()  # Be carefull, this might lead to the infinite loop

        self.__original_status = self.status

    def __str__(self):
        return 'ID: {}, Type : {}, Identifier: {}'.format(self.id, self.type, self.identifier)
    
    @property
    def get_related_items_identifier(self):
        #return self.identifier
        return self.lodgement_number

    @property
    def get_related_items_descriptor(self):
        #return '{0}, {1}'.format(self.identifier, self.description)
        return self.identifier

    @property
    def regionDistrictId(self):
        return self.district.id if self.district else self.region.id

    @property
    def regionDistrictName(self):
        return self.district.display_name if self.district else self.region.display_name

    @staticmethod
    # Rewrite for Region District models
    def get_compliance_permission_group(regionDistrictId, workflow_type):
        #region_district = RegionDistrict.objects.filter(id=regionDistrictId)

        # 2. Determine which permission(s) is going to be apllied
        compliance_content_type = ContentType.objects.get(model="compliancepermissiongroup")
        codename = 'officer'
        if workflow_type == SanctionOutcome.WORKFLOW_SEND_TO_MANAGER:
            codename = 'manager'
            per_district = True
        elif workflow_type == SanctionOutcome.WORKFLOW_DECLINE:
            codename = '---'
            per_district = False
        elif workflow_type == SanctionOutcome.WORKFLOW_ENDORSE:
            codename = 'infringement_notice_coordinator'
            per_district = False
        elif workflow_type == SanctionOutcome.WORKFLOW_MARK_DOCUMENT_POSTED:
            codename = 'officer'
            per_district = True
        elif workflow_type == SanctionOutcome.WORKFLOW_RETURN_TO_OFFICER:
            codename = 'officer'
            per_district = True
        elif workflow_type == SanctionOutcome.WORKFLOW_ESCALATE_FOR_WITHDRAWAL:
            codename = 'manager'
            # Manager group in Kensington is the branch manager group
            #region_district = RegionDistrict.objects.filter(district=RegionDistrict.DISTRICT_KENSINGTON)
            per_district = True
        elif workflow_type == SanctionOutcome.WORKFLOW_WITHDRAW_BY_MANAGER:
            codename = 'manager'
            per_district = True
        elif workflow_type == SanctionOutcome.WORKFLOW_CLOSE:
            codename = '---'
            per_district = False
        elif workflow_type == SanctionOutcome.WORKFLOW_WITHDRAW_BY_BRANCH_MANAGER:
            codename = 'manager'
            # Manager group in Kensington is the branch manager group
            #region_district = RegionDistrict.objects.filter(district=RegionDistrict.DISTRICT_KENSINGTON)
            per_district = True
        elif workflow_type == SanctionOutcome.WORKFLOW_RETURN_TO_INFRINGEMENT_NOTICE_COORDINATOR:
            codename = 'infringement_notice_coordinator'
            per_district = False
        else:
            # Should not reach here
            # instance.save()
            pass

        permissions = Permission.objects.filter(codename=codename, content_type_id=compliance_content_type.id)

        ## 3. Find groups which has the permission(s) determined above in the regionDistrict.
        #if per_district:
        #    groups = CompliancePermissionGroup.objects.filter(region_district__in=region_district, permissions__in=permissions)
        #else:
        #    groups = CompliancePermissionGroup.objects.filter(permissions__in=permissions)

        return groups.first()

    def send_to_manager(self, request):
        if self.issued_on_paper:
            self.status = self.STATUS_AWAITING_ENDORSEMENT
        else:
            self.status = self.STATUS_AWAITING_REVIEW
        new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_SEND_TO_MANAGER)
        self.allocated_group = new_group
        self.assigned_to = None
        self.responsible_officer = request.user
        self.log_user_action(SanctionOutcomeUserAction.ACTION_SEND_TO_MANAGER.format(self.lodgement_number), request)
        self.save()

    @property
    def issue_due_date_window(self):
        qs_aco = AllegedCommittedOffence.objects.filter(Q(sanction_outcome=self) & Q(included=True))
        if qs_aco.count() != 1:  # Only infringement notice can have penalty. Infringement notice can have only one alleged offence.
            raise ValidationError('There are multiple alleged committed offences in this sanction outcome.')
        else:
            return qs_aco.first().issue_due_date_window

    @property
    def dotag_offence_code(self):
        qs_aco = AllegedCommittedOffence.objects.filter(Q(sanction_outcome=self) & Q(included=True))
        if qs_aco.count() != 1:  # Only infringement notice can have penalty. Infringement notice can have only one alleged offence.
            raise ValidationError('There are multiple alleged committed offences in this sanction outcome.')
        else:
            return qs_aco.first().dotag_offence_code

    @property
    def offence_occurrence_date(self):
        return self.offence.offence_occurrence_datetime.date()

    @property
    def offence_occurrence_datetime(self):
        return self.offence.offence_occurrence_datetime

    def confirm_date_time_issue(self, raise_exception=False):
        current_datetime = datetime.datetime.now()
        if self.issued_on_paper:
            if not self.date_of_issue:
                if raise_exception:
                    raise ValidationError('Sanction outcome cannot be endorsed without setting date of issue.')
        else:
            self.date_of_issue = current_datetime.date()
            self.time_of_issue = current_datetime.time()

    def is_issuable(self, raise_exception=False):
        date_window = self.issue_due_date_window
        if not date_window:
            raise serializers.ValidationError('Issue-due-date-window for the Section/Regulation must be set.')
        issue_due_date = self.offence_occurrence_date + relativedelta(days=date_window)

        today = datetime.date.today()

        if today > issue_due_date:
            if raise_exception:
                raise serializers.ValidationError('Infringement notice must be issued before %s' % issue_due_date.strftime("%d-%m-%Y"))
            else:
                return False
        else:
            return True

    def send_to_inc(self):
        if self.type == SO_TYPE_INFRINGEMENT_NOTICE:
            # if self.is_issuable(raise_exception=True):
            self.status = SanctionOutcome.STATUS_WITH_DOT
            new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_ENDORSE)
            self.allocated_group = new_group
            self.save()
        else:
            # Should not reach here
            pass

    def endorse_parking_infringement(self):
        if self.type == SO_TYPE_INFRINGEMENT_NOTICE:
            if not self.issued_on_paper and self.is_issuable(raise_exception=True):
                self.confirm_date_time_issue(raise_exception=True)
                self.status = SanctionOutcome.STATUS_AWAITING_PAYMENT
                self.payment_status = SanctionOutcome.PAYMENT_STATUS_UNPAID
                self.set_penalty_amounts()
                self.create_due_dates()

        new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_ENDORSE)
        self.allocated_group = new_group
        self.save()

    def mark_document_posted(self, request):
        if self.type == SO_TYPE_INFRINGEMENT_NOTICE:
            self.status = SanctionOutcome.STATUS_AWAITING_PAYMENT
            self.payment_status = SanctionOutcome.PAYMENT_STATUS_UNPAID
            self.set_penalty_amounts()
            self.create_due_dates()
            new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_ENDORSE)
            self.allocated_group = new_group
        elif self.type == SO_TYPE_CAUTION_NOTICE:
            self.status = SanctionOutcome.STATUS_CLOSED
        elif self.type == SO_TYPE_LETTER_OF_ADVICE:
            self.status = SanctionOutcome.STATUS_CLOSED
        elif self.type == SO_TYPE_REMEDIATION_NOTICE:
            self.status = SanctionOutcome.STATUS_AWAITING_REMEDIATION_ACTIONS
            # new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_ENDORSE)
            new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_RETURN_TO_OFFICER)
            self.allocated_group = new_group

        self.save()

    def endorse(self):
        if self.type == SO_TYPE_INFRINGEMENT_NOTICE:
            if self.issued_on_paper:
                self.status = SanctionOutcome.STATUS_AWAITING_PAYMENT
                self.payment_status = SanctionOutcome.PAYMENT_STATUS_UNPAID
                self.set_penalty_amounts()
                self.create_due_dates()
                new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId,
                                                                            SanctionOutcome.WORKFLOW_ENDORSE)
            else:
                if self.is_issuable(raise_exception=True):
                    self.confirm_date_time_issue(raise_exception=True)
                    # self.status = SanctionOutcome.STATUS_AWAITING_PAYMENT
                    self.status = SanctionOutcome.STATUS_AWAITING_PRINT_AND_POST
                    # self.payment_status = SanctionOutcome.PAYMENT_STATUS_UNPAID
                    # self.set_penalty_amounts()
                    # self.create_due_dates()
                    new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId,
                                                                                SanctionOutcome.WORKFLOW_MARK_DOCUMENT_POSTED)
            self.allocated_group = new_group

        elif self.type in SO_TYPE_CAUTION_NOTICE:
            self.confirm_date_time_issue(raise_exception=True)

        elif self.type in SO_TYPE_LETTER_OF_ADVICE:
            self.confirm_date_time_issue(raise_exception=True)

        elif self.type == SO_TYPE_REMEDIATION_NOTICE:
            if self.issued_on_paper:
                pass
                # TODO: paper issued and endorsed
                self.status = SanctionOutcome.STATUS_AWAITING_REMEDIATION_ACTIONS
            else:
                # self.status = SanctionOutcome.STATUS_AWAITING_REMEDIATION_ACTIONS
                self.status = SanctionOutcome.STATUS_AWAITING_PRINT_AND_POST
                new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_RETURN_TO_OFFICER)
                self.allocated_group = new_group

            id_suffix = 1
            for remediation_action in self.remediation_actions.all():
                remediation_action.status = RemediationAction.STATUS_OPEN
                remediation_action.remediation_action_id = self.lodgement_number + '-' + str(id_suffix)
                remediation_action.save()
                id_suffix += 1

        self.save()

    def create_due_dates(self, extended_by_id=None):
        print('create_due_dates')
        # Construct description
        offender, title = self.get_offender()
        recipient = ''
        if title == 'driver':
            recipient = ' to the {} (driver)'.format(offender.email)
        elif title == 'registration_holder':
            recipient = ' to the {} (registration holder)'.format(offender.email)
        elif recipient == 'offender':
            recipient = ' to the {}'.format(offender.email)
        reason_for_extension = 'Issue infringement notice on ' + self.date_of_issue.strftime("%d/%m/%Y") + recipient

        due_date_config = SanctionOutcomeDueDateConfiguration.get_config_by_date(self.date_of_issue)
        self.due_date_extended_max = self.date_of_issue + relativedelta(years=1)
        data = {}
        data['due_date_1st'] = self.date_of_issue + relativedelta(days=due_date_config.due_date_window_1st)
        data['due_date_2nd'] = self.date_of_issue + relativedelta(days=due_date_config.due_date_window_1st + due_date_config.due_date_window_2nd)
        data['reason_for_extension'] = reason_for_extension
        data['extended_by_id'] = extended_by_id
        data['sanction_outcome_id'] = self.id
        serializer = SaveSanctionOutcomeDueDateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def set_penalty_amounts(self):
        amounts = self.retrieve_penalty_amounts_by_date()
        self.penalty_amount_1st = amounts.amount
        self.penalty_amount_2nd = amounts.amount_after_due

    def decline(self, request):
        self.status = self.STATUS_DECLINED
        new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_DECLINE)
        self.allocated_group = new_group
        self.log_user_action(SanctionOutcomeUserAction.ACTION_DECLINE.format(self.lodgement_number), request)
        self.save()

    def return_to_officer(self, request):
        self.status = self.STATUS_DRAFT
        new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_RETURN_TO_OFFICER)
        self.allocated_group = new_group
        self.log_user_action(SanctionOutcomeUserAction.ACTION_RETURN_TO_OFFICER.format(self.lodgement_number), request)
        self.save()

    def escalate_for_withdrawal(self, request):
        self.status = self.STATUS_ESCALATED_FOR_WITHDRAWAL
        new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_ESCALATE_FOR_WITHDRAWAL)
        self.allocated_group = new_group
        self.log_user_action(SanctionOutcomeUserAction.ACTION_ESCALATE_FOR_WITHDRAWAL.format(self.lodgement_number), request)
        self.save()

    def withdraw_by_manager(self, request):
        self.status = self.STATUS_WITHDRAWN
        new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_WITHDRAW_BY_MANAGER)
        self.allocated_group = new_group
        self.log_user_action(SanctionOutcomeUserAction.ACTION_WITHDRAW.format(self.lodgement_number), request)
        self.save()

    def withdraw_by_branch_manager(self, request):
        self.status = self.STATUS_WITHDRAWN
        new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_WITHDRAW_BY_BRANCH_MANAGER)
        self.allocated_group = new_group
        self.log_user_action(SanctionOutcomeUserAction.ACTION_WITHDRAW.format(self.lodgement_number), request)
        self.save()

    def return_to_infringement_notice_coordinator(self, request):
        self.status = self.STATUS_AWAITING_PAYMENT
        self.payment_status = SanctionOutcome.PAYMENT_STATUS_UNPAID
        new_group = SanctionOutcome.get_compliance_permission_group(self.regionDistrictId, SanctionOutcome.WORKFLOW_RETURN_TO_INFRINGEMENT_NOTICE_COORDINATOR)
        self.allocated_group = new_group
        self.log_user_action(SanctionOutcomeUserAction.ACTION_RETURN_TO_INFRINGEMENT_NOTICE_COORDINATOR.format(self.lodgement_number), request)
        self.save()

    def retrieve_penalty_amounts_by_date(self):
        qs_aco = AllegedCommittedOffence.objects.filter(Q(sanction_outcome=self) & Q(included=True))
        if qs_aco.count() != 1:  # Only infringement notice can have penalty. Infringement notice can have only one alleged offence.
            raise ValidationError('There are multiple alleged committed offences in this sanction outcome.')
        else:
            return qs_aco.first().retrieve_penalty_amounts_by_date(self.date_of_issue)

    @property
    def coming_due_date(self):
        try:
            if self.type == SO_TYPE_INFRINGEMENT_NOTICE:
                today = datetime.date.today()
                due_dates = self.due_dates.all()
                last_due_date = due_dates.order_by('id').last()
                if last_due_date.due_date_term_currently_applied == '1st':
                    return last_due_date.due_date_1st
                elif last_due_date.due_date_term_currently_applied == '2nd':
                    return last_due_date.due_date_2nd
                elif last_due_date.due_date_term_currently_applied == 'overdue':
                    # Overdue
                    return last_due_date.due_date_2nd
                # if today <= self.last_due_date_1st:
                #     return self.last_due_date_1st
                # if today <= self.last_due_date_2nd:
                #     return self.last_due_date_2nd
                # else:
                #     # Overdue
                #     return self.last_due_date_2nd
            else:
                return None
        except Exception as e:
            return None

    @property
    def last_due_date(self):
        if self.type == SO_TYPE_INFRINGEMENT_NOTICE:
            due_dates = self.due_dates.order_by('-created_at')
            if self.date_of_issue and not due_dates:
                raise ValidationError('Issued but not due dates are set.')
            return due_dates.first()
        else:
            return None

    @property
    def last_due_date_1st(self):
        return self.last_due_date.due_date_1st

    @property
    def last_due_date_2nd(self):
        return self.last_due_date.due_date_2nd

    def extend_due_date(self, target_date, reason_for_extension, extended_by_id):
        print('extend_due_date')
        now_date = datetime.datetime.now().date()
        due_date_config = SanctionOutcomeDueDateConfiguration.get_config_by_date(self.date_of_issue)
        if target_date <= self.due_date_extended_max:
            data = {}
            if now_date <= self.last_due_date_1st:
                data['due_date_1st'] = target_date
                data['due_date_2nd'] = target_date + relativedelta(days=due_date_config.due_date_window_2nd)
                data['due_date_term_currently_applied'] = '1st'
            elif now_date <= self.last_due_date_2nd:
                data['due_date_1st'] = self.last_due_date_1st
                data['due_date_2nd'] = target_date
                data['due_date_term_currently_applied'] = '2nd'
            data['reason_for_extension'] = 'Extend due date: ' + reason_for_extension
            data['extended_by_id'] = extended_by_id
            data['sanction_outcome_id'] = self.id

            # Create new duedate record
            serializer = SaveSanctionOutcomeDueDateSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return True
        return False

    def determine_penalty_amount_by_date(self, date_payment):
        try:
            if self.offence_occurrence_date <= date_payment:
                # if date_payment <= self.last_due_date_1st:
                if self.last_due_date.due_date_term_currently_applied == '1st':
                        return self.penalty_amount_1st
                elif self.last_due_date.due_date_term_currently_applied == '2nd':
                    return self.penalty_amount_2nd
                elif self.last_due_date.due_date_term_currently_applied == '2nd':
                    raise ValidationError('Overdue')
                else:
                    # Should not reach here
                    # Details of the sanction outcome is uploaded to the Fines Enforcement system after the 2nd due
                    # After that, the sanciton outcome should be closed (??? External user should still be able to see the sanction outcome???)
                    raise ValidationError('Overdue')
            else:
                # Should not reach here
                raise ValidationError('Payment must be after the offence occurrence date.')
        except Exception as e:
            raise ValidationError('Something wrong.')

    @property
    def as_line_items(self):
        """ Create the ledger lines - line item for infringement penalty sent to payment system """

        now = datetime.datetime.now()
        now_date = now.date()
        penalty_amount = self.determine_penalty_amount_by_date(now_date)

        line_items = [
            {'ledger_description': 'Infringement Notice: {}, Issued: {} {}'.format(
                self.lodgement_number,
                self.date_of_issue.strftime("%d/%m/%Y"),
                self.time_of_issue.strftime("%I:%M %p")),
                'oracle_code': 'ABC123 GST',
                'price_incl_tax': penalty_amount,
                'price_excl_tax': penalty_amount,
                'quantity': 1,
            },
        ]
        return line_items

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_SanctionOutcome'
        verbose_name_plural = 'CM_SanctionOutcomes'
        ordering = ['-id']


class AllegedCommittedOffence(RevisionedMixin):
    alleged_offence = models.ForeignKey(AllegedOffence, null=False,)
    sanction_outcome = models.ForeignKey(SanctionOutcome, null=False,)
    included = models.BooleanField(default=True)  # True means sanction_outcome is included in the sanction_outcome

    @staticmethod
    def get_active_alleged_committed_offences(alleged_offence):
        return AllegedCommittedOffence.objects.filter(
            Q(included=True) &
            Q(alleged_offence=alleged_offence)
        ).exclude(
            # Once sanction outcome is declined, related alleged_offence can be included in another sanction outcome.
            Q(sanction_outcome__status__in=(SanctionOutcome.STATUS_DECLINED, SanctionOutcome.STATUS_WITHDRAWN)))

    def retrieve_penalty_amounts_by_date(self, date_of_issue):
        return self.alleged_offence.retrieve_penalty_amounts_by_date(date_of_issue)

    @property
    def dotag_offence_code(self):
        return self.alleged_offence.dotag_offence_code

    @property
    def issue_due_date_window(self):
        return self.alleged_offence.issue_due_date_window

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_AllegedCommittedOffence'
        verbose_name_plural = 'CM_AllegedCommittedOffences'


class RemediationActionExternalManager(models.Manager):
    def get_queryset(self):
        return super(RemediationActionExternalManager, self).get_queryset().filter(
            Q(sanction_outcome__in=SanctionOutcome.objects_for_external.all())
        )


class RemediationAction(RevisionedMixin):
    STATUS_OPEN = 'open'
    STATUS_OVERDUE = 'overdue'
    STATUS_SUBMITTED = 'submitted'
    STATUS_ACCEPTED = 'accepted'
    STATUS_CHOICES = (
        (STATUS_OPEN, 'Open'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_ACCEPTED, 'Accepted')
    )
    FINAL_STATUSES = (STATUS_ACCEPTED, )

    remediation_action_id = models.CharField(max_length=20, blank=True)
    action = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    sanction_outcome = models.ForeignKey(SanctionOutcome, related_name='remediation_actions', null=True, on_delete=models.SET_NULL,)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, blank=True,)
    objects = models.Manager()
    objects_for_external = RemediationActionExternalManager()
    action_taken = models.TextField(blank=True)

    # validate if the sanction outcome is remediation_notice
    def clean_fields(self, exclude=None):
        if self.sanction_outcome.type != 'remediation_notice':
            raise ValidationError({'sanction_outcome': [u'The type of the sanction outcome must be Remediation-Notice when saving a remediation action.']})
        super(RemediationAction, self).clean_fields(exclude)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_RemediationAction'
        verbose_name_plural = 'CM_RemediationActions'

    def __str__(self):
        return 'ID: {}, action:{}'.format(self.id, self.action,)


def perform_can_close_record(sender, instance, **kwargs):
    # Trigger the close() function of each parent entity of this sanction outcome
    if isinstance(instance, SanctionOutcome):
        if instance.status in SanctionOutcome.FINAL_STATUSES:
            close_record, parents = can_close_record(instance)
            for parent in parents:
                if parent.status in ('pending_closure', ):  # tuple must include all the status regarded as pending closure
                    parent.close()
    elif isinstance(instance, RemediationAction):
        if instance.status in RemediationAction.FINAL_STATUSES:
            parent = instance.sanction_outcome
            if parent.status in (SanctionOutcome.STATUS_PENDING_CLOSURE, SanctionOutcome.STATUS_AWAITING_REMEDIATION_ACTIONS):  # tuple must include all the status regarded as pending closure
                if parent.can_close_record():
                    parent.close()

            # close_record, parents = can_close_record(instance)
            # for parent in parents:
            #     if parent.status in ('pending_closure', SanctionOutcome.STATUS_AWAITING_REMEDIATION_ACTIONS):  # tuple must include all the status regarded as pending closure
            #         parent.close()


post_save.connect(perform_can_close_record, sender=SanctionOutcome)
post_save.connect(perform_can_close_record, sender=RemediationAction)


def update_compliance_doc_filename(instance, filename):
    return 'wildlifecompliance/sanction_outcome/{}/documents/{}'.format(
        instance.sanction_outcome.id, filename)


class SanctionOutcomeDocument(Document):
    sanction_outcome = models.ForeignKey(SanctionOutcome, related_name='documents')
    _file = models.FileField(max_length=255, upload_to=update_compliance_doc_filename)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_SanctionOutcomeDocument'
        verbose_name_plural = 'CM_SanctionOutcomeDocuments'


class SanctionOutcomeDocumentAccessLog(models.Model):
    accessed_at = models.DateTimeField(auto_now_add=True)
    accessed_by = models.ForeignKey(EmailUser,)
    sanction_outcome_document = models.ForeignKey(SanctionOutcomeDocument, related_name='access_logs')

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_SanctionOutcomeDocumentAccessLog'
        verbose_name_plural = 'CM_SanctionOutcomeDocumentAccessLogs'


class SanctionOutcomeCommsLogDocument(Document):
    log_entry = models.ForeignKey('SanctionOutcomeCommsLogEntry', related_name='documents')
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'


class SanctionOutcomeCommsLogEntry(CommunicationsLogEntry):
    sanction_outcome = models.ForeignKey(SanctionOutcome, related_name='comms_logs')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        print('=================')
        print('In SanctionOutcomeCommsLogEntry.save()')
        super(SanctionOutcomeCommsLogEntry, self).save(force_insert, force_update, using, update_fields)

    class Meta:
        app_label = 'wildlifecompliance'


class SanctionOutcomeUserAction(models.Model):
    ACTION_ISSUE_PARKING_INFRINGEMENT = "Issue Parking Infringement {} to {}"
    ACTION_CREATE = "Create Sanction Outcome {}"
    ACTION_SEND_TO_MANAGER = "Forward Sanction Outcome {} to manager"
    ACTION_UPDATE = "Update Sanction Outcome {}"
    ACTION_ENDORSE_AND_ISSUE = "Endorse and Issue Sanction Outcome {}"
    ACTION_ENDORSE = "Endorse Sanction Outcome {}"
    ACTION_MARK_AS_POSTED = "Mark Document(s) posted for the Sanction Outcome {}"
    ACTION_SEND_TO_DOT = "Send details of Sanction Outcome {} to Dep. of Transport"
    ACTION_DECLINE = "Decline Sanction Outcome {}"
    ACTION_RETURN_TO_OFFICER = "Request amendment for Sanction Outcome {}"
    ACTION_RETURN_TO_INFRINGEMENT_NOTICE_COORDINATOR = "Return Sanction Outcome {} to Infringement Notice Coordinator"
    ACTION_WITHDRAW = "Withdraw Sanction Outcome {}"
    ACTION_PENDING_CLOSURE = "Mark Sanction Outcome {} as pending closure"
    ACTION_CLOSE = "Close Sanction Outcome {}"
    ACTION_ADD_WEAK_LINK = "Create manual link between Sanction Outcome: {} and {}: {}"
    ACTION_REMOVE_WEAK_LINK = "Remove manual link between Sanction Outcome: {} and {}: {}"
    ACTION_REMOVE_ALLEGED_COMMITTED_OFFENCE = "Remove alleged committed offence: {}"
    ACTION_RESTORE_ALLEGED_COMMITTED_OFFENCE = "Restore alleged committed offence: {}"
    ACTION_INCLUDE_ALLEGED_COMMITTED_OFFENCE = "Include alleged committed offence: {}"
    ACTION_EXTEND_DUE_DATE = "Extend due date of Sanction Outcome {} from {} to {}"
    ACTION_SEND_DETAILS_TO_INFRINGEMENT_NOTICE_COORDINATOR = "Send details of the Unpaid Infringement Notice {} to Infringement Notice Coordinator"
    ACTION_ESCALATE_FOR_WITHDRAWAL = "Escalate Infringement Notice {} for withdrawal"
    ACTION_INCREASE_FEE_AND_EXTEND_DUE = "Extend due date from {} to {} and Increase penalty amount from {} to {}"
    ACTION_REMEDIATION_ACTION_OVERDUE = "Set status of Remediation Action {} to 'overdue'"
    ACTION_REMEDIATION_ACTION_SUBMITTED = "Submit Remediation Action {}"
    ACTION_REMEDIATION_ACTION_ACCEPTED = "Accept Remediation Action {}"
    ACTION_REQUEST_AMENDMENT = "Request amendment for Remediation Action {}"
    ACTION_PAY_INFRINGEMENT_PENALTY = "Pay for Infringement Penalty of the Infringement {}, Total payment amount: {}, Invoice: {}"
    # ACTION_PAY_PARTIALLY = "Pay partially for Infringement Penalty of the Infringement {}, Amount: {}, Invoice: {}"
    # ACTION_OVER_PAY = "Over-Pay for Infringement Penalty of the Infringement {}, Amount: {}, Invoice: {}"

    who = models.ForeignKey(EmailUser, null=True, blank=True)
    when = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    what = models.TextField(blank=False)
    sanction_outcome = models.ForeignKey(SanctionOutcome, related_name='action_logs')

    class Meta:
        app_label = 'wildlifecompliance'
        ordering = ('-when',)

    @classmethod
    def log_action(cls, obj, action, user=None):
        return cls.objects.create(
            sanction_outcome=obj,
            who=user,
            what=str(action)
        )


class DotRequestFile(models.Model):
    contents = models.TextField(blank=True)
    filename = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sanction_outcomes = models.ManyToManyField(SanctionOutcome, related_name='dot_request_files')  # Make this manytomany for now, but it is used as onetomany

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_DotReguestFile'
        verbose_name_plural = 'CM_DotReguestFiles'


class UnpaidInfringementFile(models.Model):
    contents = models.TextField(blank=True)
    filename = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super(UnpaidInfringementFile, self).save(*args, **kwargs)

        need_save = False

        if not self.filename:
            self.filename = '{0:05d}'.format(self.pk) + 'UIN.uin'
            need_save = True

        if need_save:
            self.save()  # Be careful, this might lead to the infinite loop

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_UnpaidInfringementFile'
        verbose_name_plural = 'CM_UnpaidInfringementFiles'


class ActionTakenDocument(Document):
    remediation_action = models.ForeignKey(RemediationAction, related_name='documents')
    _file = models.FileField(max_length=255)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_RemediationActionDocument'
        verbose_name_plural = 'CM_RemediationActionDocuments'


class AmendmentRequestReason(models.Model):
    reason = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_AmendmentRequestReason'
        verbose_name_plural = 'CM_AmendmentRequestReasons'

    def __str__(self):
        return self.reason


class AmendmentRequestForRemediationAction(models.Model):
    remediation_action = models.ForeignKey(RemediationAction, related_name='amendment_requests')
    # The value of this field is copied from the selection of AmendmentRequestReason
    reason = models.CharField(max_length=100, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.reason

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_AmendmentRequest'
        verbose_name_plural = 'CM_AmendmentRequests'


class RemediationActionNotification(models.Model):
    TYPE_CLOSE_TO_DUE = 'close_to_due'
    TYPE_OVERDUE = 'overdue'

    type = models.CharField(max_length=30, blank=True,)
    remediation_action = models.ForeignKey(RemediationAction, related_name='notifications')
    sanction_outcome_comms_log_entry = models.ForeignKey(SanctionOutcomeCommsLogEntry,)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_RemediationActionNotification'
        verbose_name_plural = 'CM_RemediationActionNotifications'


import reversion
#reversion.register(SanctionOutcome_alleged_offences, follow=[])
reversion.register(SanctionOutcome, follow=['due_dates', 'allegedcommittedoffence_set', 'remediation_actions', 'documents', 'comms_logs', 'action_logs', 'dot_request_files'])
reversion.register(AllegedCommittedOffence, follow=[])
reversion.register(RemediationAction, follow=['documents', 'amendment_requests', 'notifications'])
reversion.register(SanctionOutcomeDocument, follow=['access_logs'])
reversion.register(SanctionOutcomeDocumentAccessLog, follow=[])
reversion.register(SanctionOutcomeCommsLogDocument, follow=[])
reversion.register(SanctionOutcomeCommsLogEntry, follow=['documents', 'remediationactionnotification_set'])
reversion.register(SanctionOutcomeUserAction, follow=[])
#reversion.register(DotRequestFile_sanction_outcomes, follow=[])
reversion.register(DotRequestFile, follow=[])
reversion.register(UnpaidInfringementFile, follow=[])
reversion.register(ActionTakenDocument, follow=[])
reversion.register(AmendmentRequestReason, follow=[])
reversion.register(AmendmentRequestForRemediationAction, follow=[])
reversion.register(RemediationActionNotification, follow=[])

