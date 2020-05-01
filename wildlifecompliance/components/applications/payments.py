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
    def get_dynamic_attributes(self):
        """
        Gets dynamic attributes with adjustments to fees made by applying this
        policy.
        """
        pass

    @abc.abstractmethod
    def set_dynamic_attributes(self):
        """
        Sets dynamic attributes with any adjustments to fees applying this
        policy.
        """
        pass

    @abc.abstractmethod
    def set_dynamic_attributes_for(self, activity):
        '''
        Sets dynamic attributes for a Licence Activity/Purpose with any
        adjustments to fees applying this policy.
        '''
        pass

    @abc.abstractmethod
    def set_application_fee(self):
        """
        Sets the application fee from what was previously saved on the model.
        """
        pass


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
        prev_fees = Application.calculate_base_fees(
                self.application.licence_purposes.values_list('id', flat=True)
            )['application']

        if prev_fees > 0:
            licence = self.get_licence_for()
            for activity in licence.current_activities:
                purposes_ids = self.get_form_purpose_ids_for(activity)
                for p in activity.proposed_purposes.all():
                    if p.purpose_id in purposes_ids:
                        prev_fees += p.application_fee

        application_fees = prev_fees

        self.dynamic_attributes = {
            'fees': {
                'application': application_fees,
                'licence': self.get_licence_fee(),
            },
            'activity_attributes': {},
        }

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
        if self.application.application_fee > 0:
            # application fee has been updated apply saved fees.
            save_fees = 0
            for activity in self.application.activities:
                purposes = activity.proposed_purposes.all()
                for purpose in purposes:
                    save_fees += purpose.application_fee

            application_fees = save_fees

            self.dynamic_attributes = {
                'fees': {
                    'application': application_fees,
                    'licence': self.get_licence_fee(),
                },
                'activity_attributes': {},
            }
        else:
            # no application fee re-calculate base from Application Form.
            self.init_dynamic_attributes()

        self.is_refreshing = True

    def set_application_fee_from_activity(self, activity):
        '''
        Set the application fee from an updated licence activity.

        NOTE: Same calculation for set_application_fee_from_attributes.
        '''
        self.set_purpose_fees_for(activity)         # update fees on purpose.
        fees_new = activity.application_fee         # new app + adjusted fee.
        prev_adj = self.get_previous_adjusted_fee_for(activity)

        # The new fee is the previous application base fee with the new
        # adjusted amount less the previous adjusted amount.
        # new fee = prev_fee + (fees_new - prev_fee) - prev_adj
        activity.application_fee = fees_new - prev_adj

    def set_application_fee_from_attributes(self, attributes):
        '''
        Set the new application fee from updated attributes.

        NOTE: Same calculation for set_application_fee_from_activity.
        '''
        prev_adj = 0        # total adjusted amount from previous activity.
        fees_new = 0        # new application fee including adjusted amounts.

        for activity in self.application.activities:
            prev_adj += self.get_previous_adjusted_fee_for(activity)
            # aggregate new activity fees from calculated dynamic attributes.
            fees_new += attributes[
                'activity_attributes'][activity]['fees']['application']

        # The new fee is the previous application base fee with the new
        # adjusted amount less the previous adjusted amount.
        # new fee = prev_fee + (fees_new - prev_fee) - prev_adj
        attributes['fees']['application'] = fees_new - prev_adj

    def get_previous_adjusted_fee_for(self, activity):
        """
        Get the aggregated adjusted fee for all previous purposes on the
        current selected activity.
        """
        prev_adjusted = 0
        prev_activity = activity.get_activity_from_previous()
        purposes_ids = self.get_form_purpose_ids_for(activity)
        for p in prev_activity.proposed_purposes.all():
            if p.purpose_id in purposes_ids:
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
            if p.purpose_id in purposes_ids:
                prev_fee += p.application_fee

        return prev_fee

    def set_dynamic_attributes_for(self, activity):
        '''
        Set application fees in attributes container to match the application
        fee on the selected activity licence.
        '''
        if self.is_refreshing:
            return
        self.set_licence_fee_to_zero_for(activity)
        self.set_application_fee_from_activity(activity)

    def set_dynamic_attributes(self, attributes):
        '''
        Set application fees in attributes container to new fee attributes.
        '''
        if self.is_refreshing:
            return
        self.set_application_fee_from_attributes(attributes)
        self.dynamic_attrubutes = attributes

    def get_dynamic_attributes(self):
        '''
        Gets the container of attributes set on this policy.
        '''
        return self.dynamic_attributes


