import logging
from datetime import datetime
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from wildlifecompliance.components.returns.models import (
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

    if inv.system not in ['0999']:

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
            returns=returns, invoice_reference=invoice_ref)
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
#         # print(table['name'])
#         # table_rows = _get_table_rows_from_post(table.get('name'), post_data)
#         # if len(table_rows) == 0:
#         #     return False
#         # schema = Schema(ret.return_type.get_schema_by_name(table.get('name')))
#         # if not schema.is_all_valid(table_rows):
#         #     return False
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
        if self.filename.name == 'regulation15.xlsx':
            return Regulation15Sheet(self.ret, self.filename)

        return self

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
                row_data[key.lower()] = value[row_num] if value[row_num] is not None else ''
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
