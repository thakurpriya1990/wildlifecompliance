import ast
import logging

from concurrency.exceptions import RecordModifiedError

from django.core.exceptions import ValidationError, FieldError
from django.db import transaction
from django.db.utils import IntegrityError

from ledger.checkout.utils import calculate_excl_gst

from wildlifecompliance.components.main.utils import (
    checkout,
    flush_checkout_session
)
from wildlifecompliance.components.returns.utils_schema import Schema
from wildlifecompliance.components.returns.models import (
    Return,
    ReturnType,
    ReturnTable,
    ReturnInvoice,
    ReturnRow,
    ReturnUserAction,
)

from wildlifecompliance.components.returns.email import (
    send_sheet_transfer_email_notification
)

logger = logging.getLogger(__name__)


class ReturnService(object):
    """
    Services available for Licence Species Returns.
    """

    def __init__(self):
        pass

    @staticmethod
    def get_details_for(a_return):
        """
        Return data presented in table format with column headers.
        :return: formatted data.
        """
        if a_return.has_sheet:
            sheet = ReturnSheet(a_return)
            return sheet.table

        if a_return.has_data:
            data = ReturnData(a_return)
            return data.table

        if a_return.has_question:
            question = ReturnQuestion(a_return)
            return question.table

        return []

    @staticmethod
    def store_request_details_for(a_return, request):
        """
        Return data presented in table format with column headers.
        :return: formatted data.
        """
        if a_return.has_sheet:
            sheet = ReturnSheet(a_return)
            sheet.store(request)

        if a_return.has_data:
            data = ReturnData(a_return)
            data.store(request)

        if a_return.has_question:
            question = ReturnQuestion(a_return)
            question.store(request)

        return []

    @staticmethod
    def get_sheet_activity_list_for(a_return):

        if a_return.has_sheet:
            sheet = ReturnSheet(a_return)
            return sheet.activity_list

        return None

    @staticmethod
    def get_sheet_species_list_for(a_return):

        if a_return.has_sheet:
            sheet = ReturnSheet(a_return)
            return sheet.species_list

        return None

    @staticmethod
    def get_sheet_species_for(a_return):

        if a_return.has_sheet:
            sheet = ReturnSheet(a_return)
            return sheet.species

        return None

    @staticmethod
    def set_sheet_species_for(a_return, species_id):

        if a_return.has_sheet:
            sheet = ReturnSheet(a_return)
            sheet.set_species(species_id)

        return None


