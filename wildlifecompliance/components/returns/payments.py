import abc
import logging

from wildlifecompliance.components.returns.models import (
    ReturnType,
)

logger = logging.getLogger(__name__)
logging.disable(logging.NOTSET)
logger.setLevel(logging.DEBUG)


class ReturnFeePolicy(object):
    '''
    A Payment Policy Interface for the Licence Return.
    '''
    __metaclass__ = abc.ABCMeta

    GST_FREE = True

    @staticmethod
    def get_fee_policy_for(a_return):

        SHEET = ReturnType.FORMAT_SHEET
        QUESTION = ReturnType.FORMAT_QUESTION
        DATA = ReturnType.FORMAT_DATA

        get_policy = {
            SHEET: ReturnFeePolicyForSheet(a_return),
            QUESTION: ReturnFeePolicyForQuestion(a_return),
            DATA: ReturnFeePolicyForData(a_return)
        }
        policy = get_policy.get(a_return.format)

        return policy

    @staticmethod
    def get_fee_product_lines_for(a_return):
        """
        Gets the checkout product lines for a return which includes the fees.
        """
        from ledger.checkout.utils import calculate_excl_gst

        product_lines = []
        oracle_code = a_return.return_type.oracle_account_code

        product_lines.append({
            'ledger_description': 'submission fee for {0}'.format(
                a_return.lodgement_number),
            'quantity': 1,
            'price_incl_tax': str(a_return.return_fee),
            'price_excl_tax': str(calculate_excl_gst(
                a_return.return_fee)),
            'oracle_code': oracle_code
        })

        return product_lines

    @abc.abstractmethod
    def set_return_fee(self):
        """
        Sets the return fee to what was previously saved on the model.
        """
        pass

    def set_dynamic_attributes(self, attributes):
        '''
        Set fees in attributes container for managing dynamic fee calculation.
        '''
        try:
            self.set_return_fee_from_attributes(attributes)
            self.dynamic_attributes = attributes

        except BaseException:
            raise

    def get_dynamic_attributes(self):
        '''
        Get the container of attributes set on this policy.
        '''
        return self.dynamic_attributes


class ReturnFeePolicyForData(ReturnFeePolicy):
    '''
    A fee policy that applies to a return submission for a Species Stock.
    - maintains a base fee for submission.
    '''
    DATA = ReturnType.FORMAT_DATA

    the_return = None
    dynamic_attributes = None   # Container to dynamically calculate fees.
    is_refreshing = False       # Flag indicating a page refresh.

    def __init__(self, a_return):
        super(ReturnFeePolicy, self).__init__()
        self.the_return = a_return
        if self.the_return.format == self.DATA:
            self.init_dynamic_attributes()

    def __str__(self):
        return 'Return fee policy for {0}'.format(
           'Return: {ret} '.format(ret=self.the_return.id),
        )

    def init_dynamic_attributes(self):
        '''
        Initialise the dynamic attributes on this policy for the return fee.
        '''
        self.is_refreshing = False

        return_fees = self.the_return.return_type.fee_amount
        is_required = self.the_return.return_type.fee_required

        self.dynamic_attributes = {
            'fees': {
                'return': return_fees if is_required else 0,
            },
        }

        if self.the_return.return_fee_paid:
            self.dynamic_attributes['fees'] = {'return': 0}

    def set_return_fee(self):
        '''
        Set Return fee from the saved model. Required when presentation is
        refreshed and no attributes are passed.

        calculate return fee from the return data table.
        '''
        self.is_refreshing = True
        # self.init_dynamic_attributes()
        self.calculate_table_fee()

    def set_return_fee_from_attributes(self, attributes):
        '''
        Set the new return fee from updated attributes.

        Captures any changes to the return fee.
        '''
        fees_new = attributes['fees']['return']
        # policy_return_fee = self.dynamic_attributes['fees']['return']

        if fees_new != 0:
            self.dynamic_attributes['fees']['return'] = fees_new

        # attributes['fees']['return'] = policy_return_fee

    def calculate_table_fee(self):
        '''
        Dynamically calculates applicable fees from Return data schema table.
        '''
        from wildlifecompliance.components.returns.utils import (
            NumberFieldVisitor,
            ApplyFeeFieldElement,
        )

        # Set schema field to be visited.
        schema_field = NumberFieldVisitor(self.the_return, self.DATA)
        for_apply_fee_fields = ApplyFeeFieldElement()
        for_apply_fee_fields.set_updating(True)
        for_apply_fee_fields.accept(schema_field)

        dynamic_attributes = for_apply_fee_fields.get_dynamic_attributes()
        self.set_dynamic_attributes(dynamic_attributes)


