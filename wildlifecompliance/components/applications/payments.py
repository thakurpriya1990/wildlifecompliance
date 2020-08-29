import abc
import logging

from django.db import transaction

from wildlifecompliance.components.applications.models import (
    Application,
    ApplicationSelectedActivityPurpose,
    ApplicationFormDataRecord,
    ApplicationInvoice,
    ActivityInvoiceLine,
)

logger = logging.getLogger(__name__)
logging.disable(logging.NOTSET)
logger.setLevel(logging.DEBUG)


class InvoiceClearable(object):
    '''
    An interface for invoices which may be applicable for Clearing accounts.
    '''
    TYPE_CASH = ApplicationInvoice.OTHER_PAYMENT_METHOD_CASH
    TYPE_NONE = ApplicationInvoice.OTHER_PAYMENT_METHOD_NONE
    TYPE_CARD = 'card'

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def verify_payment_status(self):
        '''
        Verifies the payment status.
        '''

    @abc.abstractmethod
    def is_refundable(self):
        '''
        Check for refund amount.
        '''

    @abc.abstractmethod
    def is_recordable(self):
        '''
        Check for amount requiring to be recorded in ledger.
        '''

    @abc.abstractmethod
    def is_refundable_with_payment(self):
        '''
        Check for refund amount at invoicing.
        '''


class LicenceFeeClearingInvoice(InvoiceClearable):
    '''
    A representation of an invoice for a licence fee that has been recorded on
    the ledger with an un-balanced amount. ie either under or over paid.

    NOTE: Can occur where the licence fee consist of fees for adjustment to
    application fee, additional fees and refunds for declined licenses.
    '''
    application = None                  # Composite application.
    fee_policy = None                   # Policy applied to the fee update.
    dynamic_attributes = None           # Container for fees.
    invoice_balance = None              # balance attributes.
    is_refreshing = False               # Flag indicating a page refresh.
    is_refundable = False               # Flag indicating if refundable.

    def __init__(self, application):
        super(InvoiceClearable, self).__init__()
        self.application = application
        self.is_refundable = self.is_refundable_with_payment()

    def verify_payment_status(self):
        '''
        Verifies the payment status.

        NOTE: concrete method.
        '''
        return self.application.payment_status

    def is_refundable_with_payment(self):
        '''
        Check for a refund amount when a payment is required for application
        fee adjustments and/or additional fees.
        - additional or adjustment fees exists.
        - application requires a refund.
        - refundable amount does not exceed fees.
        '''
        requires_payment = self.application.has_adjusted_fees \
            or self.application.has_additional_fees

        refund_amt = self.application.get_refund_amount()  # refund is negative
        requires_refund = requires_payment and (refund_amt < 0)

        # self.application.application_fee excludes licence fee amount.
        # amount = self.application.application_fee \
        #     + self.application.additional_fees + refund_amt
        amount = self.application.additional_fees + refund_amt

        return requires_refund and amount > 0

    def is_recordable(self):
        '''
        Check for amount requiring to be recorded in ledger.

        NOTE: concrete method.
        '''
        return self.application.requires_record

    def get_product_line_refund_for(self, payable_purpose):
        '''
        Builds a refundable payment line for a payable licence purpose.
        '''
        from ledger.checkout.utils import calculate_excl_gst
        if not self.is_refundable:
            return None

        refund = payable_purpose.get_refund_amount()

        if not refund < 0:
            return None

        price_excl = calculate_excl_gst(refund)
        if ApplicationFeePolicy.GST_FREE:
            price_excl = refund
        oracle_code = payable_purpose.purpose.oracle_account_code

        product_line = {
            'ledger_description': '{} (Refund)'.format(
                payable_purpose.purpose.name),
            'quantity': 1,
            'price_incl_tax': str(refund),
            'price_excl_tax': str(price_excl),
            'oracle_code': oracle_code
        }

        return product_line

    def get_invoice_line_refund_for(self, r_purpose, inv_ref):
        '''
        Builds a refundable invoice line for a payable licence purpose.
        '''
        if not self.is_refundable:
            return None

        refund = r_purpose.get_refund_amount()

        if not refund < 0:
            return None

        l_type = ActivityInvoiceLine.LINE_TYPE_LICENCE
        invoice_line = ActivityInvoiceLine(
            invoice=inv_ref,
            licence_activity=r_purpose.selected_activity.licence_activity,
            licence_purpose=r_purpose.purpose,
            invoice_line_type=l_type,
            amount=refund
        )

        return invoice_line

    def get_product_line_for_refund(self, description=None):
        '''
        Builds and returns a product line for the refund.

        NOTE: display the last invoice number on line.
        '''
        from ledger.checkout.utils import calculate_excl_gst

        if not self.is_refundable:
            return None

        product_lines = []
        activities_with_refund = [
            a for a in self.application.activities]

        for activity in activities_with_refund:

            paid_purposes = [
                p for p in activity.proposed_purposes.all()
                if p.is_payable
            ]

            for p in paid_purposes:

                fee = p.get_refund_amount()

                if not fee < 0:
                    continue

                price_excl = calculate_excl_gst(fee)
                if ApplicationFeePolicy.GST_FREE:
                    price_excl = fee
                oracle_code = p.purpose.oracle_account_code

                product_lines.append({
                    'ledger_description': '{} (Refund)'.format(
                        p.purpose.name),
                    'quantity': 1,
                    'price_incl_tax': str(fee),
                    'price_excl_tax': str(price_excl),
                    'oracle_code': oracle_code
                })

        return product_lines

    # def _get_product_line_for_refund(self, description=None):
    #     '''
    #     Builds and returns a product line for the refund.

    #     NOTE: display the last invoice number on line.
    #     '''
    #     from ledger.checkout.utils import calculate_excl_gst

    #     if not self.is_refundable:
    #         return None

    #     desc = 'Licence fee refund' if not description else description
    #     refund = self.application.get_refund_amount()
    #     refund = refund * -1
    #     refund_excl = refund \
    #         if ApplicationFeePolicy.GST_FREE else calculate_excl_gst(refund)
    #     # oracle_code = activity.licence_activity.oracle_account_code
    #     oracle_code = ''

    #     product_line = {
    #                 'ledger_description': '{0}'.format(desc),
    #                 'quantity': 1,
    #                 'price_incl_tax': str(refund),
    #                 'price_excl_tax': str(refund_excl),
    #                 'oracle_code': oracle_code
    #             }

    #     return product_line

    def set_refunded_fees_for(self, activity):
        '''
        Sets the Refunded Fee amount on the licence activity applying the
        relevant fee policy.
        '''
        if not self.is_refundable:
            return
        # apply fee policy to re-calculate total fees for application.
        self.fee_policy.set_dynamic_attributes_for(activity)

    def build_balance_amount(self):
        '''
        Calculate balance for invoices on the application.
        '''
        from ledger.payments.invoice.models import Invoice

        inv_balance_amt = 0                 # total invoice amount owed.
        inv_payment_amt = 0                 # total invoice amount paid.

        for activity in self.application.activities:

            for activity_inv in activity.activity_invoices.distinct(
                'invoice_reference',
            ):
                invoice = Invoice.objects.filter(
                    reference=activity_inv.invoice_reference
                )
                inv_balance_amt += invoice[0].amount
                inv_payment_amt += invoice[0].payment_amount

        self.invoice_balance = {
            'balance_amt': inv_balance_amt,
            'payment_amt': inv_payment_amt,
        }

    def generate(self, request):
        '''
        Generates an invoice for a CASH payment with this clearing.
        '''
        from wildlifecompliance.components.main.utils import (
            set_session_other_pay_method,
            create_other_application_invoice,
        )

        set_session_other_pay_method(
            request.session, self.TYPE_CASH)
        invoice = create_other_application_invoice(self.application, request)
        invoice_ref = invoice.reference

        return invoice_ref


