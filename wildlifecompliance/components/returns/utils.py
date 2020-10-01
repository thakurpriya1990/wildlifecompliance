import abc
import logging

from datetime import datetime
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from wildlifecompliance.components.returns.models import (
    Return,
    ReturnTable,
    ReturnRow,
)
from wildlifecompliance.components.returns.utils_schema import Schema
from wildlifecompliance.utils import excel
from ledger.checkout.utils import (
    create_basket_session,
    create_checkout_session,
)
from ledger.payments.models import Invoice

logger = logging.getLogger(__name__)


def checkout(
        request,
        returns,
        lines=[],
        invoice_text=None,
        vouchers=[],
        internal=False,
        add_checkout_params={}):
    basket_params = {
        'products': lines,
        'vouchers': vouchers,
        'system': settings.WC_PAYMENT_SYSTEM_ID,
        'custom_basket': True,
    }
    basket, basket_hash = create_basket_session(request, basket_params)
    request.basket = basket

    checkout_params = {
        'system': settings.WC_PAYMENT_SYSTEM_ID,
        'fallback_url': request.build_absolute_uri('/'),
        'return_url': request.build_absolute_uri(
            reverse('external-returns-success-invoice')),
        'return_preload_url': request.build_absolute_uri('/'),
        'force_redirect': True,
        'proxy': True if internal else False,
        'invoice_text': invoice_text}
    checkout_params.update(add_checkout_params)
    print(' -------- main utils > checkout > checkout_params ---------- ')
    print(checkout_params)
    create_checkout_session(request, checkout_params)

    response = HttpResponseRedirect(reverse('checkout:index'))
    # inject the current basket into the redirect response cookies
    # or else, anonymous users will be directionless
    response.set_cookie(
        settings.OSCAR_BASKET_COOKIE_OPEN, basket_hash,
        max_age=settings.OSCAR_BASKET_COOKIE_LIFETIME,
        secure=settings.OSCAR_BASKET_COOKIE_SECURE, httponly=True
    )

    return response


def set_session_return(session, returns):
    print('setting session Return')
    session['wc_return'] = returns.id
    session.modified = True


def get_session_return(session):
    print('getting session Return')
    from wildlifecompliance.components.returns.models import Return
    if 'wc_return' in session:
        return_id = session['wc_return']
    else:
        raise Exception('Return not in Session')

    try:
        return Return.objects.get(id=return_id)
    except Return.DoesNotExist:
        raise Exception(
            'Return not found for return_id {}'.format(return_id))


def delete_session_return(session):
    if 'wc_return' in session:
        del session['wc_return']
        session.modified = True


def flush_checkout_session(session):
    keys = [
        'checkout_data',
        'checkout_invoice',
        'checkout_order_id',
        'checkout_return_url',
        'checkout_data',
    ]
    for key in keys:
        try:
            del session[key]
        except KeyError:
            continue


def bind_return_to_invoice(request, returns, invoice_ref):
    from wildlifecompliance.components.returns.models import ReturnInvoice

    logger = logging.getLogger('return_checkout')
    try:
        inv = Invoice.objects.get(reference=invoice_ref)
    except Invoice.DoesNotExist:

        logger.error(
            u'{} tried making an return with an incorrect invoice'.format(
                u'User {} with id {}'.format(
                    returns.submitter.get_full_name(),
                    returns.submitter.id)
                if returns.submitter else u'An anonymous user'
            )
        )

        raise Exception

    if inv.system not in [settings.WC_PAYMENT_SYSTEM_PREFIX]:

        logger.error(
            u'{} tried making an return with an invoice from another system \
                with reference number {}'.format(
                u'User {} with id {}'.format(
                    returns.submitter.get_full_name(),
                    returns.submitter.id)
                if returns.submitter else u'An anonymous user',
                inv.reference))

        raise Exception

    try:
        a = ReturnInvoice.objects.get(invoice_reference=invoice_ref)

        logger.error(
            u'{} tried making an return with an already used invoice with \
                reference number {}'.format(
                u'User {} with id {}'.format(
                    returns.submitter.get_full_name(),
                    returns.submitter.id)
                if returns.submitter else u'An anonymous user',
                a.invoice_reference))

        raise Exception

    except ReturnInvoice.DoesNotExist:

        logger.info(
            u'{} submitted return {}, creating new ReturnInvoice with \
                reference {}'.format(
                u'User {} with id {}'.format(
                    returns.submitter.get_full_name(),
                    returns.submitter.id)
                if returns.submitter else u'An anonymous user',
                returns.id,
                invoice_ref))

        app_inv, created = ReturnInvoice.objects.get_or_create(
            invoice_return=returns,
            invoice_reference=invoice_ref
        )
        returns.save()

        request.session['wc_last_return'] = returns.id

        # send out the invoice before the confirmation is sent
        # send_application_invoice(application)
        # for fully paid applications, fire off confirmation email
        # if application.paid:
        #    send_application_confirmation(application, request)


