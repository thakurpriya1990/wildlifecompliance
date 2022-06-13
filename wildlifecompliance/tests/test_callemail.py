from wildlifecompliance.settings import HTTP_HOST_FOR_TEST
from wildlifecompliance.tests.test_setup import APITestSetup


class ProposalTests(APITestSetup):
    def test_create_call_email(self):
        print("test_create_call_email")
        self.client.login(email=self.volunteer1, password='pass')
        self.client.enforce_csrf_checks=True
        create_response = self.client.post(
            '/api/call_email/',
            self.create_call_email_data,
            format='json',
            HTTP_HOST=HTTP_HOST_FOR_TEST,
        )
        print("create_response.status_code")
        print(create_response.status_code)

        self.assertEqual(create_response.status_code, 201)
        self.assertTrue(create_response.data.get('id') > 0)