class ApplicationFeePolicy(object):
    """
    A Payment Policy Interface for Licence Applications.
    """
    GST_FREE = True                     # Flag to set GST.
    for_amendment = False               # Flag for licence amendments.

    __metaclass__ = abc.ABCMeta

    @staticmethod
    def get_fee_policy_for(application):

        AMEND = Application.APPLICATION_TYPE_AMENDMENT
        RENEW = Application.APPLICATION_TYPE_RENEWAL
        NEW = Application.APPLICATION_TYPE_NEW_LICENCE
        # New Activity is set for multiple activities on application.
        NEW_ACTIVITY = Application.APPLICATION_TYPE_ACTIVITY

        get_policy = {
            AMEND: ApplicationFeePolicyForAmendment(application),
            RENEW: ApplicationFeePolicyForRenew(application),
            NEW: ApplicationFeePolicyForNew(application),
            NEW_ACTIVITY: ApplicationFeePolicyForNew(application),
        }
        policy = get_policy.get(
            application.application_type,
            ApplicationFeePolicyForNew(application)
        )

        return policy

    @staticmethod
    def get_fee_product_lines_for(application):
        """
        Gets the checkout product lines for this application which includes
        fee for both the application and licence activities.
        """
        from ledger.checkout.utils import calculate_excl_gst

        product_lines = []

        # application fee.
        activities_with_fees = [
            a for a in application.activities if a.application_fee > 0]

        for activity in activities_with_fees:

            paid_purposes = [
                p for p in activity.proposed_purposes.all()
                if p.is_payable
            ]

            for p in paid_purposes:

                fee = p.get_payable_application_fee()

                price_excl = calculate_excl_gst(fee)
                if ApplicationFeePolicy.GST_FREE:
                    price_excl = fee
                oracle_code = p.purpose.oracle_account_code

                product_lines.append({
                    'ledger_description': '{} (Application Fee)'.format(
                        p.purpose.name),
                    'quantity': 1,
                    'price_incl_tax': str(fee),
                    'price_excl_tax': str(price_excl),
                    'oracle_code': oracle_code
                })

        # licence activities.
        activities_with_fees = [
            a for a in application.activities if a.licence_fee > 0]

        for activity in activities_with_fees:

            paid_purposes = [
                p for p in activity.proposed_purposes.all()
                if p.is_payable
            ]

            for p in paid_purposes:

                fee = p.get_payable_licence_fee()

                price_excl = calculate_excl_gst(fee)
                if ApplicationFeePolicy.GST_FREE:
                    price_excl = fee
                oracle_code = p.purpose.oracle_account_code

                product_lines.append({
                    'ledger_description': '{} (Licence Fee)'.format(
                        p.purpose.name),
                    'quantity': 1,
                    'price_incl_tax': str(fee),
                    'price_excl_tax': str(price_excl),
                    'oracle_code': oracle_code
                })

        # activities = application.selected_activities.all()
        # Include additional fees by licence approvers.
        # if application.has_additional_fees:
        #     # only fees which are greater than zero.
        #     activities_with_fees = [
        #         a for a in activities if a.additional_fee > 0
        #     ]

        #     # only fees awaiting payment
        #     for activity in activities_with_fees:

        #         price_excl = calculate_excl_gst(activity.additional_fee)
        #         if ApplicationFeePolicy.GST_FREE:
        #             price_excl = activity.additional_fee
        #         oracle_code = ''

        #         product_lines.append({
        #             'ledger_description': '{}'.format(
        #                 activity.additional_fee_text),
        #             'quantity': 1,
        #             'price_incl_tax': str(activity.additional_fee),
        #             'price_excl_tax': str(price_excl),
        #             'oracle_code': oracle_code
        #         })

        # Check if refund is required.
        # clear_inv = LicenceFeeClearingInvoice(application)
        # if clear_inv.is_refundable():
        #     product_lines.append(clear_inv.get_product_line_for_refund())

        return product_lines

    @abc.abstractmethod
    def set_application_fee(self):
        """
        Sets the application fee from what was previously saved on the model.
        """
        pass

    def set_has_fee_exemption(self, exempt=False):
        '''
        Set this fee policy to calculate zero fee amounts for zero amount
        invoices. A calculated fee is stored with the application.
        '''
        self.has_fee_exemption = exempt

    def set_dynamic_attributes(self, attributes):
        '''
        Set application fees in attributes container to new fee attributes.
        '''
        try:
            if self.is_refreshing:
                return
            self.set_application_fee_from_attributes(attributes)
            self.dynamic_attributes = attributes

        except BaseException:
            raise

    def get_dynamic_attributes(self):
        '''
        Get the container of attributes set on this policy.
        '''
        return self.dynamic_attributes

    def set_dynamic_attributes_for(self, activity):
        '''
        Set dynamic attributes associated with the Activity on this policy.
        '''
        try:
            if self.is_refreshing:
                return

            '''
            1.  Initialise application fees for all purposes on the activity.
                Fees on purposes may be re-set when calculating the application
                fee from updated activity (step 2).
            '''
            self.set_application_fee_on_purpose_for(activity)

            '''
            2.  Re-calculate dynamic attributes with updated activity fees.
            '''
            self.set_application_fee_from_activity(activity)

            '''
            3.  Re-calculate dynamic attributes with saved details to guarantee
                dynamic attribute fees match changes committed.

            '''
            self.set_dynamic_attributes_from_purpose_fees()

        except BaseException as e:
            logger.error(
                'ERR: set_dynamic_attributes_for activityID {0} - {1}'.format(
                    activity.id, e)
            )
            raise

    def set_dynamic_attributes_from_purpose_fees(self):
        '''
        Set the fee attributes on this policy to licence activity purposes
        saved against the application.
        '''
        has_purpose = False     # No purposes will exist with pre-submission.
        fees_app_tot = 0
        fees_lic_tot = 0
        for activity in self.application.activities:
            fees_app = 0
            fees_app_adj = 0
            fees_lic = 0
            fees_lic_adj = 0
            paid_lic_tot = 0
            paid_app_tot = 0
            for p in activity.proposed_purposes.all():
                fees_app_adj += p.adjusted_fee if p.is_payable else 0
                fees_app += p.application_fee if p.is_payable else 0
                fees_lic += p.licence_fee if p.is_payable else 0
                fees_lic_adj += p.adjusted_licence_fee if p.is_payable else 0

                paid_lic_tot += p.total_paid_adjusted_licence_fee \
                    if p.is_payable else 0
                paid_app_tot += p.total_paid_adjusted_application_fee \
                    if p.is_payable else 0

                has_purpose = True

            paid_amt = activity.total_paid_amount
            fees_app = fees_app + fees_app_adj
            fees_lic = fees_lic + fees_lic_adj

            # amount already paid on application or the policy is for a licence
            # amendment then exclude paid amount.
            if paid_amt > 0 or self.for_amendment:
                fees_app = fees_app - paid_app_tot
                fees_lic = fees_lic - paid_lic_tot

            fees_app_tot += fees_app
            fees_lic_tot += fees_lic

        if has_purpose:
            self.dynamic_attributes['fees']['application'] = fees_app_tot
            self.dynamic_attributes['fees']['licence'] = fees_lic_tot

        if self.has_fee_exemption:
            self.dynamic_attributes['fees']['application'] = 0
            self.dynamic_attributes['fees']['licence'] = 0

    @transaction.atomic
    def set_application_fee_on_purpose_for(self, activity):
        '''
        Set the base fees for all purposes on the selected activity.
        '''
        for purpose in activity.purposes:
            p, c = ApplicationSelectedActivityPurpose.objects.get_or_create(
                selected_activity_id=activity.id,
                purpose_id=purpose.id
            )
            if c:  # Only save fees for those not created.
                p.application_fee = purpose.base_application_fee
                p.licence_fee = purpose.base_licence_fee
                p.save()