# def _is_post_data_valid(ret, tables_info, post_data):

#     table_rows = _get_table_rows_from_post(tables_info['name'], post_data)
#     schema = Schema(ret.return_type.get_schema_by_name(tables_info['name']))
#     print("=========from is post data valid")
#     print(table_rows)
#     # print(schema)

#     for table in tables_info:
#         print(table)
#         print(table['name'])
#         table_rows = _get_table_rows_from_post(table.get('name'), post_data)
#         if len(table_rows) == 0:
#             return False
#         schema = Schema(
#             ret.return_type.get_schema_by_name(table.get('name')))
#         if not schema.is_all_valid(table_rows):
#             return False
#     return True
def _is_post_data_valid(ret, tables_info, post_data):
    print(type(tables_info))
    print(tables_info)

    print("from utils===================")
    # print(ast.literal_eval(table))

    table_rows = _get_table_rows_from_post(tables_info, post_data)
    print("=======printing table rows=====")
    print(table_rows)
    if len(table_rows) == 0:
        return False
    schema = Schema(ret.return_type.get_schema_by_name(tables_info))
    print("===========Schema Info========")
    print(schema.is_all_valid(table_rows))
    if not schema.is_all_valid(table_rows):
        return False
    return True


def _get_table_rows_from_post(table_name, post_data):
    table_namespace = table_name + '::'
    by_column = dict([(key.replace(table_namespace, ''), post_data.getlist(
        key)) for key in post_data.keys() if key.startswith(table_namespace)])
    # by_column is of format {'col_header':[row1_val, row2_val,...],...}
    num_rows = len(
        list(
            by_column.values())[0]) if len(
        by_column.values()) > 0 else 0
    rows = []
    for row_num in range(num_rows):
        row_data = {}
        for key, value in by_column.items():
            row_data[key] = value[row_num]
        # filter empty rows.
        is_empty = True
        for value in row_data.values():
            if len(value.strip()) > 0:
                is_empty = False
                break
        if not is_empty:
            rows.append(row_data)
    return rows


def _create_return_data_from_post_data(ret, tables_info, post_data):
    rows = _get_table_rows_from_post(tables_info, post_data)
    if rows:
        return_table = ReturnTable.objects.get_or_create(
            name=tables_info, ret=ret)[0]
        # delete any existing rows as they will all be recreated
        return_table.returnrow_set.all().delete()
        return_rows = [
            ReturnRow(
                return_table=return_table,
                data=row) for row in rows]
        ReturnRow.objects.bulk_create(return_rows)


class ReturnUtility(object):
    '''
    An abstract ReturnUtility.
    '''
    __metaclass__ = abc.ABCMeta

    @staticmethod
    def default_return_due_date():
        '''
        Standard default due date for returns 12 months from submit date.
        '''
        from datetime import date, timedelta
        PERIOD_DAYS = 356

        today_plus_days = date.today() + timedelta(days=int(PERIOD_DAYS))

        return today_plus_days


