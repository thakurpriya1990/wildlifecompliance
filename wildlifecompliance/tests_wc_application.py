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


class ApplicationTest(TestCase):

    def setUp(self):

        # credit card - 5123456789012346

        BpointToken(DVToken=5999996007564314,
                    masked_card='XXXX-XXXX-XXXX-2346',
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

        licence_type = LicenceType(name='FAUNA',
                                   code='FAU',
                                   is_renewable=True,
                                   short_name='Fauna',
                                   version=1).save()

        licence_category = LicenceCategory(licencetype_ptr_id=licence_type.id).save()

        licence_activity = LicenceActivity(name='Fauna - Taking',
                                           short_name='Taking',
                                           not_for_organisation=False,
                                           licence_category_id=licence_category.id).save()  

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

        app_selected_activity = ApplicationSelectedActivity(application_id=an_app.id,
                                                            licence_activity_id=licence_activity.id,
                                                            decision_action='default',
                                                            proposed_action='default',
                                                            processing_status='draft',
                                                            activity_status='default',
                                                            is_inspection_required='false',
                                                            licence_fee=0).save()

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

        app_selected_activity = ApplicationSelectedActivity(application_id=an_app.id,
                                                            licence_activity_id=licence_activity.id,
                                                            decision_action='default',
                                                            proposed_action='default',
                                                            processing_status='draft',
                                                            activity_status='default',
                                                            is_inspection_required='false',
                                                            licence_fee=0).save()

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

    @tag('application-draft')
    def test_draft_application(self):
        """
        External user creating a new licence application
        :return:
        """
        logger.info('APPLICATION: Assert the creating a draft application.')

        submitter = EmailUser.objects.first()
        logger.info(submitter)

        an_app = Application(application_type='new_licence',
                             comment_data='',
                             customer_status='draft',
                             lodgement_number='A000001',
                             id_check_status='not_checked',
                             return_check_status='not_checked',
                             character_check_status='not_checked',
                             review_status='not_reviewed',
                             application_fee=25
                             )

        an_app.submitter = submitter
        an_app.save()
        logger.info(an_app)
        self.assertTrue(an_app)
    
    def tearDown(self):
        pass
