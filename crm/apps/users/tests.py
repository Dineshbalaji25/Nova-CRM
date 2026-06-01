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
        from django.core.cache import cache
        cache.set(f"oauth_code_{self.user.id}", self.user.id, 600)
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


from apps.users.models import OAuthToken
from django.utils import timezone
from datetime import timedelta

class OAuthTokenAuthenticationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(name="OAuth Org", slug="oauth-org")
        self.user = User.objects.create_user(email="oauth-user@example.com", password="password123")
        OrganizationMember.objects.create(user=self.user, organization=self.organization, role='owner')
        
        self.app = OAuthApplication.objects.create(
            organization=self.organization,
            name="OAuth Client App",
            allowed_scopes=["NovaCRM.modules.READ"]
        )
        
        # Create a valid token
        self.token = OAuthToken.objects.create(
            application=self.app,
            user=self.user,
            access_token="at_valid1234567890",
            expires_at=timezone.now() + timedelta(hours=1),
            scopes="NovaCRM.modules.READ"
        )
        
        # Create an expired token
        self.expired_token = OAuthToken.objects.create(
            application=self.app,
            user=self.user,
            access_token="at_expired1234567890",
            expires_at=timezone.now() - timedelta(hours=1),
            scopes="NovaCRM.modules.READ"
        )

        # Create a revoked token
        self.revoked_token = OAuthToken.objects.create(
            application=self.app,
            user=self.user,
            access_token="at_revoked1234567890",
            expires_at=timezone.now() + timedelta(hours=1),
            is_revoked=True,
            scopes="NovaCRM.modules.READ"
        )

    def test_authenticated_with_valid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token.access_token}")
        response = self.client.get('/api/v1/crm/contacts/')
        # Should not get 401/403. Even if empty list, it should return 200 OK.
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_with_expired_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.expired_token.access_token}")
        response = self.client.get('/api/v1/crm/contacts/')
        self.assertEqual(response.status_code, 401)
        self.assertIn("expired", response.data["detail"].lower())

    def test_unauthorized_with_revoked_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.revoked_token.access_token}")
        response = self.client.get('/api/v1/crm/contacts/')
        self.assertEqual(response.status_code, 401)
        self.assertIn("invalid", response.data["detail"].lower())

    def test_unauthorized_with_non_existent_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer at_non_existent_token")
        response = self.client.get('/api/v1/crm/contacts/')
        self.assertEqual(response.status_code, 401)
        self.assertIn("invalid", response.data["detail"].lower())

    def test_jwt_fallback(self):
        # A Bearer token that doesn't start with at_ should NOT be intercepted by OAuthTokenAuthentication.
        # It will fall through to SimpleJWT and raise a JWT-specific error (or invalid token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer some_random_jwt_token")
        response = self.client.get('/api/v1/crm/contacts/')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "token_not_valid")