class ReturnSpeciesUtility(ReturnUtility):
    '''
    Utility class to manage return species.
    '''
    _return = None                      # Composite Return for this utility.
    application_species_list = []       # Composite List for this utility.

    def __init__(self, a_return):
        super(ReturnUtility, self).__init__()
        self._return = a_return

    def set_species_list_future(self, a_species_list=None):
        '''
        Set list of species for future Return.
        '''
        FUTURE = Return.RETURN_PROCESSING_STATUS_FUTURE
        try:
            if self._return.processing_status == FUTURE:

                self.set_species_list(a_species_list)

        except BaseException as e:
            logger.error('{0} ReturnID: {1} - {2}'.format(
                'ReturnSpeciesUtil.set_species_list_future()',
                self._return.id,
                e
            ))

    def set_species_list(self, a_species_list=None):
        '''
        Set list of species for the Return.
        '''
        species_list = []
        return_table = []

        try:
            if isinstance(a_species_list, list):
                self.set_application_species_list(a_species_list)
            else:
                self.set_raw_species_list(a_species_list)

            species_list = self.get_species_list()

            for specie_name in species_list:
                name_id = self.get_id_from_species_name(specie_name)
                return_table.append(
                    ReturnTable(name=name_id, ret_id=str(self._return.id))
                )

            if return_table:
                ReturnTable.objects.bulk_create(return_table)

        except BaseException as e:
            logger.error('{0} ReturnID: {1} - {2}'.format(
                'ReturnSpeciesUtil.set_species_list()',
                self._return.id,
                e
            ))

    def get_species_list(self):
        '''
        Get list of species associated with this Return.
        '''
        species_list = []

        if self._return.return_type.with_application_species:
            species_list = self.get_application_species_list()

        elif self._return.return_type.with_regulated_species:
            species_list = self.get_regulated_species_list()

        return species_list

    def get_licence_species_list(self):
        '''
        Get regulated list of species associated with this Return.
        '''
        licence_purpose = self._return.returns_condition.licence_purpose
        return licence_purpose.purpose_species.all()

    def get_application_species_list(self):
        '''
        Get application list of species associated with this Return.
        '''
        species_names = []
        for name in self.application_species_list:
            species_names.append(name)

        unique_list = list(set(species_names))

        return unique_list

    def get_regulated_species_list(self):
        '''
        Get regulated list of species associated with this Return.
        '''
        species_names = []
        for specie in self._return.return_type.regulated_species.all():
            species_names.append(specie.species_name)

        unique_list = list(set(species_names))

        return unique_list

    def set_application_species_list(self, the_species_list):
        '''
        Set application list of species associated with this Return.
        '''
        self.application_species_list = the_species_list

    def set_raw_species_list(self, raw_species_list):
        '''
        Set raw list of species associated with this Return.

        Setter to attempt to build a species list from an unknown type.
        '''
        from wildlifecompliance.components.licences.pdf import HtmlParser

        the_species_list = None
        try:
            # attempt to build from raw data type with a html parser.
            parser = HtmlParser(raw_species_list)
            the_species_list = parser.species

        except TypeError:
            logger.warn('{0} ReturnID: {1}'.format(
                'No Species list available.', self._return.id
            ))
        except BaseException as e:
            logger.error('{0} ReturnID: {1} - {2}'.format(
                'ReturnSpeciesUtility.set_raw_species_list()',
                self._return.id, e
            ))

        self.application_species_list = the_species_list

    def get_raw_species_list_for(self, selected_activity):
        '''
        Get raw list of species associated with this Return.
        '''
        raw_species_list = None
        try:

            condition = self._return.condition
            selected_purpose = [
                p for p in selected_activity.proposed_purposes.all()
                if p.purpose_id == condition.licence_purpose_id
            ][0]
            # NOTE: Expectation that only ONE species 'Details' is created.
            # 'Details' may consist of a list of species in html format.
            raw_species_list = [
                d['details'] for d in selected_purpose.purpose_species_json
                if d['species']
            ][0]

        except IndexError:
            logger.warn('{0} ReturnID: {1}'.format(
                'No Species list available.', self._return.id
            ))
        except BaseException as e:
            logger.error('{0} ReturnID: {1} - {2}'.format(
                'ReturnSpeciesUtility.get_raw_species_list_for_activity()',
                self._return.id, e
            ))

        return raw_species_list

    def get_form_species_list(self):
        '''
        Get list of species common names from the application form.
        '''
        from wildlifecompliance.components.applications.models import (
            ApplicationFormDataRecord,
        )
        SPECIES = ApplicationFormDataRecord.COMPONENT_TYPE_SELECT_SPECIES
        species_qs = []

        try:
            species_qs = ApplicationFormDataRecord.objects.values(
                'value',
            ).filter(
                licence_activity_id=self._return.condition.licence_activity_id,
                licence_purpose_id=self._return.condition.licence_purpose_id,
                application_id=self._return.condition.application_id,
                component_type=SPECIES,
            )

        except BaseException as e:
            logger.error('{0} ReturnID: {1} - {2}'.format(
                'ReturnSpeciesUtility.get_species_list_from_application()',
                self._return.id,
                e
            ))

        return species_qs

    def get_species_name_from_id(self, species_id):
        '''
        Get string name of species from underscored species identifier.
        '''
        name = ''
        name = species_id.replace('_', ' ')

        return name

    def get_id_from_species_name(self, species_name):
        '''
        Get underscored string id of species from the species name.
        '''
        import re

        identifier = ''
        identifier = re.sub(' +', '_', species_name)

        return identifier