class ApplicationFeePolicyForAmendment(ApplicationFeePolicy):
    '''
    A fee policy that applies to an application for a licence amendment.
    - applies an admin amendment fee as the application fee.
    - applies no licence fee.
    - all adjustment fees from the previous application are excluded.
    - adjustment fees based on questions are added to the application fee.
    '''
    AMEND = Application.APPLICATION_TYPE_AMENDMENT

    application = None
    dynamic_attributes = None   # Container for Activity fees.
    is_refreshing = False       # Flag indicating a page refresh.
    has_fee_exemption = False   # Allow exemption for zero amount invoice.

    def __init__(self, application):
        super(ApplicationFeePolicy, self).__init__()
        self.application = application
        if self.application.application_type == self.AMEND:
            self.for_amendment = True       # on super
            self.init_dynamic_attributes()

    def __str__(self):
        return 'Amend fee policy for {0}{1}'.format(
           'Application: {app} '.format(app=self.application.id),
           'attributes : {att} '.format(att=self.dynamic_attributes),
        )

    @staticmethod
    def set_zero_licence_fee_for(purpose):
        '''
        No base licence fees are paid for Amended Activity Purposes.
        '''
        purpose.base_licence_fee = 0
        purpose.base_application_fee = purpose.amendment_application_fee

    @staticmethod
    def set_base_application_fee_for(purpose):
        '''
        Set the application fee to the amendment fee.
        '''
        purpose.base_application_fee = purpose.amendment_application_fee

    def get_licence_for(self):
        '''
        Gets the current licence associated with this amendment application.
        '''
        from wildlifecompliance.components.licences.models import (
            WildlifeLicence,
        )
        licence = None
        current_id = self.application.licence_id

        try:
            licence = WildlifeLicence.objects.get(
                id=current_id
            )

        except WildlifeLicence.DoesNotExist:
            pass

        except BaseException:
            raise Exception('Exception getting licence.')

        return licence

    def get_form_purpose_ids_for(self, activity):
        '''
        Gets a list of purpose identifiers for the selected activity which
        exist on the Application Form.
        '''
        purpose_ids = ApplicationFormDataRecord.objects.filter(
            application_id=self.application.id,
            licence_activity_id=activity.licence_activity_id,
        ).values_list('licence_purpose_id', flat=True).distinct()

        return purpose_ids

    def init_dynamic_attributes(self):
        '''
        Initialise the dynamic attributes on this policy with the application
        fee from previous purposes on the licence.
        '''
        self.is_refreshing = False

        if self.application.application_fee == 0:
            application_fees = 0
            licence = self.get_licence_for()
            for activity in licence.current_activities:
                purposes_ids = self.get_form_purpose_ids_for(activity)
                for p in activity.proposed_purposes.all():
                    if p.purpose_id in purposes_ids and p.is_payable:
                        application_fees += p.purpose.amendment_application_fee
        else:
            application_fees = self.application.application_fee

        self.dynamic_attributes = {
            'fees': {
                'application': application_fees,
                'licence': self.get_licence_fee(),
            },
            'activity_attributes': {},
        }

        if self.application.application_fee_paid:
            self.dynamic_attributes['fees'] = {'application': 0, 'licence': 0}

    @transaction.atomic
    def set_purpose_fees_for(self, activity):
        """
        Set all fees for the selected activity/purpose.
        """
        # get purposes from the application form.
        purposes_ids = self.get_form_purpose_ids_for(activity)
        # set the selected activity purpose base fees.
        for p_id in purposes_ids:
            purpose = [p for p in activity.purposes if p.id == p_id]
            p, c = ApplicationSelectedActivityPurpose.objects.get_or_create(
                selected_activity_id=activity.id,
                purpose_id=purpose[0].id
            )
            p.application_fee = p.purpose.amendment_application_fee
            p.licence_fee = self.get_licence_fee()
            # NOTE: p.adjusted_fee not updated as this policy only updates the
            # licence and application fees.
            p.save()

    def set_licence_fee_to_zero_for(self, activity):
        """
        No licence fee is paid for amended Activity/Purpose.
        """
        activity.licence_fee = self.get_licence_fee()

    def get_licence_fee(self):
        '''
        Get licence fee set for this policy.
        '''
        from decimal import Decimal

        fee = 0

        return Decimal(fee)

    def get_amendment_fee_for(self, activity):
        '''
        Get the application amendment fee set for this policy.
        '''
        from decimal import Decimal

        fee = 0
        licence = self.get_licence_for()
        for activity in licence.current_activities:
            purposes_ids = self.get_form_purpose_ids_for(activity)
            for p in activity.proposed_purposes.all():
                if p.purpose_id in purposes_ids and p.is_payable:
                    fee += p.purpose.amendment_application_fee

        return Decimal(fee)

    def set_application_fee(self):
        """
        Set Application fee from the saved model. Required when presentation is
        refreshed and no attributes are passed.
        """
        self.is_refreshing = True
        # REQ_NOPAY = ApplicationInvoice.PAYMENT_STATUS_NOT_REQUIRED
        REQ_AMEND = Application.CUSTOMER_STATUS_AMENDMENT_REQUIRED

        is_saved = True \
            if not self.application.application_fee == 0 else False

        if self.application.customer_status == REQ_AMEND or is_saved:
            self.set_dynamic_attributes_from_purpose_fees()
            return

        # Override the parent setter as Licence amendments need to exclude
        # previous adjustments paid for licence purposes.
        application_fees = 0
        licence = self.get_licence_for()

        for activity in licence.current_activities:
            is_selected = False
            purposes_ids = self.get_form_purpose_ids_for(activity)
            a_activity = self.application.activities.filter(
                licence_activity_id=activity.licence_activity_id
            ).first()

            save_app = 0
            prev_app_adj = 0
            for p in activity.proposed_purposes.all():
                if p.purpose_id in purposes_ids and p.is_payable:
                    # Only for purposes existing in copied form.
                    # save_app += p.application_fee
                    save_app += p.purpose.amendment_application_fee
                    prev_app_adj += p.adjusted_fee
                    is_selected = True

            if is_selected:
                # adjustments and fees excluding previous adjustments paid
                # application_fees += save_app - prev_adj
                application_fees += save_app
                self.dynamic_attributes[
                    'activity_attributes'][a_activity] = {
                        'fees': application_fees
                    }

        self.dynamic_attributes['fees']['application'] = application_fees

    def set_application_fee_from_activity(self, activity):
        '''
        Set the application fee from an updated licence activity.

        Captures any changes to the application fee from the licence activity
        and applies it to the total fee for the activity.

        NOTE: Same calculation for set_application_fee_from_attributes.
        '''
        licence_paid = False if activity.total_paid_amount < 1 else True
        policy_licence_fee = self.dynamic_attributes['fees']['licence']
        self.set_purpose_fees_for(activity)         # update fees on purpose.
        prev_adj = self.get_previous_adjusted_fee_for(activity)
        # prev_app = self.get_previous_application_fee_for(activity)

        # Adjusted Fee is new adjusted fee excluding previously paid.
        # NOTE: Activity may include new adjusted amount with form changes.
        # fees_adj = activity.application_fee - (prev_app + prev_adj)
        fees_adj = activity.application_fee - prev_adj

        # Impose amendment fee.
        # fees_adj += self.get_amendment_fee_for(activity)

        fees_new = fees_adj
        activity.application_fee = fees_new
        activity.licence_fee = policy_licence_fee

        if licence_paid:
            # application fee is paid just pay adjustments.
            # no licence fee is included.
            fees_new = fees_new - activity.total_paid_amount
            activity.application_fee = fees_new

        if self.has_fee_exemption:
            activity.application_fee = 0
            activity.licence_fee = 0
            # activity.additional_fee = 0

        if fees_new < 0:
            # Refund amounts can be calculated from changes to the application
            # form which are then saved against the activity.
            # logger.info('{0}: REFUND {1} for licence ActivityID {2}'.format(
            #     'ApplicationFeePolicyForAmendment',
            #     fees_new,
            #     activity.id
            # ))
            pass

        if fees_new == 0:
            # Zero amount paid for amendment activity
            # logger.info('{0}: ZERO FEE for licence ActivityID {1}'.format(
            #     'ApplicationFeePolicyForAmendment',
            #     activity.id
            # ))
            pass

    def set_application_fee_from_attributes(self, attributes):
        '''
        Set the new application fee from updated attributes.

        Captures any changes to the application fee from the licence activity
        and applies it to the total fee for the activity.

        NOTE: Same calculation for set_application_fee_from_activity.
        '''
        fees_new = 0        # new application fee including adjusted amounts.
        policy_licence_fee = self.dynamic_attributes['fees']['licence']
        for activity in self.application.activities:
            # licence fee is zero so allow for additional fees.
            licence_paid = False if activity.total_paid_amount < 1 else True

            prev_adj = self.get_previous_adjusted_fee_for(activity)
            # prev_app = self.get_previous_application_fee_for(activity)

            # act_adj is the new adjusted fee WITH adjustments and application
            # fees copied from previous application.
            act_adj = attributes[
                'activity_attributes'][activity]['fees']['application']

            # Adjusted Fee is the new adjusted fee excluding the previous
            # adjustments and base application fees.
            # fees_adj = (act_adj - prev_adj) - prev_app
            fees_adj = act_adj - prev_adj

            # Include amendment fee.
            # fees_adj += self.get_amendment_fee_for(activity)

            if licence_paid:
                # base fee is paid just pay the adjustments difference.
                fees_lic = 0
                for purpose in activity.proposed_purposes.all():
                    fees_lic += purpose.licence_fee if purpose.is_payable \
                        else 0
                fees_new = fees_adj + fees_lic - activity.total_paid_amount
                policy_licence_fee = 0
            else:
                fees_new += fees_adj

        attributes['fees']['application'] = fees_new
        self.dynamic_attributes['fees']['application'] = fees_new
        attributes['fees']['licence'] = policy_licence_fee

        if self.has_fee_exemption:
            attributes['fees']['application'] = 0
            self.dynamic_attributes['fees']['application'] = 0
            attributes['fees']['licence'] = 0

    def get_previous_adjusted_fee_for(self, activity):
        """
        Get the aggregated adjusted fee for all previous purposes on the
        current selected activity.
        """
        prev_adjusted = 0
        prev_activity = activity.get_activity_from_previous()
        purposes_ids = self.get_form_purpose_ids_for(activity)
        for p in prev_activity.proposed_purposes.all():
            if p.purpose_id in purposes_ids and p.is_payable:
                prev_adjusted += p.adjusted_fee

        return prev_adjusted

    def get_previous_application_fee_for(self, activity):
        """
        Get the aggregated application fee for all previous purposes on the
        current selected activity.
        """
        prev_fee = 0
        prev_act = activity.get_activity_from_previous()
        purposes_ids = self.get_form_purpose_ids_for(activity)
        for p in prev_act.proposed_purposes.all():
            if p.purpose_id in purposes_ids and p.is_payable:
                prev_fee += p.application_fee

        return prev_fee


