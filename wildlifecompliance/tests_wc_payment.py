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

from wildlifecompliance.components.main.utils import (
    checkout,
    set_session_application,
    set_session_activity,
    delete_session_application


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


class PaymentTest(TestCase):

    def setUp(self):

        test_user = EmailUser(email='unit.test@someorg.com',
                              first_name='unit',
                              last_name='test',
                              is_staff=True,
                              title='Mr',
                              dob='2019-12-10',
                              phone_number='92644545',
                              extra_data='').save()

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

    @tag('pay-checkout')
    def test_checkout(self):
        try:
            instance = Application.objects.get(lodgement_number='A000100')
            request = RequestFactory()
            product_lines = []
            application_submission = u'Application submitted by {} confirmation {}'.format(
                u'{} {}'.format(instance.submitter.first_name, instance.submitter.last_name), instance.lodgement_number)
            set_session_application(request.session, instance)
            product_lines.append({
                'ledger_description': '{}'.format(instance.licence_type_name),
                'quantity': 1,
                'price_incl_tax': str(instance.application_fee),
                'price_excl_tax': str(calculate_excl_gst(instance.application_fee)),
                'oracle_code': ''
            })
            #checkout_result = checkout(request, instance, lines=product_lines,
            #                           invoice_text=application_submission)
            return checkout_result
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0].encode('utf-8')))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))