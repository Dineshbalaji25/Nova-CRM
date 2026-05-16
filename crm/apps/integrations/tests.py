from django.test import TestCase


class IntegrationsDashboardAuthTest(TestCase):
    def test_unauthenticated_user_redirects_to_login_page(self):
        response = self.client.get('/integrations')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login?next=/integrations'))
