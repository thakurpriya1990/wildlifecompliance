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
from wildlifecompliance.components.applications.models import Application, ApplicationSelectedActivity
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

        BpointToken(DVToken=5999993673975627,
                    masked_card='XXXX-XXXX-XXXX-4122',
                    expiry_date='2029-03-10',
                    user_id=EmailUser.objects.first().id,
                    card_type='VC').save()       

        test_user = EmailUser(email='unit.test@someorg.com',
                              first_name='unit',
                              last_name='test',
                              is_staff=True,
                              title='Mr',
                              dob='2019-12-10',
                              phone_number='92644545',
                              extra_data='').save()

        licence_type_FAU = LicenceType(name='FAUNA',
                                       code='FAU',
                                       is_renewable=True,
                                       short_name='Fauna',
                                       version=1).save()

        licence_cat_FAU = LicenceCategory(licencetype_ptr_id=licence_type_FAU.id).save()

        licence_act_FAU_TAKING = LicenceActivity(name='Fauna - Taking',
                                                 short_name='Taking',
                                                 not_for_organisation=False,
                                                 licence_category_id=licence_cat_FAU.id).save()  

        an_app = Application(application_type='new_licence',
                             comment_data='',
                             customer_status='default',
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
                                  customer_status='draft',
                                  lodgement_number='A000200',
                                  lodgement_date=timezone.now(),
                                  id_check_status='not_checked',
                                  return_check_status='not_checked',
                                  character_check_status='not_checked',
                                  review_status='not_reviewed',
                                  application_fee=0)

        another_app.submitter = test_user
        another_app.save()

        return_sheet_type = ReturnType(name='sheet')
        return_sheet_type.data_descriptor = '{}'
        return_sheet_type.save()

        return_question_type = ReturnType(name='question')
        return_question_type.data_descriptor = '{}'
        return_question_type.save()

        return_data_type = ReturnType(name='data')
        return_data_type.data_descriptor = '{}'
        return_data_type.save()

        address = OrganisationAddress(line1='21 Dick Perry Ave', locality='Kensington', postcode='6052').save()
        org = Organisation(name='Test Organisation', abn='1')
        org.postal_address = address
        org.save()

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

    @tag('licence-checkout')
    def test_checkout(self):

        request = RequestFactory()
        request.user = EmailUser.objects.first()
        client = Client(request)
        client.
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