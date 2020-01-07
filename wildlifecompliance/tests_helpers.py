from __future__ import unicode_literals

import os
import datetime
import re

from rest_framework import status

from django.contrib.auth.models import Group
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django.utils.encoding import smart_text
from django.contrib.messages import constants as message_constants
from django_dynamic_fixture import G

from ledger.accounts.models import EmailUser, Profile, Address, Country
from wildlifelicensing.apps.main import helpers as accounts_helpers
from wildlifecompliance.components.licences.models import WildlifeLicence

from ledger.accounts.models import EmailUser, Organisation, OrganisationAddress

import copy
from datetime import date, timedelta

from wildlifecompliance.components.returns.models import Return, ReturnType


def clone(descriptor):
    return copy.deepcopy(descriptor)


BASE_CONSTRAINTS = {
    "required": False
}

NOT_REQUIRED_CONSTRAINTS = {
    "required": False
}

REQUIRED_CONSTRAINTS = {
    "required": True
}

BASE_FIELD = {
    "name": "Name",
    "tile": "Title",
    "type": "string",
    "format": "default",
    "constraints": clone(BASE_CONSTRAINTS)
}

GENERIC_SCHEMA = {
    "fields": [
        clone(BASE_FIELD)
    ]
}

GENERIC_DATA_PACKAGE = {
    "name": "test",
    "resources": [
        {
            "name": "test",
            "format": "CSV",
            "title": "test",
            "bytes": 0,
            "mediatype": "text/csv",
            "path": "test.csv",
            "schema": clone(GENERIC_SCHEMA)
        }
    ],
    "title": "Test"
}

SPECIES_NAME_FIELD = {
    "name": "Species Name",
    "type": "string",
    "format": "default",
    "constraints": {
        "required": True
    },
    "wl": {
        "type": "species"
    }
}

LAT_LONG_OBSERVATION_SCHEMA = {
    "fields": [
        {
            "name": "Observation Date",
            "type": "date",
            "format": "any",
            "constraints": {
                "required": True,
            }
        },
        {
            "name": "Latitude",
            "type": "number",
            "format": "default",
            "constraints": {
                "required": True,
                "minimum": -90.0,
                "maximum": 90.0,
            }
        },
        {
            "name": "Longitude",
            "type": "number",
            "format": "default",
            "constraints": {
                "required": True,
                "minimum": -180.0,
                "maximum": 180.0,
            }
        },
    ]
}

TEST_SCHEMA_DATA = {"id": 1, "name": "Fauna Industry - Taking", "type": "tab", "label": "Fauna Industry - Taking",
               "status": "Draft",
               "children": [{"name": "Section1_0", "type": "section", "label": "Section 1",
               "children": [{"name": "Section1-0_0", "type": "text_area","label": "The first question in section 1"},
                            {"name": "Section1-1_0", "type": "text","label": "The second question in section 1"},
                            {"name": "Section1-2_0", "type": "text", "label": "The third question in section 1"}]},
                            {"name": "Section2_0", "type": "section", "label": "Section 2",
               "children": [{"name": "Section2-0_0", "type": "text_area", "label": "The first question in section 2"},
                            {"name": "Section2-1_0", "type": "text", "label": "The second question in section 2"},
                            {"name": "Section2-2_0", "type": "text", "label": "The third question in section 2"}]}]},\
              {"id": 2, "name": "Fauna Industry - Processing", "type": "tab","label": "Fauna Industry - Processing",
               "status": "Draft",
               "children": [{"name": "Section1_1", "type": "section", "label": "Section 1",
               "children": [{"name": "Section1-0_1", "type": "text_area", "label": "The first question in section 1"},
                            {"name": "Section1-1_1", "type": "text", "label": "The second question in section 1"},
                            {"name": "Section1-2_1", "type": "text", "label": "The third question in section 1"}]},
                            {"name": "Section2_1", "type": "section", "label": "Section 2",
               "children": [{"name": "Section2-0_1", "type": "text_area", "label": "The first question in section 2"},
                            {"name": "Section2-1_1", "type": "text", "label": "The second question in section 2"},
                            {"name": "Section2-2_1", "type": "text", "label": "The third question in section 2"}]}]}, \
              {"id": 3, "name": "Fauna Industry - Dealing", "type": "tab", "label": "Fauna Industry - Dealing",
               "status": "Draft",
               "children": [{"name": "ADS_applicationSection_2", "type": "section", "label": "This is a long label for Fauna dealing (pet dealer) licence",
               "children": [{"name": "ADS_Application0_2", "type": "label", "label": "Please click here to download the application form"},
                            {"name": "ADS_Application1_2", "type": "label", "label": ""},
                            {"name": "ADS_Application2_2", "type": "file", "label": "Attach the completed application form here"}]}]}