class ReturnData(object):
    """
    Informational data of requirements supporting licence condition.
    """
    def __init__(self, a_return):
        self._return = a_return

    @property
    def table(self):
        """
        Table of return information presented in Grid format.
        :return: Grid formatted data.
        """
        tables = []
        for resource in self._return.return_type.resources:
            resource_name = resource.get('name')
            schema = Schema(resource.get('schema'))
            headers = []
            for f in schema.fields:
                header = {
                    "label": f.data['label'],
                    "name": f.data['name'],
                    "required": f.required,
                    "type": f.type.name,
                    "readonly": False,
                }
                if f.is_species:
                    header["species"] = f.species_type
                headers.append(header)
            table = {
                'name': resource_name,
                'label': resource.get('title', resource.get('name')),
                'type': 'grid',
                'headers': headers,
                'data': None
            }
            try:
                return_table = self._return.returntable_set.get(
                    name=resource_name)
                all_return_rows = return_table.returnrow_set.all()
                rows = [
                    return_row.data for return_row in all_return_rows]
                validated_rows = schema.rows_validator(rows)
                table['data'] = validated_rows
            except ReturnTable.DoesNotExist:
                result = {}
                results = []
                for field_name in schema.fields:
                    result[field_name.name] = {
                            'value': None
                    }
                results.append(result)
                table['data'] = results
            tables.append(table)

        return tables

    def store(self, request):
        """
        Save the current state of this Return Data.
        :param request:
        :return:
        """
        for key in request.data.keys():
            if key == "nilYes":
                self._return.nil_return = True
                self._return.comments = request.data.get('nilReason')
                self._return.save()
            if key == "nilNo":
                returns_tables = request.data.get('table_name')
                if self._is_post_data_valid(
                        returns_tables.encode('utf-8'), request.data):
                    table_info = returns_tables.encode('utf-8')
                    table_rows = self._get_table_rows(
                        table_info, request.data)
                    if table_rows:
                        self._return.save_return_table(
                            table_info, table_rows, request)
                else:
                    raise FieldError('Enter data in correct format.')

    def build_table(self, rows):
        """
        Method to create and validate rows of data to the table schema without
        persisting. Used for Loading data from spreadsheets.
        :param rows: data to be formatted.
        :return: Array of tables.
        """
        tables = []
        for resource in self._return.return_type.resources:
            resource_name = resource.get('name')
            schema = Schema(resource.get('schema'))
            table = {
                'name': resource_name,
                'label': resource.get('title', resource.get('name')),
                'type': None,
                'headers': None,
                'data': None
            }
            try:
                validated_rows = schema.rows_validator(rows)
                table['data'] = validated_rows
            except AttributeError:
                result = {}
                results = []
                for field_name in schema.fields:
                    result[field_name.name] = {
                            'value': None
                    }
                results.append(result)
                table['data'] = results
            tables.append(table)

        return tables

    def _is_post_data_valid(self, tables_info, post_data):
        """
        Validates table data against the Schema for correct entry of data
        types.
        :param tables_info:
        :param post_data:
        :return:
        """
        table_rows = self._get_table_rows(tables_info, post_data)
        if len(table_rows) == 0:
            return False
        schema = Schema(
            self._return.return_type.get_schema_by_name(tables_info))
        if not schema.is_all_valid(table_rows):
            return False
        return True

    def _get_table_rows(self, table_name, post_data):
        """
        Builds a row of data taken from a table into a standard that can be
        consumed by the Schema.
        :param table_name:
        :param post_data:
        :return:
        """
        table_namespace = table_name + '::'
        # exclude fields defaulted from renderer. ie comment-field,
        # deficiency-field (Application specific)
        excluded_field = ('-field')
        by_column = dict([(key.replace(table_namespace, ''), post_data.getlist(
            key)) for key in post_data.keys() if key.startswith(
                table_namespace) and not key.endswith(excluded_field)])
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

    def __str__(self):
        return self._return.lodgement_number


class ReturnActivity(object):
    """
    An Activity relating to the Transfer of Stock.
    """

    _TRANSFER_STATUS_NONE = ''
    _TRANSFER_STATUS_NOTIFY = 'Notified'
    _TRANSFER_STATUS_ACCEPT = 'Accepted'
    _TRANSFER_STATUS_DECLINE = 'Declined'

    # Activity properties.
    _ACTIVITY_DATE = 'date'
    _COMMENT = 'comment'
    _TRANSFER = 'transfer'
    _QUANTITY = 'qty'
    _LICENCE = 'licence'
    _ACTIVITY = 'activity'
    _TOTAL = 'total'
    _ROWID = 'rowId'

    def __init__(self, transfer):
        self.date = transfer[self._ACTIVITY_DATE]
        self.comment = transfer[self._COMMENT]
        self.transfer = transfer[self._TRANSFER]
        self.qty = transfer[self._QUANTITY]
        self.licence = transfer[self._LICENCE]
        self.total = ''
        self.rowId = '0'
        self.activity = transfer[self._ACTIVITY]

    def get_licence_return(self):
        """
        Method to retrieve Return with Running Sheet from a Licence No.
        :return: a Return object.
        """
        try:
            return Return.objects.filter(
                licence__licence_number=self.licence,
                return_type__data_format=ReturnType.FORMAT_SHEET
                ).first()

        except Return.DoesNotExist:
            raise ValidationError({'error': 'Error exception.'})

    @staticmethod
    def factory(transfer):
        NOTIFY = ReturnActivity._TRANSFER_STATUS_NOTIFY
        ACCEPT = ReturnActivity._TRANSFER_STATUS_ACCEPT
        DECLINE = ReturnActivity._TRANSFER_STATUS_DECLINE

        if transfer[ReturnActivity._TRANSFER] == NOTIFY:
            return NotifyTransfer(transfer)
        if transfer[ReturnActivity._TRANSFER] == ACCEPT:
            return AcceptTransfer(transfer)
        if transfer[ReturnActivity._TRANSFER] == DECLINE:
            return DeclineTransfer(transfer)

        return None