class SpreadSheet(object):
    """
    An utility object for Excel manipulation.
    """

    def __init__(self, _return, _filename):
        self.ret = _return
        self.filename = _filename
        self.errors = []
        self.rows_list = []

    def factory(self):
        """
        Simple Factory Method for spreadsheet types.
        :return: Specialised SpreadSheet.
        """

        return ReturnDataSheet(self.ret, self.filename)

    def get_table_rows(self):
        """
        Gets the row of data.
        :return: list format {'col_header':[row1_val,, row2_val,...],...}
        """
        wb = excel.load_workbook(self.filename)
        sheet_name = excel.get_sheet_titles(wb)[0]
        ws = wb[sheet_name]
        table_data = excel.TableData(ws, 1, 1)
        row_list = table_data._parse_rows()
        num_rows = row_list.__len__()
        for row_num in range(num_rows):
            row_data = {}
            for key, value in table_data.by_columns():
                if type(value[row_num]) is datetime:
                    row_data[key.lower()] = value[row_num].strftime("%d/%m/%Y")
                    continue
                row_data[key.lower()] = value[row_num] \
                    if value[row_num] is not None else ''

            # create deficiency key as part of row data
            table_name = self.ret.return_type.resources[0]['name']
            table_deficiency = table_name + '-deficiency-field'
            row_data[table_deficiency] = None

            self.rows_list.append(row_data)

        return self.rows_list

    def create_return_data(self):
        """
        Method to persist Return record.
        :return: Boolean
        """
        return False

    def is_valid(self):
        """
        Validates against schema.
        :return: Boolean
        """
        return False

    def get_error(self):
        """
        List of errors.
        :return:
        """

        return self.errors


class Regulation15Sheet(SpreadSheet):
    """
    Specialised utility object for Regulation 15 Spreadsheet.
    """
    REGULATION_15 = 'regulation-15'

    def __init__(self, _ret, _filename):
        super(Regulation15Sheet, self).__init__(_ret, _filename)
        self.schema = Schema(
            self.ret.return_type.get_schema_by_name(
                self.REGULATION_15))

    def is_valid(self):
        """
        Validates against schema.
        :return: Boolean
        """
        table_rows = self.get_table_rows()
        if len(table_rows) == 0:
            return False
        for row in table_rows:
            self.errors.append(self.schema.get_error_fields(row))

        return self.errors[1].__len__() == 0

    def create_return_data(self):
        """
        Method to persist Return record.
        :return:
        """
        if self.rows_list:
            return_table = ReturnTable.objects.get_or_create(
                name=self.REGULATION_15, ret=self.ret)[0]
            # delete any existing rows as they will all be recreated
            return_table.returnrow_set.all().delete()
            return_rows = [
                ReturnRow(
                    return_table=return_table,
                    data=row) for row in self.rows_list]
            ReturnRow.objects.bulk_create(return_rows)

        return True


class ReturnDataSheet(SpreadSheet):
    '''
    Specialised utility object for Return Data Spreadsheet.
    '''
    RETURN_DATA = 'return-data'

    def __init__(self, _ret, _filename):
        super(ReturnDataSheet, self).__init__(_ret, _filename)
        self.schema = Schema(
            self.ret.return_type.get_schema_by_name(
               self.ret.return_type.resources[0]['name']))

    def is_valid(self):
        '''
        Validates against schema.
        :return: Boolean
        '''
        table_rows = self.get_table_rows()
        if len(table_rows) == 0:
            return False
        for row in table_rows:
            self.errors.append(self.schema.get_error_fields(row))

        return self.errors[1].__len__() == 0

    def create_return_data(self):
        '''
        Method to persist Return record.
        :return:
        '''
        if self.rows_list:
            return_table = ReturnTable.objects.get_or_create(
                name=self.RETURN_DATA, ret=self.ret)[0]
            # delete any existing rows as they will all be recreated
            return_table.returnrow_set.all().delete()
            return_rows = [
                ReturnRow(
                    return_table=return_table,
                    data=row) for row in self.rows_list]
            ReturnRow.objects.bulk_create(return_rows)

        return True


class SchemaFieldVisitor(object):
    '''
    An Interface for Return Data schema field types which can be visited.
    '''
    __metaclass__ = abc.ABCMeta


class NumberFieldVisitor(SchemaFieldVisitor):
    '''
    An implementation of an operation declared by ReturnFieldVisitor to do an
    algorithm specific to Number types on the schema fields.
    '''
    def __init__(self, a_return, data_source):
        self._return = a_return
        self._data_source = data_source
        # Apply a traversal strategy.
        self._compositor = NumberFieldCompositor(a_return, data_source)

    def visit_apply_fee_field(self, apply_fee_field):
        self._apply_fee_field = apply_fee_field
        self._compositor.do_algorithm(self._apply_fee_field)