TEST_DATA = {"Fauna Industry - Dealing": [{"ADS_applicationSection_2": [{"ADS_Application2_2": ""}]}],
             "Fauna Industry - Disturbing": [
                 {"Section1_0": [{"Section1-0_0": "section1", "Section1-1_0": "", "Section1-2_0": ""}],
                  "Section2_0": [{"Section2-0_0": "", "Section2-1_0": "", "Section2-2_0": ""}],
                  "Section3_0": [{"Section3-0_0": "", "Section3-1_0": "", "Section3-2_0": ""}],
                  "Section4_0": [{"Section4-0_0": "", "Section4-1_0": "", "Section4-2_0": ""}],
                  "Section5_0": [{"Section5-0_0": "", "Section5-1_0": "", "Section5-2_0": ""}]}],
             "Fauna Industry - Processing": [
                 {"Section1_1": [{"Section1-0_1": "section tab 2", "Section1-1_1": "", "Section1-2_1": ""}],
                  "Section2_1": [{"Section2-0_1": "", "Section2-1_1": "", "Section2-2_1": ""}]}]}

SPECIES_SCHEMA = clone(LAT_LONG_OBSERVATION_SCHEMA)
SPECIES_SCHEMA['fields'].append(clone(SPECIES_NAME_FIELD))

SPECIES_DATA_PACKAGE = clone(GENERIC_DATA_PACKAGE)
SPECIES_DATA_PACKAGE['resources'][0]['schema'] = clone(SPECIES_SCHEMA)

TEST_LICENCE_TYPE_DATA = {"id": 1, "name": "Fauna Industry Licence", "short_name": "Fauna Industry",
                          "activity_type": [{"id": 4, "name": "Fauna Industry - Taking", "activity": [
                              {"id": 4, "name": "Taking Live Fauna for Commercial Purpose", "short_name": ""}],
                                             "short_name": "Taking", "proposed_decline": False,
                                             "processing_status": "With Officer"},
                                            {"id": 7, "name": "Fauna Industry - Processing", "activity": [
                                                {"id": 8, "name": "Processing Fauna (e.g. crocodiles)",
                                                 "short_name": ""}], "short_name": "Processing",
                                             "proposed_decline": False, "processing_status": "With Officer"},
                                            {"id": 8, "name": "Fauna Industry - Dealing", "activity": [
                                                {"id": 10, "name": "Fauna dealing (pet dealer) licence",
                                                 "short_name": "Dealing (pet dealer)"}], "short_name": "Dealing",
                                             "proposed_decline": False, "processing_status": "With Officer"}]}

TEST_LICENCE_PURPOSE_SCHEMA = {"name": "Section1", "type": "section", "label": "Section 1", "children": [
    {"name": "Section1-0", "type": "text_area", "label": "The first question in section 1"}, {"name": "Section1-1",
    "type": "text", "label": "The second question in section 1"}, {"name": "Section1-2", "type": "text",
    "label": "The third question in section 1"}]}, {"name": "Section2", "type": "section", "label": "Section 2",
    "children": [{"name": "Section2-0", "type": "text_area", "label": "The first question in section 2"},
   {"name": "Section2-1", "type": "text", "label": "The second question in section 2"}, {"name": "Section2-2",
    "type": "text", "label": "The third question in section 2"}]}

TEST_RETURN_SHEET_SCHEMA = {"name": "sheet", "title": "Standard return for stock", "resources": [{"name": "sheet",
                            "path": "", "title": "Stock Return", "schema": {"fields": [{"stype": {"type": "species",
                            "speciesType": "fauna"}, "name": "SPECIES", "type": "string", "constraints":
                           {"required": True }}, {"name": "DATE", "type": "date", "format": "fmt:%d/%m/%Y",
                            "constraints": {"required": True}}, {"sgroup": {"type": "speciesGroup",   "speciesGroup":
                            "stock" }, "name": "TYPE", "type": "string", "constraints": {"required": True}}, {"name":
                            "QUANTITY", "type": "number", "constraints": {"required": True }}, {"name": "TOTAL",
                            "type": "number", "constraints": {"required": True}}, {"name": "COMMENTS", "type":
                            "string"}]}}]}