class NotifyTransfer(ReturnActivity):
    """
    Notification of a Transfer Activity.
    """

    def __init__(self, transfer):
        super(NotifyTransfer, self).__init__(transfer)
        self.activity = ReturnSheet._ACTIVITY_TYPES[
            transfer[self._ACTIVITY]]['outward']

    @transaction.atomic
    def store_transfer_activity(self, species, request, from_return):
        """
        Saves the Transfer Activity under the Receiving Licence return for
        species.
        :return: _new_transfer boolean.
        """
        to_return = self.get_licence_return()
        self.licence = from_return.licence.licence_number

        try:
            # get the Return Table record and save immediately to check if it
            # has been concurrently modified.
            return_table, created = ReturnTable.objects.get_or_create(
                name=species, ret=to_return)
            return_table.save()
            rows = ReturnRow.objects.filter(return_table=return_table)
            table_rows = []
            row_exists = False
            total = 0
            row_cnt = 0
            self.rowId = str(row_cnt)
            for row in rows:
                if row.data[self._ACTIVITY_DATE] == self.date:  # update record
                    row_exists = True
                    row.data[self._QUANTITY] = self.qty
                    row.data[self._COMMENT] = self.comment
                    row.data[self._TRANSFER] = self.transfer
                total = row.data[self._TOTAL]
                table_rows.append(row.data)
                row_cnt = row_cnt + 1
                self.rowId = str(row_cnt)
            if not row_exists:
                self.total = total
                table_rows.append(self.__dict__)
            # delete any existing rows as they will all be recreated
            return_table.returnrow_set.all().delete()
            return_rows = [
                ReturnRow(
                    return_table=return_table,
                    data=row) for row in table_rows]
            ReturnRow.objects.bulk_create(return_rows)
            # log transaction
            from_return.log_user_action(
                ReturnUserAction.ACTION_SUBMIT_TRANSFER.format(
                    from_return), request)

            if not row_exists:
                send_sheet_transfer_email_notification(
                    request, to_return, from_return)

            return row_exists
        except RecordModifiedError:
            raise IntegrityError(
                'A concurrent save occurred please refresh page details.')
        except BaseException:
            raise


class AcceptTransfer(ReturnActivity):
    """
    A ReturnActivity that is an Accepted Transfer.
    """

    def __init__(self, transfer):
        super(AcceptTransfer, self).__init__(transfer)

    @transaction.atomic
    def store_transfer_activity(self, species, request, from_return):
        """
        Saves the Transfer Activity under the Receiving Licence return for
        species.
        :return: _new_transfer boolean.
        """
        to_return = self.get_licence_return()

        try:
            # get the Return Table record and save immediately to check if
            # it has been concurrently modified.
            return_table = ReturnTable.objects.get(name=species, ret=to_return)
            return_table.save()
            rows = ReturnRow.objects.filter(return_table=return_table)
            table_rows = []
            row_exists = False
            for row in rows:  # update total and status for accepted activity.
                if row.data[self._ACTIVITY_DATE] == self.date:
                    row_exists = True
                    row.data[self._TRANSFER] = \
                        ReturnActivity._TRANSFER_STATUS_ACCEPT
                    row.data[
                        self._TOTAL] = int(row.data[
                            self._TOTAL]) - int(self.qty)
                    break
            for row in rows:  # update totals for subsequent activities.
                if row_exists and int(row.data[
                        self._ACTIVITY_DATE]) > int(self.date):
                    row.data[self._TOTAL] = int(row.data[
                        self._TOTAL]) - int(self.qty)
                table_rows.append(row.data)
            # delete any existing rows as they will all be recreated
            return_table.returnrow_set.all().delete()
            return_rows = [
                ReturnRow(
                    return_table=return_table,
                    data=row) for row in table_rows]
            ReturnRow.objects.bulk_create(return_rows)
            # log transaction
            from_return.log_user_action(
                ReturnUserAction.ACTION_ACCEPT_TRANSFER.format(
                    from_return), request)

            return row_exists
        except RecordModifiedError:
            raise IntegrityError(
                'A concurrent save occurred please refresh page details.')
        except BaseException:
            raise


