from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.users.models import OAuthApplication, Organization, OrganizationMember

User = get_user_model()


class OAuthClientScopesTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(name="Scope Org", slug="scope-org")
        self.user = User.objects.create_user(email="scope@example.com", password="password123")
        OrganizationMember.objects.create(user=self.user, organization=self.organization, role='owner')
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.organization.id))

    def test_create_oauth_app_with_allowed_scopes(self):
        response = self.client.post('/api/v1/oauth-apps/', {
            "name": "Test Integration",
            "redirect_uri": "https://example.com/oauth/callback",
            "allowed_scopes": [
                "NovaCRM.modules.READ",
                "NovaCRM.settings.READ",
            ],
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["client_id"].startswith("client_"))
        self.assertTrue(response.data["client_secret"].startswith("secret_"))
        self.assertEqual(response.data["allowed_scopes"], ["NovaCRM.modules.READ", "NovaCRM.settings.READ"])

    def test_token_exchange_rejects_scope_not_allowed_by_client(self):
        app = OAuthApplication.objects.create(
            organization=self.organization,
            name="Restricted App",
            allowed_scopes=["NovaCRM.modules.READ"],
        )

        self.client.force_authenticate(user=None)
        response = self.client.post('/api/v1/oauth/token/', {
            "grant_type": "authorization_code",
            "client_id": app.client_id,
            "client_secret": app.client_secret,
            "code": str(self.user.id),
            "scope": "NovaCRM.modules.WRITE",
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "invalid_scope")

