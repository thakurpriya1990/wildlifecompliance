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
        if isinstance(purpose, ApplicationSelectedActivityPurpose):
            purpose.base_licence_fee = 0

    @staticmethod
    def set_previous_application_fee_for(purpose):
        '''
        The application fee is the same as the previous fee for Purpose.
        '''
        if isinstance(purpose, ApplicationSelectedActivityPurpose):
            previous = purpose.get_purpose_from_previous()
            prev_fee = previous.application_fee if previous else 0
            purpose.application_fee = prev_fee

    def init_dynamic_attributes(self):
        '''
        Initialise the dynamic attributes.
        '''
        self.is_refreshing = False
        application_fees = Application.calculate_base_fees(
                self.application.licence_purposes.values_list('id', flat=True)
            )['application']

        if self.application.application_fee > 0:
            # Apply previous application fee amount instead of base.
            prev_fees = self.application.previous_application.application_fee
            prev_fees = 0
            for activity in self.application.activities:
                prev = activity.get_activity_from_previous()
                purposes = prev.proposed_purposes.all() if prev else None
                for purpose in purposes:
                    prev_fees += purpose.application_fee

            application_fees = prev_fees

        self.dynamic_attributes = {
            'fees': {
                'application': application_fees,
                'licence': self.set_licence_fee(),
            },
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
            previous = p.get_purpose_from_previous()
            prev_fee = previous.application_fee if previous else 0
            p.application_fee = prev_fee
            p.licence_fee = self.set_licence_fee()
            p.additional_fee = 0
            p.save()

    def set_licence_fee_to_zero_for(self, activity):
        """
        No licence fee is paid for amended Activity/Purpose
        """
        activity.licence_fee = 0

    def set_application_fee_to_previous_base_for(self, activity):
        """
        Application base fee is the same as previous application fee.

        NOTE: Same as amend_adjusted_fee(self, attributes)

        """
        self.set_purpose_fees_for(activity)
        prev_total = self.get_previous_paid_total_for(activity)
        prev_act = self.get_previous_paid_actual_for(activity)

        fees_adj = activity.application_fee         # Adjusted Fees.
        prev_adj = prev_total - prev_act            # Previous Adjustments.
        fees = prev_act + prev_adj                  # Total Fees.
        new_adj = fees_adj - fees                   # New Adjusments.
        activity.application_fee = prev_act
        if new_adj < 0:
            # No over-payments are reimbursed for Amendment applications - just
            # pay new calculated fee.
            activity.application_fee = fees_adj
        else:
            activity.application_fee += new_adj

    def get_previous_paid_total_for(self, activity):
        """
        Set Licence fee as an aggregated amount of all new Activity/Purposes
        which have been added as part of this Licence Amendment.
        """
        prev_total = 0
        for purpose in activity.proposed_purposes.all():
            prev = purpose.get_purpose_from_previous()
            prev_app_fee = prev.application_fee if prev else 0
            prev_adj_fee = prev.adjusted_fee if prev else 0
            prev_total += prev_app_fee
            prev_total += prev_adj_fee    # Fee from questions.

        prev_activity = activity.get_activity_from_previous()
        if prev_activity and prev_activity.has_adjusted_application_fee:
            prev_total += prev_activity.additional_fee

        return prev_total

    def get_previous_paid_actual_for(self, activity):
        """
        Set Licence fee as an aggregated amount of all new Activity/Purposes
        which have been added as part of this Licence Amendment.
        """
        prev_actual = 0
        for purpose in activity.proposed_purposes.all():
            prev_purpose = purpose.get_purpose_from_previous()
            prev_fee = prev_purpose.application_fee if prev_purpose else 0
            prev_actual += prev_fee

        return prev_actual

    def set_licence_fee(self):
        """
        Set Licence fee as an aggregated amount of all new Activity/Purposes
        which have been added as part of this Licence Amendment.
        """
        from decimal import Decimal

        fee = 0

        return Decimal(fee)

    def set_application_fee(self):
        """
        Set Application fee from the saved model. Required when presentation is
        refreshed and no attributes are passed.
        """
        self.init_dynamic_attributes()
        self.is_refreshing = True

    def set_dynamic_attributes(self, attributes):
        '''
        Apply Licence Amendment Fee policy to dynamic attributes.
        '''
        if self.is_refreshing:
            return
        attributes = self.amend_adjusted_fee(attributes)

        self.dynamic_attrubutes = attributes

    def set_dynamic_attributes_for(self, activity):
        '''
        Apply Licence Amendment Fee policy to Activity fees.
        '''
        if self.is_refreshing:
            return
        self.set_licence_fee_to_zero_for(activity)
        self.set_application_fee_to_previous_base_for(activity)

    def amend_adjusted_fee(self, attributes):
        '''
        Amend only Application Fees for dynamic attributes.

        NOTE: Same as set_application_fee_to_previous_base_for(self, activity)

        '''
        prev_total = 0
        prev_act = 0
        new_act = 0
        fees_adj = 0

        for activity in self.application.activities:
            prev_total += self.get_previous_paid_total_for(activity)
            prev_act += self.get_previous_paid_actual_for(activity)
            # aggregate adjusted fees from calculated dynamic attributes.
            fees_adj += attributes[
                'activity_attributes'][activity]['fees']['application']

        prev_adj = prev_total - prev_act        # previous adjustments
        fees = prev_act + prev_adj + new_act    # total fees
        new_adj = fees_adj - fees               # new adjustments
        attributes['fees']['application'] = prev_act + new_act
        if new_adj < 0:
            # No over-payments are reimbursed for Amendment applications - just
            # pay new calculated fee.
            attributes['fees']['application'] = fees_adj
        else:
            attributes['fees']['application'] += new_adj

        return attributes

    def get_dynamic_attributes(self):
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