def get_or_create_return_type(licence_type):
    return ReturnType.objects.get_or_create(licence_type=licence_type)[0]


def create_return(licence):
    return_type = get_or_create_return_type(licence.licence_type)

    return Return.objects.create(return_type=return_type, licence=licence, due_date=date.today() + timedelta(weeks=52),
                                 status='current')

class TestData(object):
    TEST_ID_PATH = os.path.join('wildlifelicensing', 'apps', 'main', 'test_data', 'test_id.jpg')

    DEFAULT_CUSTOMER = {
        'email': 'customer@test.com',
        'first_name': 'Homer',
        'last_name': 'Cust',
        'dob': datetime.date(1989, 8, 12),
    }
    DEFAULT_PROFILE = {
        'email': 'customer@test.com',
    }
    DEFAULT_ADDRESS = {
        'line1': '1 Test Street',
        'locality': 'Testland',
        'postcode': '7777',
    }
    DEFAULT_OFFICER = {
        'email': 'officer@test.com',
        'first_name': 'Offy',
        'last_name': 'Sir',
        'dob': datetime.date(1979, 12, 13),
    }
    DEFAULT_ASSESSOR = {
        'email': 'assessor@test.com',
        'first_name': 'Assess',
        'last_name': 'Ore',
        'dob': datetime.date(1979, 10, 5),
    }
    DEFAULT_ASSESSOR_GROUP = {
        'name': 'ass group',
        'email': 'assessor@test.com',
    }
    DEFAULT_API_USER = {
        'email': 'apir@test.com',
        'first_name': 'api',
        'last_name': 'user',
        'dob': '1979-12-13',
    }


class SocialClient(Client):
    """
    A django Client for authenticating with the social auth password-less framework.
    """

    def login(self, email):
        # important clear the mail box before
        clear_mailbox()
        self.post(reverse('social:complete', kwargs={'backend': "email"}), {'email': email})
        if len(mail.outbox) == 0:
            raise Exception("Email not received")
        else:
            login_url = re.search('(?P<url>https?://[^\s]+)', mail.outbox[0].body).group('url')
            response = self.get(login_url, follow=True)
            clear_mailbox()
        return response

    def logout(self):
        self.get(reverse('accounts:logout'))


def create_default_country():
    return G(Country, iso_3166_1_a2='AU')


def is_client_authenticated(client):
    return '_auth_user_id' in client.session


def belongs_to(user, group_name):
    return accounts_helpers.belongs_to(user, group_name)


def add_to_group(user, group_name):
    if not belongs_to(user, group_name):
        group, created = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
        user.save()
    return user


def get_or_create_user(params):
    user, created = EmailUser.objects.get_or_create(**params)
    return user, created


def create_random_user():
    return G(EmailUser, dob='1970-01-01')


def create_random_customer():
    return create_random_user()


def get_or_create_default_customer(include_default_profile=False):
    user, created = get_or_create_user(TestData.DEFAULT_CUSTOMER)

    if include_default_profile:
        create_default_country()
        address = Address.objects.create(user=user, **TestData.DEFAULT_ADDRESS)
        profile = Profile.objects.create(user=user, postal_address=address, **TestData.DEFAULT_PROFILE)
        profile.user = user

    return user


def get_or_create_default_officer():
    user, created = get_or_create_user(TestData.DEFAULT_OFFICER)
    if created:
        add_to_group(user, 'Officers')
    return user


def get_or_create_api_user():
    user, created = get_or_create_user(TestData.DEFAULT_API_USER)
    if created:
        add_to_group(user, 'API')
    return user


#def get_or_create_licence_type(product_title='regulation-17'):
#    return WildlifeLicenceType.objects.get_or_create(product_title=product_title)[0]

def get_or_create_org_1():
    address = OrganisationAddress(line1='21 Dick Perry Ave', locality='Kensington', postcode='6052').save()
    org = Organisation(name='Test Organisation', abn='1')
    org.postal_address = address
    org.save()
    return org