class ApplicationFeePolicyForRenew(ApplicationFeePolicy):
    '''
    A fee policy that applies to an application to renew a licence.
    - Applies a renewal fee from admin as the application fee amount.
    - Sets the licence fee from administration.
    - adjustment fees from the previous application are included in fee.
    - adjustment fees based on questions are added to the application fee.
    '''
    RENEW = Application.APPLICATION_TYPE_RENEWAL

    application = None
    dynamic_attributes = None   # Container for Activity fees.
    is_refreshing = False       # Flag indicating a page refresh.
    has_fee_exemption = False   # Allow exemption for zero amount invoice.

    def __init__(self, application):
        super(ApplicationFeePolicy, self).__init__()
        self.application = application
        if self.application.application_type == self.RENEW:
            self.init_dynamic_attributes()

    def __str__(self):
        return 'Renew fee policy for {0}{1}'.format(
           'Application: {app} '.format(app=self.application.id),
           'attributes : {att} '.format(att=self.dynamic_attributes),
        )

    @staticmethod
    def set_base_application_fee_for(purpose):
        '''
        Set the application fee to the renewal fee.
        '''
        purpose.base_application_fee = purpose.renewal_application_fee

    def get_licence_for(self):
        '''
        Gets the current licence associated with this renewal application.
        '''
        from wildlifecompliance.components.licences.models import (
            WildlifeLicence,
        )
        licence = None
        current_id = self.application.licence_id
        try:
            licence = WildlifeLicence.objects.get(
                id=current_id
            )
        except WildlifeLicence.DoesNotExist:
            pass
        except BaseException:
            raise Exception('Exception getting licence.')

        return licence

    def get_form_purpose_ids_for(self, activity):
        '''
        Gets a list of purpose identifiers for the selected activity which
        exist on the Application Form.
        '''
        purpose_ids = ApplicationFormDataRecord.objects.filter(
            application_id=self.application.id,
            licence_activity_id=activity.licence_activity_id,
        ).values_list('licence_purpose_id', flat=True).distinct()

        return purpose_ids

    def init_dynamic_attributes(self):
        '''
        Initialise the dynamic attributes on this policy with the application
        fee from previous purposes on the licence.
        '''
        fees = Application.calculate_base_fees(
            self.application.licence_purposes.values_list('id', flat=True))

        self.dynamic_attributes = {
            'fees': fees,
            'activity_attributes': {},
        }

        licence = self.get_licence_for()
        # previous adjusted fees for purpose is included with the renewal fee.
        fees_adj = 0
        fees_lic = 0
        for activity in licence.current_activities:
            purposes_ids = self.get_form_purpose_ids_for(activity)
            for p in activity.proposed_purposes.all():
                if p.purpose_id in purposes_ids and p.is_payable:
                    fees_adj += p.adjusted_fee
                    fees_adj += p.purpose.renewal_application_fee
                    fees_lic += p.purpose.base_licence_fee

        self.dynamic_attributes['fees']['application'] = fees_adj
        self.dynamic_attributes['fees']['licence'] = fees_lic

        if self.application.application_fee_paid:
            self.dynamic_attributes['fees'] = {'application': 0, 'licence': 0}

        self.is_refreshing = False

    @transaction.atomic
    def set_purpose_fees_for(self, activity):
        """
        Set all fees for the selected activity/purpose.
        """
        # get purposes from the application form.
        purposes_ids = self.get_form_purpose_ids_for(activity)
        # set the selected activity purpose base fees.
        for p_id in purposes_ids:
            purpose = [p for p in activity.purposes if p.id == p_id]
            p, c = ApplicationSelectedActivityPurpose.objects.get_or_create(
                selected_activity_id=activity.id,
                purpose_id=purpose[0].id
            )
            p.application_fee = p.purpose.renewal_application_fee
            p.licence_fee = p.purpose.base_licence_fee
            # NOTE: p.adjusted_fee not updated as this policy only updates the
            # licence and application fees.
            p.save()

    def set_application_fee(self):
        '''
        Set Application fee from the saved fees. Required when presentation is
        refreshed and no attributes are passed.
        '''
        self.is_refreshing = True
        REQ_NOPAY = ApplicationInvoice.PAYMENT_STATUS_NOT_REQUIRED
        REQ_AMEND = Application.CUSTOMER_STATUS_AMENDMENT_REQUIRED

        is_saved = True \
            if not self.application.payment_status == REQ_NOPAY else False

        if self.application.customer_status == REQ_AMEND or is_saved:
            self.set_dynamic_attributes_from_purpose_fees()
            return

        # Override the parent setter as Licence renewals need to include
        # previous adjustments paid for licence purpose.
        application_fees = 0
        licence_fees = 0
        licence = self.get_licence_for()

        for activity in licence.current_activities:
            is_selected = False
            purposes_ids = self.get_form_purpose_ids_for(activity)
            a_activity = self.application.activities.filter(
                licence_activity_id=activity.licence_activity_id
            ).first()

            if not a_activity:
                continue

            # save_app include both form adjustments and renewal fee.
            save_app = 0
            save_lic = 0
            for p in activity.proposed_purposes.all():

                if p.purpose_id in purposes_ids and p.is_payable:
                    # Only for purposes existing in copied form.
                    save_app += p.purpose.renewal_application_fee
                    save_lic += p.purpose.base_licence_fee
                    is_selected = True

            if is_selected:
                # adjustments and fees including previous adjustments paid.
                application_fees += save_app
                licence_fees += save_lic
                self.dynamic_attributes[
                    'activity_attributes'][a_activity] = {
                        'fees': application_fees
                    }

        self.dynamic_attributes['fees']['application'] = application_fees
        self.dynamic_attributes['fees']['licence'] = licence_fees

    def get_renewal_fee_for(self, activity):
        '''
        Get the application renewal fee set for this policy.
        '''
        from decimal import Decimal

        fee = 0
        licence = self.get_licence_for()
        for activity in licence.current_activities:
            purposes_ids = self.get_form_purpose_ids_for(activity)
            for p in activity.proposed_purposes.all():
                if p.purpose_id in purposes_ids and p.is_payable:
                    fee += p.purpose.renewal_application_fee

        return Decimal(fee)

    def set_application_fee_from_activity(self, activity):
        '''
        Set the application fee from an updated licence activity.

        Captures any changes to the application fee from the licence activity
        and applies it to the total fee for the activity.

        NOTE: Same calculation for set_application_fee_from_attributes.
        '''
        licence_paid = False if activity.total_paid_amount < 1 else True
        # policy_licence_fee = self.dynamic_attributes['fees']['licence']
        self.set_purpose_fees_for(activity)         # update fees on purpose.
        prev_adj = self.get_previous_adjusted_fee_for(activity)

        # Adjusted Fee is new adjusted fee excluding previously app fee.
        # NOTE: Activity may include new adjusted amount with form changes.
        fees_adj = activity.application_fee + prev_adj

        # Impose renewal fee.
        # fees_adj += self.get_renewal_fee_for(activity)

        fees_new = fees_adj
        activity.application_fee = fees_new
        # NOTE: Activity will have licence fee set from admin.
        fees_new = fees_new + activity.licence_fee

        if licence_paid:
            # application fee is paid just pay the adjustments.
            fees_lic = self.get_previous_licence_fee_for(activity)
            fees_new = fees_lic + fees_new - activity.total_paid_amount
            activity.application_fee = fees_new
            activity.licence_fee = 0

        if self.has_fee_exemption:
            activity.application_fee = 0
            activity.licence_fee = 0
            # activity.additional_fee = 0

        if fees_new < 0:
            # Refund for application fees can occur when paid activity
            # adjustment amounts are reduced and recovered from app fees.
            # logger.info('{0}: REFUND {1} for licence ActivityID {2}'.format(
            #     'ApplicationFeePolicyForRenew',
            #     fees_new,
            #     activity.id
            # ))
            pass

        if fees_new == 0:
            # Zero amount paid for activity
            # logger.info('{0}: ZERO FEE for licence ActivityID {1}'.format(
            #     'ApplicationFeePolicyForRenew',
            #     activity.id
            # ))
            pass

    def set_application_fee_from_attributes(self, attributes):
        '''
        Set the new application fee from updated attributes.

        Captures any changes to the application fee from the licence activity
        and applies it to the total fee for the activity.

        NOTE: Same calculation for set_application_fee_from_activity.
        '''
        fees_new = 0        # new application fee including adjusted amounts.
        policy_licence_fee = self.dynamic_attributes['fees']['licence']
        for activity in self.application.activities:
            # licence fee is zero so allow for additional fees.
            licence_paid = False if activity.total_paid_amount < 1 else True

            prev_adj = self.get_previous_adjusted_fee_for(activity)
            # prev_app = self.get_previous_application_fee_for(activity)

            # act_adj is the new adjusted fee WITH adjustments and application
            # fees copied from previous application.
            act_adj = attributes[
                'activity_attributes'][activity]['fees']['application']

            # Adjusted Fee is the new adjusted fee excluding the previous
            # adjustments and base application fees.
            # fees_adj = (act_adj + prev_adj) - prev_app
            fees_adj = act_adj + prev_adj

            # Include renewal fee.
            # fees_adj += self.get_renewal_fee_for(activity)

            if licence_paid:
                # base fee is paid just pay the adjustments difference.
                fees_lic = self.get_previous_licence_fee_for(activity)
                fees_new = fees_adj + fees_lic - activity.total_paid_amount
                policy_licence_fee = 0
            else:
                fees_new += fees_adj

        attributes['fees']['application'] = fees_new
        self.dynamic_attributes['fees']['application'] = fees_new
        attributes['fees']['licence'] = policy_licence_fee

        if self.has_fee_exemption:
            attributes['fees']['application'] = 0
            self.dynamic_attributes['fees']['application'] = 0
            attributes['fees']['licence'] = 0

    def get_previous_adjusted_fee_for(self, activity):
        """
        Get the aggregated adjusted fee for all previous purposes on the
        current selected activity.
        """
        prev_adjusted = 0
        prev_activity = activity.get_activity_from_previous()
        purposes_ids = self.get_form_purpose_ids_for(activity)
        for p in prev_activity.proposed_purposes.all():
            if p.purpose_id in purposes_ids and p.is_payable:
                prev_adjusted += p.adjusted_fee

        return prev_adjusted

    def get_previous_application_fee_for(self, activity):
        """
        Get the aggregated application fee for all previous purposes on the
        current selected activity.
        """
        prev_fee = 0
        prev_act = activity.get_activity_from_previous()
        purposes_ids = self.get_form_purpose_ids_for(activity)
        for p in prev_act.proposed_purposes.all():
            if p.purpose_id in purposes_ids and p.is_payable:
                prev_fee += p.application_fee

        return prev_fee

    def get_previous_licence_fee_for(self, activity):
        """
        Get the aggregated licence fee for all previous purposes on the
        current selected activity.
        """
        prev_fee = 0
        prev_act = activity.get_activity_from_previous()
        purposes_ids = self.get_form_purpose_ids_for(activity)
        for p in prev_act.proposed_purposes.all():
            if p.purpose_id in purposes_ids and p.is_payable:
                prev_fee += p.licence_fee

        return prev_fee