class DeclineTransfer(ReturnActivity):
    """
    A ReturnActivity that is an Declined Transfer.
    """

    def __init__(self, transfer):
        super(DeclineTransfer, self).__init__(transfer)

    @transaction.atomic
    def store_transfer_activity(self, species, request, from_return):
        """
        Saves the Transfer Activity under the Receiving Licence return for
        species.
        :return: _new_transfer boolean.
        """
        to_return = self.get_licence_return()

        try:
            # get the Return Table record and save immediately to check if it
            # has been concurrently modified.
            return_table = ReturnTable.objects.get(name=species, ret=to_return)
            return_table.save()
            rows = ReturnRow.objects.filter(return_table=return_table)
            table_rows = []
            row_exists = False
            for row in rows:  # update status for selected activity.
                if row.data[self._ACTIVITY_DATE] == self.date:
                    row_exists = True
                    row.data[self._TRANSFER] = \
                        ReturnActivity._TRANSFER_STATUS_DECLINE
                table_rows.append(row.data)

            # delete any existing rows as they will all be recreated
            return_table.returnrow_set.all().delete()
            return_rows = [
                ReturnRow(
                    return_table=return_table,
                    data=row) for row in table_rows]
            ReturnRow.objects.bulk_create(return_rows)
            # log transaction
            from_return.log_user_action(
                ReturnUserAction.ACTION_DECLINE_TRANSFER.format(
                    from_return), request)

            return row_exists
        except RecordModifiedError:
            raise IntegrityError(
                'A concurrent save occurred please refresh page details.')
        except BaseException:
            raise


class ReturnQuestion(object):
    """
    Informational question of requirements supporting licence condition.
    """
    def __init__(self, a_return):
        self._return = a_return

    @property
    def table(self):
        """
        Table of return questions.
        :return: formatted data.
        """
        tables = []
        for resource in self._return.return_type.resources:
            resource_name = ReturnType.FORMAT_QUESTION
            schema = Schema(resource.get('schema'))
            headers = []
            for f in schema.fields:
                header = {
                    "label": f.data['label'],
                    "name": f.data['name'],
                    "required": f.required,
                    "type": f.type.name,
                    "readonly": False,
                }
                if f.is_species:
                    header["species"] = f.species_type
                headers.append(header)
            table = {
                'name': resource_name,
                'title': resource.get('title', resource.get('name')),
                'headers': headers,
                'data': None
            }
            try:
                r_table = self._return.returntable_set.get(
                    name=resource_name)
                rows = [
                    r_row.data for r_row in r_table.returnrow_set.all()]
                table['data'] = rows
            except ReturnTable.DoesNotExist:
                result = {}
                results = []
                for field_name in schema.fields:
                    result[field_name.name] = {
                        'value': None
                    }
                results.append(result)
                table['data'] = results
            tables.append(table)
        return tables

    def store(self, request):
        """
        Save the current state of the Return.
        :param request:
        :return:
        """
        # Nb: There is only ONE row where each Question is a header.
        table_rows = self._get_table_rows(request.data)
        self._return.save_return_table(
            ReturnType.FORMAT_QUESTION, table_rows, request)

    def _get_table_rows(self, _data):
        """
        Builds a row of data taken from the Request into a standard that can
        be saved.
        :param _data:
        :return:
        """
        # by_column is of format {'col_header':[row1_val, row2_val,...],...}
        by_column = dict([])
        rows = []
        for key in _data.keys():
            by_column[key] = _data[key]
        rows.append(by_column)

        return rows

    def __str__(self):
        return self._return.lodgement_number


