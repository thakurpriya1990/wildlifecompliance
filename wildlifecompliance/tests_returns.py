from django.test import TestCase, RequestFactory, tag, Client
from django.utils import timezone
from concurrency.exceptions import RecordModifiedError
from django.db.utils import IntegrityError
import logging
import os
import re

from django.core import mail
from django.core.urlresolvers import reverse

from wildlifecompliance.components.returns.models import Return, ReturnType, ReturnTable, ReturnRow
from wildlifecompliance.components.applications.models import Application, ApplicationSelectedActivity, ApplicationStandardCondition, ApplicationCondition
from wildlifecompliance.components.licences.models import LicenceActivity, WildlifeLicence, \
    LicenceCategory, LicencePurpose
from wildlifecompliance.components.main.utils import checkout, flush_checkout_session

from ledger.accounts.models import EmailUser, Organisation, OrganisationAddress
from .tests_helpers import get_or_create_default_customer, \
                           TEST_SCHEMA_DATA, TEST_DATA, \
                           TEST_LICENCE_TYPE_DATA, \
                           get_or_create_default_officer, \
                           SocialClient, \
                           create_return, TEST_RETURN_SHEET_SCHEMA, TEST_LICENCE_PURPOSE_SCHEMA

from ledger.payments.models import BpointToken
from ledger.payments.invoice.models import Invoice
from ledger.checkout.utils import calculate_excl_gst


logger = logging.getLogger(__name__)
logging.disable(logging.NOTSET)
logger.setLevel(logging.DEBUG)

TEST_SPREADSHEET_PATH = os.path.join('wildlifecompliance', 'regulation15.xlsx')

TEST_VALUES = {
    'LOCATION': 'Test Location',
    'SITE': 'Test Site',
    'DATUM': 'WSG84',
    'LATITUDE': 35,
    'LONGITUDE': -45,
    'ZONE': 'Danger',
    'EASTING': 2,
    'NORTHING': 3,
    'ACCURACY': 'Very',
    'DATE': 'Today',
    'NAME_ID': 'Bird',
    'SPECIES_NAME': 'Biggus bird',
    'COMMON_NAME': 'Big Bird',
    'SPECIES_GROUP': 'Birds',
    'COUNT': 1,
    'IDENTIFIER': 'Colour',
    'CERTAINTY': 'Very',
    'METHOD': 'Trap',
    'FATE': 'School',
    'SAMPLES': 'None',
    'MARKING': 'None',
    'TRANSMITTER': 'Radio',
    'VOUCHER_REF': 'Free Whopper'
}

# usage : python2 manage_wc.py test  --tag='return' --keepdb

class SocialClient(Client):
    """
    A django Client for authenticating with the social auth password-less framework.
    """

    def login(self, email):
        # important clear the mail box before
        self.clear_mailbox()
        self.post(reverse('social:complete', kwargs={'backend': "email"}), {'email': email})
        if len(mail.outbox) == 0:
            raise Exception("Email not received")
        else:
            login_url = re.search('(?P<url>https?://[^\s]+)', mail.outbox[0].body).group('url')
            response = self.get(login_url, follow=True)
            self.clear_mailbox()
        return response

    def logout(self):
        self.get(reverse('accounts:logout'))

    def clear_mailbox(self):
        mail.outbox = []