def get_or_create_default_assessor():
    user, created = get_or_create_user(TestData.DEFAULT_ASSESSOR)
    if created:
        add_to_group(user, 'Assessors')
    return user


def get_or_create_default_assessor_group():
    pass
    #return ApplicationAssessorGroup.objects.get(default=True)
    #return AssessorGroup.objects.get_or_create(defaults=TestData.DEFAULT_ASSESSOR_GROUP,
    #                                           name=TestData.DEFAULT_ASSESSOR_GROUP['name'])[0]


def add_assessor_to_assessor_group(assessor, group):
    group.members.add(assessor)
    group.save()


def is_login_page(response):
    if hasattr(response, 'content'):
        content = response.content
    else:
        content = smart_text(response)
    return content.find(b'<div id="wl-login-container">') > 0


def get_emails():
    return mail.outbox


def get_email():
    emails = get_emails()
    return emails[0] if len(emails) > 0 else None


def is_email():
    return len(get_emails()) > 0


def clear_mailbox():
    mail.outbox = []


def upload_id(user):
    with open(TestData.TEST_ID_PATH, 'rb') as fp:
        post_params = {
            'identification': True,
            'identification_file': fp
        }
        client = SocialClient()
        client.login(user.email)
        response = client.post(reverse('wl_main:identification'), post_params, follow=True)
        client.logout()
        return response


def clear_id_file(user):
    if user.identification:
        os.remove(user.identification.path)


def clear_all_id_files():
    for user in EmailUser.objects.all():
        clear_id_file(user)


def get_user_home_url(user):
    if accounts_helpers.is_officer(user):
        return '/dashboard/officer'
    elif accounts_helpers.is_assessor(user):
        return '/dashboard/tables/assessor'

    return '/dashboard/tables/customer'


def get_response_messages(response):
    if 'messages' in response.context:
        return list(response.context['messages'])
    return []


def has_response_messages(response):
    return len(get_response_messages(response)) > 0


def get_response_error_messages(response):
    return [m for m in get_response_messages(response) if m.level == message_constants.ERROR]


def has_response_error_messages(response):
    return len(get_response_error_messages(response)) > 0


class BaseUserTestCase(TestCase):
    """
    A test case that provides some users
    """
    client_class = SocialClient

    def _pre_setup(self):
        super(BaseUserTestCase, self)._pre_setup()
        self.customer = get_or_create_default_customer(include_default_profile=True)
        self.officer = get_or_create_default_officer()
        self.assessor = get_or_create_default_assessor()
        self.all_users = [
            self.officer,
            self.assessor,
            self.customer
        ]

    def _post_teardown(self):
        super(BaseUserTestCase, self)._post_teardown()
        self.client.logout()


class BasePermissionViewTestCase(BaseUserTestCase):
    view_url = None

    @property
    def permissions(self):
        """
        Override this method to define permissions for relevant method.
        Example:
        {
            'get': {
                'allowed': [self.officer],
                'forbidden': [self.customer, self.assessor],
                'kwargs': {}
            }
            'post': {
                'allowed': [self.officer],
                'forbidden': [self.customer, self.assessor]
                'kwargs': {
                    'data': {}
                }
            },
        }
        Note: the kwargs are passed to the request method. Useful for post data
        """
        return None

    def test_permissions(self):
        if not self.view_url:
            return
        permissions = self.permissions or {}
        verbs = ['get', 'post', 'put', 'patch', 'delete']
        for verb in verbs:
            method = getattr(self.client, verb)
            if callable(method):
                if verb in permissions:
                    allowed = permissions[verb].get('allowed', [])
                    forbidden = permissions[verb].get('forbidden', self.all_users)
                    kwargs = permissions[verb].get('kwargs', {})
                    for user in allowed:
                        self.client.login(user.email)
                        response = method(self.view_url, **kwargs)
                        expected_status = status.HTTP_200_OK
                        self.assertEqual(
                            response.status_code, expected_status,
                            msg="{got} != {expected} for user {user} with method {verb} at {url} with params {kwargs}".format(
                                got=response.status_code,
                                expected=expected_status,
                                user=user.email,
                                verb=verb,
                                url=self.view_url,
                                kwargs=kwargs,
                            )
                        )
                        self.client.logout()

                    for user in forbidden:
                        self.client.login(user.email)
                        response = method(self.view_url, **kwargs)
                        expected_status = status.HTTP_403_FORBIDDEN
                        self.assertEqual(
                            response.status_code, expected_status,
                            msg="{got} != {expected} for user {user} with method {verb} at {url} with params {kwargs}".format(
                                got=response.status_code,
                                expected=expected_status,
                                user=user.email,
                                verb=verb,
                                url=self.view_url,
                                kwargs=kwargs,
                            )
                        )
                        self.client.logout()
                else:
                    # method not in the permissions list should return 405 (or 403)
                    for user in self.all_users:
                        self.client.login(user.email)
                        response = method(self.view_url, **kwargs)
                        expected_statuses = [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_403_FORBIDDEN]
                        self.assertIn(
                            response.status_code, expected_statuses,
                            msg="{got} != {expected} for user {user} with method {verb} at {url} with params {kwargs}".format(
                                got=response.status_code,
                                expected=expected_statuses,
                                user=user.email,
                                verb=verb,
                                url=self.view_url,
                                kwargs=kwargs,
                            )
                        )
                        self.client.logout()
            else:
                self.fail('Method {} is not supported by client.'.format(verb))