class ReturnSheet(object):
    """
    Informational Running Sheet of Species requirements supporting licence
    condition.
    """
    _DEFAULT_SPECIES = '0000000'

    _SHEET_SCHEMA = {
        "name": "sheet",
        "title": "Running Sheet of Return Data",
        "resources": [{
            "name": "species_id",
            "path": "",
            "title": "Return Data for Specie",
            "schema": {
                "fields": [{
                    "name": "date",
                    "type": "date",
                    "format": "fmt:%d/%m/%Y",
                    "constraints": {
                        "required": True}}, {
                    "name": "activity",
                    "type": "string",
                    "constraints": {
                        "required": True}}, {
                    "name": "qty",
                    "type": "number",
                    "constraints": {
                        "required": True}}, {
                    "name": "total",
                    "type": "number",
                    "constraints": {
                        "required": True}}, {
                    "name": "licence",
                    "type": "string"}, {
                    "name": "comment",
                    "type": "string"}, {
                    "name": "transfer",
                    "type": "string"}]}}]}

    _NO_ACTIVITY = {
        "echo": 1,
        "totalRecords": "0",
        "totalDisplayRecords": "0",
        "data": []}

    # todo: change activity id to a meaningful name
    _ACTIVITY_TYPES = {
        "SA01": {"label": "Stock", "auto": "false", "licence": "false",
                 "pay": "false", "initial": ""},
        "SA02": {"label": "In through import", "auto": "false",
                 "licence": "false", "pay": "false", "inward": ""},
        "SA03": {"label": "In through birth", "auto": "false",
                 "licence": "false", "pay": "false", "inward": ""},
        "SA04": {"label": "In through transfer", "auto": "true",
                 "licence": "false", "pay": "false", "inward": ""},
        "SA05": {"label": "Out through export", "auto": "false",
                 "licence": "false", "pay": "false", "outward": ""},
        "SA06": {"label": "Out through death", "auto": "false",
                 "licence": "false", "pay": "false", "outward": ""},
        "SA07": {"label": "Out through transfer other", "auto": "false",
                 "licence": "true", "pay": "true", "outward": "SA04"},
        "SA08": {"label": "Out through transfer dealer", "auto": "false",
                 "licence": "true", "pay": "false", "outward": "SA04"},
        "0": {"label": "", "auto": "false", "licence": "false",
              "pay": "false", "initial": ""}}

    def __init__(self, a_return):
        self._return = a_return
        self._return.return_type.data_descriptor = self._SHEET_SCHEMA
        self._species_list = []
        self._table = {'data': None}
        # build list of currently added Species.
        self._species = self._DEFAULT_SPECIES
        for _species in ReturnTable.objects.filter(ret=a_return):
            self._species_list.append(_species.name)
            self._species = _species.name

    @staticmethod
    def set_licence_species(the_return):
        """
        Sets the species from the licence for the current Running Sheet.
        :return:
        """
        # TODO: create default entries for each species on the licence.
        # TODO: Each species has a defaulted Stock Activity (0 Totals).
        # TODO: Call _set_activity_from_previous to carry over Stock totals
        # for Licence reissues.
        '''
        _data = []
        new_sheet = the_return.sheet
        for species in the_return.licence.species_list:
            try:
                _data = {''}
                table_rows = new_sheet._get_table_rows(_data)
                self._return.save_return_table(species, table_rows, request)
            except AttributeError:
                continue
        '''
        pass

    @property
    def table(self):
        """
        Running Sheet Table of data for Species. Defaults to a Species on the
        Return if exists.
        :return: formatted data.
        """
        return self._get_activity(self._species)['data']

    @property
    def species(self):
        """
        Species type associated with this Running Sheet of Activities.
        :return:
        """
        return self._species

    @property
    def species_list(self):
        """
        List of Species available with Running Sheet of Activities.
        :return: List of Species.
        """
        return self._species_list

    @property
    def activity_list(self):
        """
        List of stock movement activities applicable for Running Sheet.
        Format: "SA01": {
            "label": "Stock",
            "auto": "false",
            "licence": "false",
            "pay": "false",
            "outward": "SA04"}
        Label: Activity Description.
        Auto: Flag indicating automated activity.
        Licence: Flag indicating licence required for activity.
        Pay: Flag indicating payment required for activity.
        Inward/Outward: Transfer type with Activity Type for outward transfer.
        :return: List of Activities applicable for Running Sheet.
        """
        return self._ACTIVITY_TYPES

    # todo: more generic method name for payment transfer
    @property
    def process_transfer_fee_payment(self, request):
        from ledger.payments.models import BpointToken
        # if self.return_ee_paid:
        #    return True

        application = self.application
        applicant = application.proxy_applicant \
            if application.proxy_applicant else application.submitter
        card_owner_id = applicant.id
        card_token = BpointToken.objects.filter(
            user_id=card_owner_id).order_by('-id').first()
        if not card_token:
            logger.error("No card token found for user: %s" % card_owner_id)
            return False

        product_lines = []
        return_submission = u'Transfer of stock for {} Return {}'.format(
            u'{} {}'.format(applicant.first_name, applicant.last_name),
            application.lodgement_number)
        product_lines.append({
            'ledger_description': '{}'.format(self._return.id),
            'quantity': 1,
            'price_incl_tax': str(self._return.return_fee),
            'price_excl_tax': str(calculate_excl_gst(self.licence_fee)),
            'oracle_code': ''
        })
        checkout(
            request, application, lines=product_lines,
            invoice_text=return_submission,
            internal=True,
            add_checkout_params={
                'basket_owner': request.user.id,
                'payment_method': 'card',
                'checkout_token': card_token.id,
            }
        )
        try:
            invoice_ref = request.session['checkout_invoice']
        except KeyError:
            ID = self.licence_activity_id
            logger.error(
                "No invoice reference generated for Activity ID: %s" % ID)
            return False
        ReturnInvoice.objects.get_or_create(
            invoice_return=self,
            invoice_reference=invoice_ref
        )
        flush_checkout_session(request.session)
        # return self.licence_fee_paid and
        # send_activity_invoice_email_notification(
        # application, self, invoice_ref, request)
        return self.licence_fee_paid

    def store(self, request):
        """
        Save the current state of this Return Sheet.
        :param request:
        :return:
        """
        for species in self.species_list:
            try:
                _data = request.data.get(species).encode('utf-8')
                _data = ast.literal_eval(_data)  # ast should convert to tuple.
                table_rows = self._get_table_rows(_data)
                self._return.save_return_table(species, table_rows, request)
            except AttributeError:
                continue
        self._add_transfer_activity(request)

    def set_species(self, _species):
        """
        Sets the species for the current Running Sheet.
        :param _species:
        :return:
        """
        self._species = _species
        # self._species_list.add(_species)

    def get_species(self):
        """
        Gets the species for the current Running Sheet.
        :return:
        """
        return self._species

    def is_valid_transfer(self, req):
        """
        Validate transfer request details.
        :param request:
        :return:
        """
        is_valid = True
        if not req.data.get('transfer'):
            return False
        _data = req.data.get('transfer').encode('utf-8')
        _transfers = ast.literal_eval(_data)
        _lic = _transfers['licence']
        is_valid = \
            False if not is_valid else self._is_valid_transfer_licence(_lic)
        is_valid = \
            False if not is_valid else self._is_valid_transfer_quantity(req)

        return is_valid

    def _get_activity(self, _species_id):
        """
        Get Running Sheet activity for the movement of Species stock.
        :return:
        formatted data {
            'name': 'speciesId',
            'data': [{'date': '2019/01/23', 'activity': 'SA01', ..., }]}
        """
        self._species = _species_id
        for resource in self._return.return_type.resources:
            _resource_name = _species_id
            _schema = Schema(resource.get('schema'))
            try:
                _r_table = self._return.returntable_set.get(
                    name=_resource_name)
                rows = [
                    _r_row.data for _r_row in _r_table.returnrow_set.all()]
                _schema.rows_validator(rows)
                self._table['data'] = rows
                self._table['echo'] = 1
                self._table['totalRecords'] = str(rows.__len__())
                self._table['totalDisplayRecords'] = str(rows.__len__())
            except ReturnTable.DoesNotExist:
                self._table = self._NO_ACTIVITY

        return self._table

    def _get_table_rows(self, _data):
        """
        Gets the formatted row of data from Species data.
        :param _data:
        :return:
        """
        by_column = dict([])
        # by_column is of format {'col_header':[row1_val, row2_val,...],...}
        key_values = []
        num_rows = 0
        if isinstance(_data, tuple):
            for key in _data[0].keys():
                for cnt in range(_data.__len__()):
                    key_values.append(_data[cnt][key])
                by_column[key] = key_values
                key_values = []
            num_rows = len(list(by_column.values())[0])\
                if len(by_column.values()) > 0 else 0
        else:
            for key in _data.keys():
                by_column[key] = _data[key]
            num_rows = num_rows + 1

        rows = []
        for row_num in range(num_rows):
            row_data = {}
            if num_rows > 1:
                for key, value in by_column.items():
                    row_data[key] = value[row_num]
            else:
                row_data = by_column
            # filter empty rows.
            is_empty = True
            for value in row_data.values():
                if value and len(value.strip()) > 0:
                    is_empty = False
                    break
            if not is_empty:
                row_data['rowId'] = str(row_num)
                rows.append(row_data)

        return rows

    def _set_activity_from_previous(self):
        """
        Sets Running Sheet Species stock total from previous Licence Running
        Sheet.
        :return: tuple of species and total.
        """
        previous_licence = \
            self._return.application.previous_application.licence
        previous_return = self._get_licence_return(previous_licence)
        previous_stock = {}  # {species_id: amount}
        if previous_return:
            species_tables = ReturnTable.objects.filter(ret=previous_return)
            for table in species_tables:
                rows = ReturnRow.objects.filter(return_table=table)
                stock_total = 0
                for row in rows:
                    stock_total = row.data['total']
                previous_stock[table.name] = stock_total
        return previous_stock

    def _get_licence_return(self, licence_no):
        """
        Method to retrieve Return with Running Sheet from a Licence No.
        :param licence_no:
        :return: a Return object.
        """
        TYPE = ReturnType.FORMAT_SHEET
        try:
            return Return.objects.filter(licence__licence_number=licence_no,
                                         return_type__data_format=TYPE
                                         ).first()
        except Return.DoesNotExist:
            raise ValidationError({'error': 'Error exception.'})

    def _add_transfer_activity(self, request):
        """
        Add transfer activity to a validated receiving licence return.
        :param request:
        :return:
        """
        if not request.data.get('transfer'):
            return False
        _data = request.data.get('transfer').encode('utf-8')
        _transfers = ast.literal_eval(_data)
        if isinstance(_transfers, tuple):
            for transfer in _transfers:
                a_transfer = ReturnActivity.factory(transfer)
                a_transfer.store_transfer_activity(
                    transfer['species_id'], request, self._return)
        else:
            a_transfer = ReturnActivity.factory(_transfers)
            a_transfer.store_transfer_activity(
                _transfers['species_id'], request, self._return)

    def _is_valid_transfer_licence(self, _licence):
        """
        Method to check if licence is current.
        :return: boolean
        """
        return True if self._get_licence_return(_licence) else False

    def _is_valid_transfer_quantity(self, request):
        """
        Method to check transfer transfer quantity does not exceed total.
        :param request:
        :return: boolean
        """
        # TODO: This validation is not completed.
        if not request.data.get('transfer'):
            return False
        data = request.data.get('transfer').encode('utf-8')
        ast.literal_eval(data)
        # quantity = transfers['qty']
        # species_id = transfers['transfer']
        '''
        return_table = ReturnTable.objects.get(
            name=species, ret=to_return)[0]
        rows = ReturnRow.objects.filter(return_table=return_table)
            # optimistic load of rows.
        table_rows = []
        r_exists = False
        total = 0
        for r in rows:  # update total and status for accepted activity.
            if r.data[self._ACTIVITY_DATE] == self.date:
                r_exists = True
                r.data[self._TRANSFER] = ReturnActivity._TRANSFER_STATUS_ACCEPT
                r.data[self._TOTAL] = int(r.data[self._TOTAL]) - int(self.qty)
                table_rows.append(r.data)
                break
        for r in rows:  # update totals for subsequent activities.
            if r_exists and int(r.data[self._ACTIVITY_DATE]) > int(self.date):
                r.data[self._TOTAL] = int(r.data[self._TOTAL]) - int(self.qty)
            table_rows.append(r.data)
        '''
        return True

    def __str__(self):
        return self._return.lodgement_number