class ReturnFeePolicyForSheet(ReturnFeePolicy):
    '''
    A fee policy that applies to fees associated with a Return running sheet.
    - maintains a fee for transfer of stock.
    '''
    SHEET = ReturnType.FORMAT_SHEET

    the_return = None
    dynamic_attributes = None   # Container to dynamically calculate fees.
    is_refreshing = False       # Flag indicating a page refresh.

    def __init__(self, a_return):
        super(ReturnFeePolicy, self).__init__()
        self.the_return = a_return
        if self.the_return.format == self.SHEET:
            self.init_dynamic_attributes()

    def __str__(self):
        return 'Return fee policy for {0}'.format(
           'Return: {ret} '.format(ret=self.the_return.id),
        )

    def init_dynamic_attributes(self):
        '''
        Initialise the dynamic attributes on this policy for the return fee.
        '''
        self.is_refreshing = False

        return_fees = 0

        self.dynamic_attributes = {
            'fees': {
                'return': return_fees,
            },
        }

        if self.the_return.return_fee_paid:
            self.dynamic_attributes['fees'] = {'return': 0}

    def set_return_fee(self):
        '''
        Set Return fee from the saved model. Required when presentation is
        refreshed and no attributes are passed.

        TODO: the return fee on running sheets is for stock transfers and unit
        cost is not stored. Applying the admin fee amount as generic unit cost.
        '''
        self.is_refreshing = True

        return_fees = self.the_return.return_type.fee_amount
        is_required = True

        self.dynamic_attributes = {
            'fees': {
                'return': return_fees if is_required else 0,
            },
        }

    def set_return_fee_from_attributes(self, attributes):
        '''
        Set the new return fee from updated attributes.

        Captures any changes to the return fee.
        '''
        fees_new = 0
        policy_return_fee = self.dynamic_attributes['fees']['return']

        if fees_new != 0:
            attributes['fees']['return'] = fees_new
            self.dynamic_attributes['fees']['return'] = fees_new
        attributes['fees']['return'] = policy_return_fee


class ReturnFeePolicyForQuestion(ReturnFeePolicy):
    '''
    A fee policy that applies to a return submission for responses for
    Questions.
    - maintains a fee for based on responses.
    '''
    QUESTION = ReturnType.FORMAT_QUESTION

    the_return = None
    dynamic_attributes = None   # Container to dynamically calculate fees.
    is_refreshing = False       # Flag indicating a page refresh.

    def __init__(self, a_return):
        super(ReturnFeePolicy, self).__init__()
        self.the_return = a_return
        if self.the_return.format == self.QUESTION:
            self.init_dynamic_attributes()

    def __str__(self):
        return 'Return fee policy for {0}'.format(
           'Return: {ret} '.format(ret=self.the_return.id),
        )

    def init_dynamic_attributes(self):
        '''
        Initialise the dynamic attributes on this policy for the return fee.
        '''
        self.is_refreshing = False

        return_fees = 0

        self.dynamic_attributes = {
            'fees': {
                'return': return_fees,
            },
        }

        if self.the_return.return_fee_paid:
            self.dynamic_attributes['fees'] = {'return': 0}

    def set_return_fee(self):
        '''
        Set Return fee from the saved model. Required when presentation is
        refreshed and no attributes are passed.
        '''
        self.is_refreshing = True
        self.init_dynamic_attributes()

    def set_return_fee_from_attributes(self, attributes):
        '''
        Set the new return fee from updated attributes.

        Captures any changes to the return fee.
        '''
        fees_new = 0
        policy_return_fee = self.dynamic_attributes['fees']['return']

        if fees_new != 0:
            attributes['fees']['return'] = fees_new
            self.dynamic_attributes['fees']['return'] = fees_new
        attributes['fees']['return'] = policy_return_fee