class ApplicationFeePolicyForNew(ApplicationFeePolicy):
    '''
    A fee policy that applies to an application for a new licence.
    - applies base purpose fees for both application and licence.
    - adjustment fees based on questions is added to the application fee.
    '''
    NEW = [
        Application.APPLICATION_TYPE_ACTIVITY,
        Application.APPLICATION_TYPE_NEW_LICENCE
    ]

    application = None
    dynamic_attributes = None   # Container for Activity fees.
    is_refreshing = False       # Flag indicating a page refresh.
    has_fee_exemption = False   # Allow exemption for zero amount invoice.

    def __init__(self, application):
        super(ApplicationFeePolicy, self).__init__()
        self.application = application
        if self.application.application_type in self.NEW:
            self.init_dynamic_attributes()

    def __str__(self):
        return 'New fee policy for {0}{1}'.format(
           'Application: {app} '.format(app=self.application.id),
           'attributes : {att} '.format(att=self.dynamic_attributes),
        )

    def init_dynamic_attributes(self):
        self.is_refreshing = False
        fees = Application.calculate_base_fees(
            self.application.licence_purposes.values_list('id', flat=True))

        if self.application.application_fee_paid:
            fees = {'application': 0, 'licence': 0}

        self.dynamic_attributes = {
            'fees': fees,
            'activity_attributes': {},
        }

    def set_application_fee(self):
        '''
        Set Application fee from the saved fees. Required when presentation is
        refreshed and no attributes are passed.
        '''
        self.is_refreshing = True
        self.set_dynamic_attributes_from_purpose_fees()

    def set_application_fee_from_activity(self, activity):
        '''
        Set the application and licence fees from an updated licence activity.

        Captures any changes to the application fee from the licence activity
        and applies it to the total fee for the activity.

        Owing amount is the licence fee with additional costs plus the
        application fee and adjustments less what has been paid.
        fees_new = fees_lic + fees_add + fees_app + fees_adj - paid

        NOTE: Same calculation for set_application_fee_from_attributes.
        '''
        fees_app_adj = 0
        fees_app = 0
        fees_lic_adj = 0
        fees_lic = 0

        paid_lic_tot = 0
        paid_app_tot = 0

        licence_paid = False if activity.total_paid_amount < 1 else True

        for purpose in activity.proposed_purposes.all():
            fees_app_adj += purpose.adjusted_fee if purpose.is_payable else 0
            fees_app += purpose.application_fee if purpose.is_payable else 0
            fees_lic += purpose.licence_fee if purpose.is_payable else 0
            fees_lic_adj += purpose.adjusted_licence_fee \
                if purpose.is_payable else 0

            paid_lic_tot += purpose.total_paid_adjusted_licence_fee \
                if purpose.is_payable else 0
            paid_app_tot += purpose.total_paid_adjusted_application_fee \
                if purpose.is_payable else 0

        fees_app_new = fees_app + fees_app_adj
        fees_lic_new = fees_lic + fees_lic_adj

        if licence_paid:
            # just calculate adjustments.
            fees_app_new = fees_app_adj + fees_app - paid_app_tot
            fees_lic_new = fees_lic_adj + fees_lic - paid_lic_tot
            activity.application_fee = 0
            fees_lic = 0

        # if fees_app_new != 0:
        activity.application_fee = fees_app_new
        activity.licence_fee = fees_lic_new

        if self.has_fee_exemption:
            activity.application_fee = 0
            activity.licence_fee = 0
            # activity.additional_fee = 0

        if fees_app_new < 0:
            # Refund amounts can be calculated from changes to the application
            # form which are then saved against the activity. Will occur for
            # requested amendments.
            # logger.info('{0}: REFUND {1} for licence ActivityID {2}'.format(
            #     'ApplicationFeePolicyForNew',
            #     fees_new,
            #     activity.id
            # ))
            pass

    def set_application_fee_from_attributes(self, attributes):
        '''
        Set the application and licence fees from updated attributes.

        Captures any changes to the application fee from the licence activity
        and applies it to the total fee for the application.

        Owing amount is the licence fee with additional costs plus the
        application fee and adjustments less what has been paid.
        fees_new = fees_lic + fees_add + fees_app + fees_adj - paid

        NOTE: Same calculation for set_application_fee_from_activity.
        '''
        fees_app_new = 0
        fees_lic_new = 0
        # policy_licence_fee = self.dynamic_attributes['fees']['licence']
        for activity in self.application.activities:
            licence_paid = False if activity.total_paid_amount < 1 else True
            # adjusted fees on activity includes application fee amount.
            # fees_adj = fees_adj + fees_app
            fees_app_adj = attributes[
                'activity_attributes'][activity]['fees']['application']
            fees_lic_adj = attributes[
                'activity_attributes'][activity]['fees']['licence']

            if licence_paid:
                fees_lic = 0
                fees_app = 0
                paid_lic_tot = 0
                paid_app_tot = 0
                for p in activity.proposed_purposes.all():
                    fees_lic += p.licence_fee if p.is_payable \
                        else 0
                    fees_app += p.application_fee if p.is_payable \
                        else 0
                    paid_lic_tot += p.total_paid_adjusted_licence_fee \
                        if p.is_payable else 0
                    paid_app_tot += p.total_paid_adjusted_application_fee \
                        if p.is_payable else 0

                fees_app_new = fees_app_adj - paid_app_tot
                fees_lic_new = fees_lic_adj - paid_lic_tot

            else:
                fees_app_new += fees_app_adj
                fees_lic_new += fees_lic_adj

        attributes['fees']['application'] = fees_app_new
        self.dynamic_attributes['fees']['application'] = fees_app_new
        attributes['fees']['licence'] = fees_lic_new

        if self.has_fee_exemption:
            attributes['fees']['application'] = 0
            self.dynamic_attributes['fees']['application'] = 0
            attributes['fees']['licence'] = 0

    def get_form_purpose_ids_for(self, activity):
        '''
        Gets a list of purpose identifiers for the selected activity which
        exist on the Application Form.
        '''
        purpose_ids = ApplicationFormDataRecord.objects.filter(
            application_id=self.application.id,
            licence_activity_id=activity.licence_activity_id,
        ).values_list('licence_purpose_id', flat=True).distinct()

        return purpose_ids