class SchemaFieldCompositor(object):
    '''
    Declares an interface common to all supported Schema Field algorithms.
    A context can use this interface to call a specific algorithm to act on
    a Special Field Element on a Return Schema.
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def do_algorithm(self, special_field_element):
        '''
        Performs an algorithm applicable to a Special Field Element.
        '''
        pass


class NumberFieldCompositor(SchemaFieldCompositor):
    '''
    A Class for objects which encapsulates an algorithm for inspecting a Number
    field on the Return schema.
    '''
    def __init__(self, a_return, data_source):
        self._return = a_return
        self._data_source = data_source
        self._children = set()

    def do_algorithm(self, special_field_element):
        self._field = special_field_element
        self.render()

    def render(self):
        '''
        Rendering algorithm to obtain field element from return schema.
        '''
        from wildlifecompliance.components.returns.services import (
            ReturnService,
        )

        try:
            # 1. loop through table.
            table = ReturnService.get_details_for(self._return)
            fields = self._return.resources[0]['schema']['fields']
            schema_fields = [f for f in fields if self._field.NAME in f]

            for schema_data in schema_fields:
                self._field.reset()
                data = table[0]['data']
                for row in data['gi_frame'].f_locals['rows']:

                    if schema_data[self._field.NAME] \
                            and schema_data['name'] in row:

                        self._field.parse_component(
                            component=row,
                            schema_name=schema_data['name']
                        )

        except TypeError:
            '''
            A TypeError will be thrown if no rows exist in the table. We just
            catch the exception and continue.
            '''
            self._field.field_name = schema_data['name']

        except KeyError:
            '''
            A KeyError will be thrown if the special field element does not
            exist in the schema. We just catch the exception and continue.
            '''
            self._field.field_name = schema_data['name']

        except Exception as e:
            self._field.field_name = schema_data['name']
            logger.error('ERR {0} ReturnID {1} Field {2}: {3}'.format(
                'NumberFieldCompositor.render()',
                self._return.id,
                self._field.field_name,
                e
            ))


class SpecialFieldElement(object):
    '''
    Special Field that defines an Accept operation that takes a
    ReturnVisitor as an argument.
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def accept(self, visitor):
        pass


class ApplyFeeFieldElement(SpecialFieldElement):
    '''
    An implementation of an SpecialFieldElement operation that takes a
    ReturnVisitor as an argument.

    The Applicable Fee field element value is aggregated for each Return
    schema item.
    '''
    NAME = 'ApplyFee'           # Field Element name.

    fee = 0
    dynamic_attributes = None   # Attributes collected from this field visit.
    _return = None              # the Return this field visit is applied to.
    data_source = None          # a data source to replace Return schema.
    is_refreshing = False       # Flag indicating a page refresh.
    is_updating = False         # Flag indicating if update or retrieval.
    field_name = None           # Name of schema field with ApplyFee.

    def __str__(self):
        return 'Field Element: {0}'.format(self._NAME)

    def accept(self, return_visitor):
        self._return = return_visitor._return
        self.data_source = return_visitor._data_source
        self.dynamic_attributes = {
            'fees': {
                'return': 0,
            },
        }
        # Add this field element to the visitor.
        return_visitor.visit_apply_fee_field(self)

        # Add relevant Fee policy to impact any Applicable Fees on this field.
        # NOTE: FeePolicy applies utilty.
        # self.fee_policy = ReturnFeePolicy.get_fee_policy_for(self.a_return)
        # if not self._data_source:  # No form data set.
        #     self.fee_policy.set_return_fee()
        #     self.is_refreshing = True

        # self.dynamic_attributes = self.fee_policy.get_dynamic_attributes()

    def set_updating(self, is_update):
        '''
        Sets the flag indicating that this visit is an update and not retrieve.
        (ie. for estimate calculation etc)
        '''
        self.is_updating = is_update

    def reset(self):
        '''
        Reset any field updates.
        '''
        if self.is_refreshing:
            # No user update with a page refesh.
            return

        self.fee = 0

    def parse_component(self, component, schema_name):
        '''
        Parse component to be visited.
        '''
        from decimal import Decimal

        self.field_name = schema_name

        if self.is_refreshing:
            # No user update with a page refesh.
            return

        if schema_name in component:
            '''
            Set the selected fields.
            '''
            amount = Decimal(
                component[schema_name]) * self._return.return_type.fee_amount
            self.fee += amount
            self.dynamic_attributes = {
                'fees': {
                    'return': self.fee,
                },
            }

    def get_dynamic_attributes(self):
        '''
        Gets the current dynamic attributes created by this Field Element.
        '''
        return self.dynamic_attributes

    def get_field_name(self):
        '''
        Get the name of the field element with Apply Fee.
        '''
        return self.field_name
