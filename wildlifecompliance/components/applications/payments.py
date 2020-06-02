import abc
import logging

from wildlifecompliance.components.applications.models import (
    Application,
    ApplicationSelectedActivityPurpose,
    ApplicationFormDataRecord,
)

logger = logging.getLogger(__name__)
logging.disable(logging.NOTSET)
logger.setLevel(logging.DEBUG)


class ApplicationFeePolicy(object):
    """
    A Payment Policy Interface for Licence Applications.
    """
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
        Gets the checkout product lines for this application which inlcudes
        fee for both the application and licence activities.
        """
        from ledger.checkout.utils import calculate_excl_gst

        product_lines = []

        # application.
        activities_with_fees = [
            a for a in application.activities if a.application_fee > 0]

        for activity in activities_with_fees:
            product_lines.append({
                'ledger_description': '{} (Application Fee)'.format(
                    activity.licence_activity.name),
                'quantity': 1,
                'price_incl_tax': str(activity.application_fee),
                'price_excl_tax': str(calculate_excl_gst(
                    activity.application_fee)),
                'oracle_code': ''
            })

        # licence activities.
        activities_with_fees = [
            a for a in application.activities if a.licence_fee > 0]

        for activity in activities_with_fees:
            product_lines.append({
                'ledger_description': '{} (Licence Fee)'.format(
                    activity.licence_activity.name),
                'quantity': 1,
                'price_incl_tax': str(activity.licence_fee),
                'price_excl_tax': str(calculate_excl_gst(
                        activity.licence_fee)),
                'oracle_code': ''
            })

        return product_lines

    @abc.abstractmethod
    def set_application_fee(self):
        """
        Sets the application fee from what was previously saved on the model.
        """
        pass

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
        Set any updated attribute fees associated with the Activity.
        '''
        try:
            if self.is_refreshing:
                return
            self.set_application_fee_on_purpose_for(activity)
            self.set_application_fee_from_activity(activity)
            self.set_dynamic_attributes_from_purpose_fees()

        except BaseException:
            raise

    def set_dynamic_attributes_from_purpose_fees(self):
        '''
        Set the fee attributes on this policy to licence activity purposes.
        '''
        has_purpose = False     # No purposes will exist with pre-submission.
        fees_app_tot = 0
        fees_lic_tot = 0
        for activity in self.application.activities:
            fees_app = 0
            fees_adj = 0
            fees_lic = 0
            for p in activity.proposed_purposes.all():
                fees_adj += p.adjusted_fee if p.is_proposed else 0
                fees_app += p.application_fee if p.is_proposed else 0
                fees_lic += p.licence_fee if p.is_proposed else 0
                has_purpose = True
            paid_amt = activity.total_paid_amount
            fees_app = fees_app + fees_adj
            if paid_amt > 0:        # amount already paid on application.
                fees_app = fees_lic + fees_app - paid_amt
                fees_lic = 0
            fees_app_tot += fees_app
            fees_lic_tot += fees_lic

        if has_purpose:
            self.dynamic_attributes['fees']['application'] = fees_app_tot
            self.dynamic_attributes['fees']['licence'] = fees_lic_tot

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
    - maintains a base application fee from previous application.
    - applies no licence fee.
    - all adjustment fees from the previous application are excluded.
    - adjustment fees based on questions are added to the application fee.
    '''
    AMEND = Application.APPLICATION_TYPE_AMENDMENT

    application = None
    dynamic_attributes = None   # Container for Activity fees.
    is_refreshing = False       # Flag indicating a page refresh.

    def __init__(self, application):
        super(ApplicationFeePolicy, self).__init__()
        self.application = application
        if self.application.application_type == self.AMEND:
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

        application_fees = 0
        licence = self.get_licence_for()
        for activity in licence.current_activities:
            purposes_ids = self.get_form_purpose_ids_for(activity)
            for p in activity.proposed_purposes.all():
                if p.purpose_id in purposes_ids and p.is_proposed:
                    application_fees += p.application_fee

        self.dynamic_attributes = {
            'fees': {
                'application': application_fees,
                'licence': self.get_licence_fee(),
            },
            'activity_attributes': {},
        }

        if self.application.application_fee_paid:
            self.dynamic_attributes['fees'] = {'application': 0, 'licence': 0}

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
            previous = p.get_purpose_from_previous()
            p.application_fee = previous.application_fee if previous else 0
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

    def set_application_fee(self):
        """
        Set Application fee from the saved model. Required when presentation is
        refreshed and no attributes are passed.
        """
        self.is_refreshing = True
        self.set_dynamic_attributes_from_purpose_fees()

    def set_application_fee_from_activity(self, activity):
        '''
        Set the application fee from an updated licence activity.

        Captures any changes to the application fee from the licence activity
        and applies it to the total fee for the activity.

        Owing amount is the licence fee with additional costs plus the
        application fee and adjustments less what has been paid.
        fees_new = fees_lic + fees_add + fees_app + fees_adj - paid

        NOTE: Same calculation for set_application_fee_from_attributes.
        '''
        licence_paid = False if activity.total_paid_amount < 1 else True
        policy_licence_fee = self.dynamic_attributes['fees']['licence']
        self.set_purpose_fees_for(activity)         # update fees on purpose.
        prev_adj = self.get_previous_adjusted_fee_for(activity)

        fees_new = activity.application_fee - prev_adj
        if licence_paid:
            # application fee is paid just pay adjustments.
            # no licence fee is included.
            activity.application_fee = 0
            fees_new = fees_new - activity.total_paid_amount

        if fees_new != 0:
            activity.application_fee = fees_new
        activity.licence_fee = policy_licence_fee

    def set_application_fee_from_attributes(self, attributes):
        '''
        Set the new application fee from updated attributes.

        Captures any changes to the application fee from the licence activity
        and applies it to the total fee for the activity.

        Owing amount is the licence fee with additional costs plus the
        application fee and adjustments less what has been paid.
        fees_new = fees_lic + fees_add + fees_app + fees_adj - paid

        NOTE: Same calculation for set_application_fee_from_activity.
        '''
        fees_new = 0        # new application fee including adjusted amounts.
        policy_licence_fee = self.dynamic_attributes['fees']['licence']
        for activity in self.application.activities:
            # licence fee is zero so allow for additional fees.
            licence_paid = False if activity.total_paid_amount < 1 else True

            old_adj = self.get_previous_adjusted_fee_for(activity)
            # aggregate new activity fees from calculated dynamic attributes.
            act_adj = attributes[
                'activity_attributes'][activity]['fees']['application']
            fees_adj = act_adj - old_adj

            if licence_paid:
                # base fee is paid just pay the adjustments difference.
                fees_lic = 0
                for purpose in activity.proposed_purposes.all():
                    fees_lic += purpose.licence_fee if purpose.is_proposed \
                        else 0
                fees_new = fees_adj + fees_lic - activity.total_paid_amount
                policy_licence_fee = 0
            else:
                fees_new += fees_adj

        if fees_new != 0:
            attributes['fees']['application'] = fees_new
            self.dynamic_attributes['fees']['application'] = fees_new
        attributes['fees']['licence'] = policy_licence_fee

    def get_previous_adjusted_fee_for(self, activity):
        """
        Get the aggregated adjusted fee for all previous purposes on the
        current selected activity.
        """
        prev_adjusted = 0
        prev_activity = activity.get_activity_from_previous()
        purposes_ids = self.get_form_purpose_ids_for(activity)
        for p in prev_activity.proposed_purposes.all():
            if p.purpose_id in purposes_ids and p.is_proposed:
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
            if p.purpose_id in purposes_ids and p.is_proposed:
                prev_fee += p.application_fee

        return prev_fee


class ApplicationFeePolicyForRenew(ApplicationFeePolicy):
    '''
    A fee policy that applies to an application to renew a licence.
    - Sets the application fee and licence fee from administration.
    - adjustment fees from the previous application are included in fee.
    - adjustment fees based on questions are added to the application fee.
    '''
    RENEW = Application.APPLICATION_TYPE_RENEWAL

    application = None
    dynamic_attributes = None   # Container for Activity fees.
    is_refreshing = False       # Flag indicating a page refresh.

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
        # previous adjusted fees for purpose is included in the total fee.
        fees_adj = 0
        for activity in licence.current_activities:
            purposes_ids = self.get_form_purpose_ids_for(activity)
            for p in activity.proposed_purposes.all():
                if p.purpose_id in purposes_ids and p.is_proposed:
                    fees_adj += p.adjusted_fee

        self.dynamic_attributes['fees']['application'] += fees_adj

        if self.application.application_fee_paid:
            self.dynamic_attributes['fees'] = {'application': 0, 'licence': 0}

        self.is_refreshing = False

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
        fees_adj = 0
        fees_app = 0
        fees_lic = 0

        for purpose in activity.proposed_purposes.all():
            fees_adj += purpose.adjusted_fee if purpose.is_proposed else 0
            fees_app += purpose.application_fee if purpose.is_proposed else 0
            fees_lic += purpose.licence_fee if purpose.is_proposed else 0

        licence_paid = False if activity.total_paid_amount < 1 else True
        # self.set_purpose_fees_for(activity)         # update fees on purpose.

        fees_new = fees_app + fees_adj
        if licence_paid:
            # application fee is paid just pay adjustments.
            fees_new = fees_lic + fees_new - activity.total_paid_amount
            activity.application_fee = 0
            fees_lic = 0

        if fees_new != 0:
            activity.application_fee = fees_new
        activity.licence_fee = fees_lic

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
        fees_new = 0        # new application fee including adjusted amounts.
        policy_licence_fee = self.dynamic_attributes['fees']['licence']
        for activity in self.application.activities:
            licence_paid = False if activity.total_paid_amount < 1 else True
            act_adj = attributes[
                'activity_attributes'][activity]['fees']['application']

            fees_adj = act_adj
            if licence_paid:
                # base fee is paid just pay the adjustments difference.
                fees_lic = 0
                for purpose in activity.proposed_purposes.all():
                    fees_lic += purpose.licence_fee if purpose.is_proposed \
                        else 0
                fees_new = fees_adj + fees_lic - activity.total_paid_amount
                policy_licence_fee = 0
            else:
                fees_new += fees_adj

        if fees_new != 0:
            attributes['fees']['application'] = fees_new
            self.dynamic_attributes['fees']['application'] = fees_new
        attributes['fees']['licence'] = policy_licence_fee

    def set_application_fee_on_purpose_for(self, activity):
        """
        Set all fees for the selected activity/purpose.

        """
        # get purposes from the application form.
        purpose_ids = self.get_form_purpose_ids_for(activity)
        # set the selected activity purpose base fees.
        for p_id in purpose_ids:
            purpose = [p for p in activity.purposes if p.id == p_id]
            p, c = ApplicationSelectedActivityPurpose.objects.get_or_create(
                selected_activity_id=activity.id,
                purpose_id=purpose[0].id
            )
            p.application_fee = purpose[0].base_application_fee
            p.licence_fee = purpose[0].base_licence_fee
            p.save()

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

    def get_previous_adjusted_fee_for(self, activity):
        """
        Get the aggregated adjusted fee for all previous purposes on the
        current selected activity.
        """
        prev_adjusted = 0
        prev_activity = activity.get_activity_from_previous()
        purposes_ids = self.get_form_purpose_ids_for(activity)
        for p in prev_activity.proposed_purposes.all():
            if p.purpose_id in purposes_ids and p.is_proposed:
                prev_adjusted += p.adjusted_fee

        return prev_adjusted

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
            p.application_fee = purpose[0].base_application_fee
            p.licence_fee = purpose[0].base_licence_fee
            # NOTE: p.adjusted_fee not updated as this policy only updates the
            # licence and application fees.
            p.save()


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
        fees_adj = 0
        fees_app = 0
        fees_lic = 0

        licence_paid = False if activity.total_paid_amount < 1 else True

        for purpose in activity.proposed_purposes.all():
            fees_adj += purpose.adjusted_fee if purpose.is_proposed else 0
            fees_app += purpose.application_fee if purpose.is_proposed else 0
            fees_lic += purpose.licence_fee if purpose.is_proposed else 0

        fees_new = fees_app + fees_adj
        if licence_paid:
            # just calculate adjustments.
            fees_new = fees_lic + fees_new - activity.total_paid_amount
            activity.application_fee = 0
            fees_lic = 0

        if fees_new != 0:
            activity.application_fee = fees_new
        activity.licence_fee = fees_lic

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
        fees_new = 0
        policy_licence_fee = self.dynamic_attributes['fees']['licence']
        for activity in self.application.activities:
            licence_paid = False if activity.total_paid_amount < 1 else True
            # adjusted fees on activity includes application fee amount.
            # fees_adj = fees_adj + fees_app
            fees_adj = attributes[
                'activity_attributes'][activity]['fees']['application']

            if licence_paid:
                fees_lic = 0
                for purpose in activity.proposed_purposes.all():
                    fees_lic += purpose.licence_fee if purpose.is_proposed \
                        else 0
                fees_new = fees_adj + fees_lic - activity.total_paid_amount
                policy_licence_fee = 0
            else:
                fees_new += fees_adj

        if fees_new != 0:
            attributes['fees']['application'] = fees_new
            self.dynamic_attributes['fees']['application'] = fees_new
        attributes['fees']['licence'] = policy_licence_fee

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
