from mixer.backend.django import mixer
from django.conf import settings
from importlib import import_module
from django.utils import timezone
from datetime import timedelta

from wildlifecompliance.management.default_data_manager import DefaultDataManager
#from .models import *
from ledger.accounts.models import EmailUser, EmailUserManager
import random
import string
import json, io, os, sys
from rest_framework.test import (
        APIRequestFactory, 
        force_authenticate, 
        APITestCase,
        APILiveServerTestCase,
        RequestsClient,
        )
from rest_framework import status
from ledger.accounts.models import EmailUser, Address
from ledger.address.models import UserAddress
from requests.auth import HTTPBasicAuth
from wildlifecompliance.components.call_email.models import (
        CallEmail,
        CallType,
        )
from wildlifecompliance.components.main.models import (
        ComplianceManagementSystemGroup,
        Region,
        District,
        )


class APITestSetup(APITestCase):
    fixtures = ['countries.json']

    def setUp(self):
        print("setup method")
        # Create security groups
        self.region = Region.objects.create(name="South West", cddp_name="South West")
        self.district = District.objects.create(name="Blackwood", cddp_name="Blackwood", region=self.region)
        #self.callemailtriagegroup = CallEmailTriageGroup.objects.create(region=self.region, district=self.district)
        #self.volunteergroup = VolunteerGroup.objects.first()
        #self.callemailreadonlygroup = ComplianceManagementCallEmailReadOnlyGroup.objects.first()
        self.callemailtriagegroup = ComplianceManagementSystemGroup.objects.create(
                name=settings.GROUP_CALL_EMAIL_TRIAGE, 
                region=self.region, 
                district=self.district
                )
        self.volunteergroup = ComplianceManagementSystemGroup.objects.get(name=settings.GROUP_VOLUNTEER)
        self.callemailreadonlygroup = ComplianceManagementSystemGroup.objects.get(name=settings.GROUP_COMPLIANCE_MANAGEMENT_CALL_EMAIL_READ_ONLY)

        self.superAdminUN = 'test.superadmin@dbcatest.com'
        self.adminUN = 'test.admin@dbcatest.com'
        self.nonAdminUN = 'test.customer@dbcatest.com'
        superadminUser = None
        adminUser = None
        user = None
        eum = EmailUserManager()
        self.superadminUser = EmailUser.objects.create(email=self.superAdminUN, password="pass", is_staff=True, is_superuser=True)
        self.superadminUser.set_password('pass')
        self.superadminUser.save()
        self.adminUser  = EmailUser.objects.create(email=self.adminUN,password="pass",is_staff=True, is_superuser=False)
        self.adminUser.set_password('pass')
        self.adminUser.save()

        #self.volunteer1 = EmailUser.objects.create(email=self.nonAdminUN, password="pass", is_staff=False, is_superuser=False)
        self.volunteer1 = EmailUser.objects.create(email="volunteer1@dbcatest.com", password="pass", is_staff=True, is_superuser=False)
        self.volunteer1.set_password('pass')
        self.volunteer1.save()
        # customer UserAddress
        user_address = UserAddress.objects.create(
                country_id= 'AU',
                #is_default_for_billing= True,
                #is_default_for_shipping= True,
                line1= '17 Dick Perry',
                #line2: '',
                #line3': u'',
                #line4': u'BENTLEY DELIVERY CENTRE',
                #notes': u'',
                #num_orders': 0,
                #phone_number': None,
                postcode= '6151',
                #'search_text': u'',
                state= 'WA',
                #title': u'',
                user_id= self.volunteer1.id
                )

        volunteer1_address = Address.objects.create(user=self.volunteer1, oscar_address=user_address)
        self.volunteer1.residential_address = volunteer1_address
        self.volunteer1.save()
        self.volunteergroup.add_member(self.volunteer1)

        self.callemailtriage1 = EmailUser.objects.create(email="callemailtriage1@dbcatest.com", password="pass", is_staff=False, is_superuser=False)
        self.callemailtriage1.set_password('pass')
        self.callemailtriage1.save()
        # customer UserAddress
        user_address = UserAddress.objects.create(
                country_id= 'AU',
                #is_default_for_billing= True,
                #is_default_for_shipping= True,
                line1= '17 Dick Perry',
                #line2: '',
                #line3': u'',
                #line4': u'BENTLEY DELIVERY CENTRE',
                #notes': u'',
                #num_orders': 0,
                #phone_number': None,
                postcode= '6151',
                #'search_text': u'',
                state= 'WA',
                #title': u'',
                user_id= self.callemailtriage1.id
                )

        callemailtriage1_address = Address.objects.create(user=self.callemailtriage1, oscar_address=user_address)
        self.callemailtriage1.residential_address = callemailtriage1_address
        self.callemailtriage1.save()
        self.callemailtriagegroup.add_member(self.callemailtriage1)

        settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        self.session = store
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

        # CallType
        self.calltype1 = CallType.objects.create(name="calltype1")

        # create call_email data
        self.create_call_email_data = {}

        # submit_call_email_data
        with open('wildlifecompliance/tests/all_the_features_1.json', 'r') as features_file_1:
            self.all_the_features_1 = json.load(features_file_1)
        with open('wildlifecompliance/tests/all_the_features_2.json', 'r') as features_file_2:
            self.all_the_features_2 = json.load(features_file_2)

        # Dates
        self.today = timezone.now().date()
        self.today_str = self.today.strftime('%d/%m/%Y')
        day_delta = timedelta(days=1)
        week_delta = timedelta(weeks=1)
        self.today_plus_1_day = self.today + day_delta
        self.today_plus_1_week = self.today + day_delta
        self.today_plus_26_weeks = self.today + (day_delta * 26)
        self.today_plus_1_day_str = self.today_plus_1_day.strftime('%d/%m/%Y')
        self.today_plus_1_week_str = self.today_plus_1_week.strftime('%d/%m/%Y')
        self.today_plus_26_weeks_str = self.today_plus_26_weeks.strftime('%d/%m/%Y')

        # Get data ready
        temp = DefaultDataManager()

    def random_email(self):
        """Return a random email address ending in dbca.wa.gov.au
        """
#        print time
#        time.sleep(5)
        # import time as systime
        # systime.sleep(2)
        s = ''.join(random.choice(string.ascii_letters) for i in range(80))
        return '{}@dbca.wa.gov.au'.format(s)


# write location data to file
def json_filewriter_example():
    # open(os.path.join(sys.path[0], input_file), 'r')
    input_file = 'all_the_features_1.json'
    with io.open(os.path.join(sys.path[0], input_file), 'w', encoding="utf8") as json_file:
        data = json.dumps(d, ensure_ascii=False, encoding="utf8")
        json_file.write(unicode(data))