class ApplicationFeePolicyForRenew(ApplicationFeePolicy):
    '''
    A fee policy that applies to an application to renew a licence.
    - maintains the application fee and licence fee from previous licence.
    - adjustment fees from the previous application are excluded.
    - adjustment fees based on questions are added to the application fee.
    '''
    RENEW = Application.APPLICATION_TYPE_RENEWAL

    is_refreshing = False       # Flag indicating a page refresh.

    def __init__(self, application):
        self._application = application
        if self._application.application_type == self.RENEW:
            self.init_dynamic_attributes()

    def __str__(self):
        return 'Renew fee policy for {0}{1}'.format(
           'Application: {app} '.format(app=self.application.id),
           'attributes : {att} '.format(att=self.dynamic_attributes),
        )

    def init_dynamic_attributes(self):
        self.is_refreshing = False
        self._dynamic_attributes = {
            'fees': Application.calculate_base_fees(
                self._application.licence_purposes.values_list('id', flat=True)
            ),
            'activity_attributes': {},
        }

    def set_application_fee(self):
        """
        Set Application fee from the saved model.
        """
        self.is_refreshing = True
        application_fees = Application.calculate_base_fees(
                self._application.licence_purposes.values_list('id', flat=True)
            )['application']
        licence_fees = Application.calculate_base_fees(
                self._application.licence_purposes.values_list('id', flat=True)
            )['licence']

        if self._application.application_fee > 0:
            application_fees = self._application.application_fee

        self._dynamic_attributes = {
            'fees': {
                'application': application_fees,
                'licence': licence_fees,
                },
            'activity_attributes': {},
        }

    def set_dynamic_attributes(self, attributes):
        if self.is_refreshing:
            return
        self._dynamic_attributes = attributes

    def get_dynamic_attributes(self):
        return self._dynamic_attributes

    def set_dynamic_attributes_for(self, activity):
        if self.is_refreshing:
            return


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
        self.dynamic_attributes = {
            'fees': Application.calculate_base_fees(
                self.application.licence_purposes.values_list('id', flat=True)
            ),
            'activity_attributes': {},
        }

    def set_purpose_fees_for(self, activity):
        """
        Set all fees for the selected activity/purpose.

        """
        # get purposes from the application form.
        purpose_ids = ApplicationFormDataRecord.objects.filter(
            application_id=activity.application_id,
            licence_activity_id=activity.licence_activity_id,
        ).values_list('licence_purpose_id', flat=True).distinct()
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

    def set_application_fee(self):
        """
        Set Application fee from the saved model.
        """
        self.is_refreshing = True
        application_fees = Application.calculate_base_fees(
                self.application.licence_purposes.values_list('id', flat=True)
            )['application']
        licence_fees = Application.calculate_base_fees(
                self.application.licence_purposes.values_list('id', flat=True)
            )['licence']

        if self.application.application_fee > 0:
            application_fees = self.application.application_fee

        self.dynamic_attributes = {
            'fees': {
                'application': application_fees,
                'licence': licence_fees,
                },
            'activity_attributes': {},
        }

    def set_dynamic_attributes(self, attributes):
        if self.is_refreshing:
            return
        self.dynamic_attributes = attributes

    def get_dynamic_attributes(self):
        return self.dynamic_attributes

    def set_dynamic_attributes_for(self, activity):
        '''
        Sets any updated attribute fees associated with the Activity.
        '''
        if self.is_refreshing:
            return
        self.set_purpose_fees_for(activity)
