from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from apps.core.middleware import TenantContextMiddleware
from apps.users.models import Organization
from apps.crm.models import Company

User = get_user_model()

class CoreMiddlewareAndModelTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.org = Organization.objects.create(name="Test Org 1", slug="test-org-1")
        self.user = User.objects.create_user(email="testuser@example.com", password="password")
        self.middleware = TenantContextMiddleware(get_response=lambda r: r)

    def test_tenant_context_middleware_with_header(self):
        request = self.factory.get('/api/v1/crm/companies/', HTTP_X_TENANT_ID=str(self.org.id))
        request.user = self.user
        self.middleware(request)
        self.assertEqual(request.tenant_id, str(self.org.id))

    def test_tenant_context_middleware_without_header(self):
        request = self.factory.get('/api/v1/crm/companies/')
        request.user = self.user
        self.middleware(request)
        self.assertIsNone(request.tenant_id)

    def test_soft_delete_model_behavior(self):
        company = Company.objects.create(name="Soft Delete Co", tenant=self.org)
        company_id = company.id
        
        # Soft delete the company
        company.delete()
        
        # Reload from DB
        company.refresh_from_db()
        self.assertTrue(company.is_deleted)
        self.assertIsNotNone(company.deleted_at)
        
        # Verify it can still be fetched directly, but is soft-deleted
        self.assertEqual(Company.objects.filter(id=company_id).count(), 1)
        
        # Hard delete
        company.hard_delete()
        self.assertEqual(Company.objects.filter(id=company_id).count(), 0)