class HelpersTest(TestCase):
    def setUp(self):
        self.client = SocialClient()

    def test_create_default_customer(self):
        user = get_or_create_default_customer()
        self.assertIsNotNone(user)
        self.assertTrue(isinstance(user, EmailUser))
        self.assertEqual(TestData.DEFAULT_CUSTOMER['email'], user.email)
        self.assertTrue(accounts_helpers.is_customer(user))
        # test that we can login
        self.client.login(user.email)
        is_client_authenticated(self.client)

    def test_create_default_officer(self):
        user = get_or_create_default_officer()
        self.assertIsNotNone(user)
        self.assertTrue(isinstance(user, EmailUser))
        self.assertEqual(TestData.DEFAULT_OFFICER['email'], user.email)
        self.assertTrue(accounts_helpers.is_officer(user))
        # test that we can login
        self.client.login(user.email)
        is_client_authenticated(self.client)

    def test_create_default_assessor(self):
        user = get_or_create_default_assessor()
        self.assertIsNotNone(user)
        self.assertTrue(isinstance(user, EmailUser))
        self.assertEqual(TestData.DEFAULT_ASSESSOR['email'], user.email)
        self.assertTrue(accounts_helpers.is_assessor(user))
        # test that we can login
        self.client.login(user.email)
        is_client_authenticated(self.client)

    def create_random_user(self):
        user = create_random_user()
        self.assertIsNotNone(user)
        self.assertTrue(isinstance(user, EmailUser))
        self.assertEqual(TestData.DEFAULT_CUSTOMER['email'], user.email)
        # test that we can login
        self.client.login(user.email)
        is_client_authenticated(self.client)

    def create_random_customer(self):
        user = create_random_customer()
        self.assertIsNotNone(user)
        self.assertTrue(isinstance(user, EmailUser))
        self.assertEqual(TestData.DEFAULT_CUSTOMER['email'], user.email)
        self.assertTrue(accounts_helpers.is_customer(user))
        # test that we can login
        self.client.login(user.email)
        is_client_authenticated(self.client)


class TestClient(TestCase):
    def test_login_logout_login(self):
        user = get_or_create_default_customer()
        client = SocialClient()
        self.assertFalse(is_client_authenticated(client))
        client.login(user.email)
        self.assertTrue(is_client_authenticated(client))
        client.logout()
        self.assertFalse(is_client_authenticated(client))
        client.login(user.email)
        self.assertTrue(is_client_authenticated(client))
        self.assertEqual(smart_text(user.pk), client.session.get('_auth_user_id'))
        client.logout()
        officer = get_or_create_default_officer()
        client.login(officer.email)
        self.assertTrue(is_client_authenticated(client))
        self.assertEqual(smart_text(officer.pk), client.session.get('_auth_user_id'))
        client.logout()
        client.login(user.email)
        self.assertTrue(is_client_authenticated(client))
        self.assertEqual(smart_text(user.pk), client.session.get('_auth_user_id'))