class ReturnsTest(TestCase):

    def setUp(self):

        test_user = EmailUser(email='unit.test@someorg.com',
                              first_name='unit',
                              last_name='test',
                              is_staff=True,
                              title='Mr',
                              dob='2019-12-10',
                              phone_number='92644545',
                              extra_data='').save()

        self.user = test_user

        an_app = Application(application_type='new_licence',
                             comment_data='',
                             customer_status='under_review',
                             lodgement_number='A000100',
                             lodgement_date=timezone.now(),
                             id_check_status='not_checked',
                             return_check_status='not_checked',
                             character_check_status='not_checked',
                             review_status='not_reviewed',
                             application_fee=0
                             )

        #an_app.schema = TEST_SCHEMA_DATA
        #an_app.data = TEST_DATA
        an_app.submitter = test_user
        an_app.save()

        another_app = Application(application_type='new_licence',
                                  comment_data='',
                                  customer_status='under_review',
                                  lodgement_number='A000200',
                                  lodgement_date=timezone.now(),
                                  id_check_status='not_checked',
                                  return_check_status='not_checked',
                                  character_check_status='not_checked',
                                  review_status='not_reviewed',
                                  application_fee=0)

        another_app.submitter = test_user
        another_app.save()

        BpointToken(DVToken=5999993673975627,
                    masked_card='XXXX-XXXX-XXXX-4122',
                    expiry_date='2029-03-10',
                    user_id=EmailUser.objects.first().id,
                    card_type='VC').save()

        activities = ApplicationSelectedActivity(
                            application=an_app,
                            reason=''
                            ).save()

        return_sheet_type = ReturnType(name='sheet')
        return_sheet_type.data_descriptor = '{}'
        return_sheet_type.data_format = 'sheet'
        return_sheet_type.save()

        return_question_type = ReturnType(name='question')
        return_question_type.data_descriptor = '{}'
        return_sheet_type.data_format = 'question'
        return_question_type.save()

        return_data_type = ReturnType(name='data')
        return_data_type.data_descriptor = '{}'
        return_data_type.save()

        address = OrganisationAddress(line1='21 Dick Perry Ave', locality='Kensington', postcode='6052').save()
        org = Organisation(name='Test Organisation', abn='1')
        org.postal_address = address
        org.save()


        standard_condition_NONE = ApplicationStandardCondition(text='A standard Condition',
                                                               code='SC010',
                                                               obsolete=False).save()

        standard_condition_SHEET= ApplicationStandardCondition(text='A standard Shaeet Condition',
                                                               code='SC020',
                                                               obsolete=False,
                                                               return_type_id=return_sheet_type.id).save()                                                              

        app_condition_1 = ApplicationCondition(standard=True,
                                               recurrence=False,
                                               recurrence_pattern='weekly',
                                               application_id=an_app.id,
                                               due_date='2029-02-01',
                                               standard_condition=standard_condition_SHEET,
                                               return_type=ReturnType.objects.get(id=return_sheet_type.id))
        app_condition_1.save()

        app_condition_2 = ApplicationCondition(standard=True,
                                               recurrence=False,
                                               recurrence_pattern='weekly',
                                               application_id=an_app.id,
                                               due_date='2029-01-01')
        app_condition_2.standard_condition=standard_condition_NONE
        app_condition_2.save()

        licence_activity = LicenceActivity(name='Dealing').save()

        licence_category = LicenceCategory()
        licence_category.save()

        licence_purpose = LicencePurpose(name='Taking Live Fauna for Commercial Purposes',
                                         base_application_fee='0.00',
                                         base_licence_fee='0.00')
        licence_purpose.licence_activity = licence_activity
        licence_purpose.schema = TEST_LICENCE_PURPOSE_SCHEMA
        licence_purpose.save()

        a_licence = WildlifeLicence(licence_number='L0000001',
                                    licence_category=licence_category,
                                    licence_sequence=1)

        a_licence.submitter = test_user
        a_licence.applicant = org
        a_licence.current_application = an_app
        a_licence.licence_type = licence_purpose
        a_licence.save()

        another_licence = WildlifeLicence(licence_number='L0000002',
                                          licence_category=licence_category,
                                          licence_sequence=1)

        another_licence.submitter = test_user
        another_licence.applicant = org
        another_licence.current_application = another_app
        another_licence.licence_type = licence_purpose
        another_licence.save()

        user = EmailUser.objects.first()

        a_sheet = Return(application_id=an_app.id,
                         assigned_to_id=None,
                         comments=None,
                         condition_id=None,
                         due_date='2029-06-01',
                         licence_id=a_licence.id,
                         nil_return=False,
                         post_reminder_sent=False,
                         processing_status='future',
                         reminder_sent=False,
                         return_type_id=return_sheet_type.id,
                         submitter_id=user.id
                         )
        a_sheet.save()

        a_question = Return(application_id=an_app.id,
                            assigned_to_id=None,
                            comments=None,
                            condition_id=None,
                            due_date='2019-06-01',
                            licence_id=a_licence.id,
                            nil_return=False,
                            post_reminder_sent=False,
                            processing_status='future',
                            reminder_sent=False,
                            return_type_id=return_question_type.id,
                            submitter_id=user.id
                            )
        a_question.save()

        a_data = Return(application_id=an_app.id,
                        assigned_to_id=None,
                        comments=None,
                        condition_id=None,
                        due_date='2019-06-01',
                        licence_id=a_licence.id,
                        nil_return=False,
                        post_reminder_sent=False,
                        processing_status='future',
                        reminder_sent=False,
                        return_type_id=return_data_type.id,
                        submitter_id=user.id
                        )
        a_data.save()

        another_sheet = Return(application_id=another_app.id,
                               assigned_to_id=None,
                               comments=None,
                               condition_id=None,
                               due_date='2029-06-05',
                               licence_id=another_licence.id,
                               nil_return=False,
                               post_reminder_sent=False,
                               processing_status='future',
                               reminder_sent=False,
                               return_type_id=return_sheet_type.id,
                               submitter_id=user.id
                              )
        another_sheet.save()

        table_rows = {"comment":"","rowId":"0","transfer":"","qty":"100","licence":"","activity":"SA01","date":1561341976000,"total":100}
        return_table = ReturnTable.objects.get_or_create(name='S000001', ret=a_sheet)[0]
        # delete any existing rows as they will all be recreated
        return_table.returnrow_set.all().delete()
        return_rows = [
            ReturnRow(
                return_table=return_table,
                data=row) for row in table_rows]
        ReturnRow.objects.bulk_create(return_rows)


    @tag('generate')
    def test_generate_returns(self):
        """
        The system must support a Running Sheet type of Return for the recording of Stock (Species) details.
        :return:
        """
        logger.info('SHEET: Asserted the generation of Running Sheets.')
        an_application = Application.objects.first()
        licence = WildlifeLicence.objects.first()
        start_date = '2019-03-01'
        expiry_date = '2020-03-01'
        selected_activity = an_application.activities.first()
        selected_activity.decision_action = ApplicationSelectedActivity.DECISION_ACTION_ISSUED
        selected_activity.processing_status = ApplicationSelectedActivity.PROCESSING_STATUS_ACCEPTED
        selected_activity.original_issue_date = start_date
        selected_activity.start_date = start_date
        selected_activity.expiry_date = expiry_date
        selected_activity.activity_status = ApplicationSelectedActivity.ACTIVITY_STATUS_CURRENT
        selected_activity.save()
        # an_application has two conditions: 1 RunningSheet 2 No Return Types
        an_application.generate_returns(licence, selected_activity, self)
        a_sheet_type = ReturnType.objects.filter(data_format='sheet').first()
        a_stock_sheet = Return.objects.filter(application_id=an_application.id, return_type=a_sheet_type).first()
        self.assertTrue(a_stock_sheet, 'Running Sheet is not retrieved')

    @tag('question')
    def test_add_question(self):
        """
        The system must support the ability to create Question based Returns.
        :return:
        """
        _DATA_0 = ({"comment": "", "licence": "", "qty": "0", "rowId": "0", "activity": "", "date": "100000000000", "total": ""})

        logger.info('SHEET: Assert the adding new Species with Running Sheet.')
        #an_application = Application.objects.first()
        #a_return = Return.objects.filter(application_id=an_application.id, return_type__name='question').first()

        #print(a_return)


    @tag('sheet')
    def test_add_sheet_species_1(self):
        """
        The system must support the ability to create a Running Sheet for different species available on licence.
        :return:
        """
        _DATA_0 = ({"comment": "", "licence": "", "qty": "0", "rowId": "0", "activity": "", "date": "100000000000", "total": ""})

        logger.info('SHEET: Assert the adding new Species with Running Sheet.')
        an_application = Application.objects.first()
        a_return = Return.objects.get(application_id=an_application.id)

        if a_return.has_sheet:
            a_return.sheet.set_activity('SPEC01', _DATA_0)  # Add new species with no activity

        self.assertEquals(a_return.sheet.get_activity('SPEC01')['totalRecords'], '0', 'Total Records incorrect')

    @tag('she')
    def test_add_sheet_species_2(self):
        """
        The system must support the ability to create a Running Sheet for different species available on licence.
        :return:
        """
        _DATA_1 = ({"comment": "Initial backup", "licence": "", "qty": "5", "rowId": "3", "activity": "SA01",
                   "date": "2019/01/23", "total": "5"})

        logger.info('SHEET: Assert the adding new Species with Running Sheet.')
        an_application = Application.objects.first()
        a_return = Return.objects.get(application_id=an_application.id)

        a_return.sheet.set_activity('SPEC01', _DATA_1)  # Add activity

        self.assertEquals(a_return.sheet.get_activity('SPEC01')['totalRecords'], '1', 'Total Records incorrect')
        self.assertEquals(a_return.sheet.get_activity('SPEC01')['data'][0]['rowId'], '0', 'RowID incorrect')


    @tag('she')
    def test_add_sheet_species_2(self):
        """
        The system must support the ability to create a Running Sheet for different species available on licence.
        :return:
        """

        _DATA_0 = ({"comment": "", "licence": "", "qty": "", "rowId": "", "activity": "", "date": "", "total": ""})

        _DATA_1 = ({"comment": "Initial backup", "licence": "", "qty": "5", "rowId": "3", "activity": "SA01",
                   "date": "2019/01/23", "total": "5"})

        _DATA_2 = ({"comment": "Initial", "licence": "", "qty": "5", "rowId": "", "activity": "SA01",
                    "date": "2019/01/23", "total": "5"}, {"comment": "Birth", "licence": "",
                    "qty": "3", "rowId": "", "activity": "SA03", "date": "2019/01/31","total": "8000"})

        _DATA_3 = ({"comment": "Initial backup", "licence": "", "qty": "5", "rowId": "", "activity": "SA01",
                    "date": "2019/01/23", "total": "5"}, {"comment": "Birth", "licence": "",
                    "qty": "3", "rowId": "1", "activity": "SA03", "date": "2019/01/31", "total": "8000"})

        logger.info('SHEET: Assert the adding new Species with Running Sheet.')

        an_application = Application.objects.first()
        a_return = Return.objects.filter(application_id=an_application.id).first()

        #a_return.sheet.set_activity('SPEC02', _DATA_2)  # Add new species with two activities

        #a_return = Return.objects.get(application_id=an_application.id)
        #a_return.sheet.set_activity('SPEC02', _DATA_2)  # Add new species with two activities

        #a_return = Return.objects.get(application_id=an_application.id)
        #print(a_return.sheet.get_activity('SPEC02'))

        #self.assertEquals(a_return.sheet.get_activity('SPEC02')['totalRecords'], '4', 'Total Records incorrect')
        #self.assertEquals(a_return.sheet.get_activity('SPEC02')['data'][1]['rowId'], '1', 'RowID incorrect')

        print (a_return.customer_status)

    @tag('shee')
    def test_update_sheet_for_species(self):
        """
        The system must support the ability to update a Running Sheet for different species available on the licence.
        :return:
        """

    @tag('shee')
    def test_get_specie_activity_types(self):
        """
        Expose a list of Specie Activity types that may be available for the stock Return data.
        :return:
        """
        an_application = Application.objects.first()
        stock_sheet = Return.objects.get(application_id=an_application.id).sheet

        self.assertTrue(stock_sheet)

    @tag('shee')
    def test_edit_row_for_activity(self):
        # The system must support the ability to record details on a Running Sheet for different species.
        logger.info('SHEET: Asserted the update of row details for activity.')
        an_application = Application.objects.first()
        a_stock_sheet = Return.objects.get(application_id=an_application.id)
        self.assertTrue(a_stock_sheet)

    @tag('shee')
    def test_add_row_for_activity(self):
        # The system must support the ability to record new activities on a Running Sheet for different species.
        logger.info('SHEET: Asserted the addition of new row of activity.')
        an_application = Application.objects.first()
        a_stock_sheet = Return.objects.get(application_id=an_application.id,)
        self.assertTrue(a_stock_sheet)

    @tag('shee')
    def test_auto_row_for_transfer_in(self):
        # The system must support the ability to automatically add a row when incoming transfer is accepted.
        logger.info('SHEET: Asserted the auto addition of row for Transfer-In.')
        an_application = Application.objects.first()
        a_stock_sheet = Return.objects.get(application_id=an_application.id)
        self.assertTrue(a_stock_sheet)

    @tag('shee')
    def test_auto_calculate_for_transfer_in(self):
        # The system must support the ability to automatically re-calculate totals when incoming transfer is accepted.
        logger.info('SHEET: Asserted the auto calculation of row details for Transfer-In.')
        an_application = Application.objects.first()
        a_stock_sheet = Return.objects.get(application_id=an_application.id)
        self.assertTrue(a_stock_sheet)

    @tag('shee')
    def test_email_notification_transfer_out(self):
        # The system must support the ability to send out email notification for acceptance or decline of transfer.
        logger.info('SHEET: Asserted the email of notification for Transfer-Out.')
        an_application = Application.objects.first()
        a_stock_sheet = Return.objects.filter(application_id=an_application.id).first()
        #request = RequestFactory()
        #request.user = EmailUser.objects.first()
        #print('running test')
        #a_stock_sheet.send_transfer_notification(request)
        self.assertTrue(a_stock_sheet)

    @tag('sheet')
    def test_accept_transfer_stock(self):
        # The system must support the ability to accept or decline a transfer.
        logger.info('SHEET: Asserted the acceptance of Transfers.')
        a_sheet_type = ReturnType.objects.filter(data_format='sheet').first()
        licence_return_1 = Return.objects.filter(licence__licence_number='L0000001').first()
        licence_return_2 = Return.objects.filter(licence__licence_number='L0000002').first()

        # table_rows = {"comment":"","rowId":"0","transfer":"","qty":"100","licence":"","activity":"SA01","date":1561341976000,"total":100}

        table_rows_1 = [
         {'comment': '', 'rowId': '0', 'transfer': '', 'qty': '100', 'licence': '', 'activity': 'SA01',
          'date': 1561343567000, 'total': 100},
         {'comment': '', 'rowId': '1', 'transfer': 'Accepted', 'qty': '10', 'licence': 'L4321344', 'activity': 'SA08',
          'date': 1561343598000, 'total': 90},
         {'comment': '', 'rowId': '2', 'transfer': 'Accepted', 'qty': '5', 'licence': 'L4321344', 'activity': 'SA08',
          'date': 1561344091000, 'total': 85},
         {'comment': '', 'rowId': '3', 'transfer': '', 'qty': '10', 'licence': '', 'activity': 'SA03',
          'date': 1561344101000, 'total': 95},
         {'comment': '', 'rowId': '4', 'transfer': '', 'qty': '5', 'licence': '', 'activity': 'SA06',
          'date': 1561344112000, 'total': 90},
         {'comment': '', 'rowId': '5', 'transfer': '', 'qty': '10', 'licence': '', 'activity': 'SA02',
          'date': 1561345818000, 'total': 100}
        ]

        table_rows_2 = [
            {'comment': '', 'rowId': '0', 'transfer': '', 'qty': '100', 'licence': '', 'activity': 'SA01',
             'date': 1561343567000, 'total': 100},
            {'comment': '', 'rowId': '1', 'transfer': 'Notify', 'qty': '15', 'licence': 'L4321344',
             'activity': 'SA08',
             'date': 1561343598000, 'total': 90},
            {'comment': '', 'rowId': '2', 'transfer': 'Notify', 'qty': '10', 'licence': 'L4321344', 'activity': 'SA08',
             'date': 1561344091000, 'total': 85},
            {'comment': '', 'rowId': '3', 'transfer': '', 'qty': '10', 'licence': '', 'activity': 'SA03',
             'date': 1561344101000, 'total': 95},
            {'comment': '', 'rowId': '4', 'transfer': '', 'qty': '5', 'licence': '', 'activity': 'SA06',
             'date': 1561344112000, 'total': 90},
            {'comment': '', 'rowId': '5', 'transfer': '', 'qty': '10', 'licence': '', 'activity': 'SA02',
             'date': 1561345818000, 'total': 100}
        ]

        return_table_1, created = ReturnTable.objects.get_or_create(name='S000001', ret=licence_return_1)
        # delete any existing rows as they will all be recreated
        return_rows_1 = [
            ReturnRow(
                return_table=return_table_1,
                data=row) for row in table_rows_1]

        return_table_2, created = ReturnTable.objects.get_or_create(name='S000001', ret=licence_return_1)
        # delete any existing rows as they will all be recreated
        return_rows_2 = [
            ReturnRow(
                return_table=return_table_2,
                data=row) for row in table_rows_2]

        return_table_1.returnrow_set.all().delete()
        return_table_1.save()
        ReturnRow.objects.bulk_create(return_rows_1)

        try :
            return_table_2.returnrow_set.all().delete()
            return_table_2.save()
            ReturnRow.objects.bulk_create(return_rows_2)
        except RecordModifiedError:
            raise IntegrityError("concurrent update")

        rows = ReturnRow.objects.filter()

        print(rows)

        self.assertTrue(licence_return_1)
        ##self.assertTrue(licence_return_2)

    def test_issue_licence(self):
        logger.info('issue_licence')

        app = Application.objects.first()
        request = RequestFactory()
        activity_type = []
        activity_type.append({'final_status': 'Issue', 'id': 4, 'name': 'Fauna Industry - Taking', 'start_date': '2020-02-01', 'end_date': '2019-02-01'})
        request.data = {'activity_type': activity_type}
        request.user = EmailUser.objects.first()
        #fails creating next_licence_number_id test db cannot generate
        #app.final_decision(request)

    def test_final_decision(self):
        logger.info('final_decision')
        request = RequestFactory()
        request.data = []

    def test_lodge_nil_return(self):
        """Testing that a user can log a nil return"""
        logger.info('lodge_nil_return')
        #self.client.login(self.customer.email)

        #post_params = {
        #    'nil': True,
        #    'comments': 'No survey taken'
        #}
        #response = self.client.post(reverse('wl_returns:enter_return', args=(self.ret.pk,)),
        #                            post_paramsi)

        #self.assertRedirects(response, reverse('home'),
        #                     status_code=302, target_status_code=200, fetch_redirect_response=False)

    def test_user_list(self):
        """Assert the generation of returns"""

        request = RequestFactory()
        request.user = EmailUser.objects.first()
        tc = SocialClient()

        return_id = 1
        #client = Client()
        #tc.login(request.user)
        # url = tc.post(reverse('returns:user_list', args=['return_id']))
        #response = client.get('/internal/returns/1')

        client = Client()
        response = client.get('http://127.0.0.1:8000/internal/returns/1')
        #response = client.get(reverse('internal'))

        logger.info(response.status_code)
        #logger.info('test user_list')

    def test_upload_return_spreadsheet(self):
        """Testing that a user can upload a return spreadsheet"""

        self.client.login(self.customer.email)

        with open(TEST_SPREADSHEET_PATH, 'rb') as fp:
             post_params = {
                 'upload': True,
                 'spreadsheet_file': fp
             }
             response = self.client.post(reverse('wl_returns:enter_return', args=(self.ret.pk,)),
                                            post_params)

        self.assertEqual(200, response.status_code)

        # assert values in the response context match those in the spreadsheet
        for key, value in response.context['tables'][0]['data'][0].items():
            self.assertEqual(value['value'], TEST_VALUES[key])

    @tag('pay')
    def test_checkout(self):

        request = RequestFactory()
        request.user = EmailUser.objects.first()
        client = Client(request)
        
        an_application = Application.objects.first()
        a_return = Return.objects.filter(application_id=an_application.id).first()

        application = an_application
        applicant = a_return.submitter
        card_owner_id = applicant.id
        card_token = BpointToken.objects.filter(user_id=card_owner_id).order_by('-id').first()

        if not card_token:
            logger.error("No card token found for user: %s" % card_owner_id)
            return False

        product_lines = []
        return_submission = u'Transfer of stock for {} Return {}'.format(
            u'{} {}'.format(applicant.first_name, applicant.last_name), a_return.lodgement_number)
        product_lines.append({
            'ledger_description': '{}'.format(a_return.id),
            'quantity': 1,
            'price_incl_tax': str(a_return.return_fee),
            'price_excl_tax': str(calculate_excl_gst(a_return.return_fee)),
            'oracle_code': ''
        })
        logger.info(return_submission)
        checkout(
            request, a_return, lines=product_lines,
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
            logger.error("No invoice reference generated for Activity ID: %s" )
            return False

        self.assertTrue(a_return)

    def test_submit_return(self):
        logger.info('submit_return')

    def test_amend_return(self):
        logger.info('amend_return')

    def test_accept_return(self):
        logger.info('accept_return')

    def tearDown(self):
        pass


#class ReturnsTestCase(TestCase):
    #fixtures = ['licences.json', 'countries.json', 'catalogue.json', 'partner.json', 'returns.json']

    #def setUp(self):
    #    logger.info('setup')

    #    test_user = EmailUser(email='unit.test@someorg.com',
    #                          first_name='unit',
    #                          last_name='test',
    #                          is_staff=True,
    #                          title='Mr',
    #                         dob='2019-12-10',
    #                          phone_number='92644545',
    #                          extra_data='').save()

    #    app = Application(application_type='new_licence',
    #                      data=TEST_DATA,
    #                      assessor_data='',
    #                      comment_data='',
    #                      licence_type_data=TEST_LICENCE_TYPE_DATA,
    #                      licence_type_name='Fauna Industry - Taking (), Processing (), Dealing (Dealing (pet dealer))',
    #                      licence_category='Fauna Industry',
    #                      schema=TEST_SCHEMA_DATA,
    #                      proposed_issuance_licence='',
    #                      customer_status='under_review',
    #                      lodgement_number='A000100',
    #                      lodgement_sequence=0,
    #                      lodgement_date=timezone.now(),
    #                      processing_status='draft',
    #                      id_check_status='not_checked',
    #                      return_check_status='not_checked',
    #                      character_check_status='not_checked',
    #                      review_status='not_reviewed',
    #                      proposed_decline_status='False',
    #                      application_fee=0
    #                      )

    #    app.schema = TEST_SCHEMA_DATA
    #    app.data = TEST_DATA
        # app.licence_type_data = TEST_LICENCE_TYPE_DATA
    #    app.submitter = test_user
    #    app.save()

    #    address = OrganisationAddress(line1='21 Dick Perry Ave', locality='Kensington', postcode='6052').save()
    #    org = Organisation(name='Test Organisation', abn='1')
    #    org.postal_address = address
    #    org.save()

    #    licence_activity = WildlifeLicenceActivity(name='Dealing').save()

    #    licence_activity_type = WildlifeLicenceActivityType(licence_activity_status='current', name='Flora Industry')
        #licence_activity_type.activity = licence_activity
    #    licence_activity_type.save()

    #    licence_class = WildlifeLicenceClass(licence_class_status='current')
        #licence_class.activity_type = licence_activity_type
    #    licence_class.save()

    #    licence = WildlifeLicence(status='current',
    #                              start_date='2018-07-01',
    #                              expiry_date=datetime.datetime.now(),
    #                              licence_number='01-000001',
    #                              renewal_sent=False,
    #                              licence_sequence=1)
    #    licence.submitter = test_user
    #    licence.applicant = org
    #    licence.current_application = app
    #    licence.licence_class = licence_class
    #    licence.licence_type = TEST_LICENCE_TYPE_DATA
    #    licence.save()

    #    self.customer = get_or_create_default_customer(include_default_profile=True)
    #    self.officer = get_or_create_default_officer()

    #    self.client = SocialClient()

        #self.licence = create_licence(self.customer, self.officer, product_title='regulation-17')
    #    self.licence = WildlifeLicence.objects.first()
    #    self.ret = create_return(self.licence)

    #def tearDown(self):
    #    self.client.logout()

    #def test_lodge_nil_return(self):
    #   """Testing that a user can log a nil return"""

    #    self.client.login(self.customer.email)

    #    post_params = {
    #        'nil': True,
    #        'comments': 'No survey taken'
    #    }
    #    response = self.client.post(reverse('wl_returns:enter_return', args=(self.ret.pk,)),
    #                                post_params)

   #     self.assertRedirects(response, reverse('home'),
    #                         status_code=302, target_status_code=200, fetch_redirect_response=False)

    #def test_upload_return_spreadsheet(self):
    #    """Testing that a user can upload a return spreadsheet"""
    #
    #    self.client.login(self.customer.email)
    #
    #    with open(TEST_SPREADSHEET_PATH, 'rb') as fp:
    #        post_params = {
    #            'upload': True,
    #            'spreadsheet_file': fp
    #        }
    #        response = self.client.post(reverse('wl_returns:enter_return', args=(self.ret.pk,)),
    #                                    post_params)
    #
    #    self.assertEqual(200, response.status_code)
    #
    #    # assert values in the response context match those in the spreadsheet
    #    for key, value in response.context['tables'][0]['data'][0].items():
    #        self.assertEqual(value['value'], TEST_VALUES[key])

    #def test_lodge_return(self):
    #    """Testing that a user can lodge a return"""
    #    self.client.login(self.customer.email)

        # check return status is intially 'current'
    #    self.assertEqual(self.ret.status, 'current')

    #    post_params = {
    #        'lodge': True,
    #    }

    #    for key, value in TEST_VALUES.items():
    #        post_params['regulation-17::{}'.format(key)] = value

    #    response = self.client.post(reverse('wl_returns:enter_return', args=(self.ret.pk,)), post_params)

    #    self.assertRedirects(response, reverse('home'),
    #                         status_code=302, target_status_code=200, fetch_redirect_response=False)

    #    self.ret.refresh_from_db()

        # check return status is 'submitted'
    #    self.assertEqual(self.ret.status, 'submitted')

        # assert values in the return is what is expected
    #    for key, value in self.ret.returntable_set.first().returnrow_set.first().data.items():
    #        self.assertEqual(value, str(TEST_VALUES[key]))