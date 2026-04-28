from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from apps.crm.models import Company
from apps.users.models import Organization
from django.contrib.auth import get_user_model

User = get_user_model()

class BasicSanityTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org", slug="test-org")
        self.user = User.objects.create_user(email="test@example.com", password="password")
        self.client = APIClient()
        
    def test_database_connection(self):
        """Verify that basic models can be created and queried."""
        Company.objects.create(name="Test Company", tenant=self.org)
        self.assertEqual(Company.objects.count(), 1)
        
    def test_api_client_initialization(self):
        """Verify that the API client is working and can reach an endpoint (even if restricted)."""
        response = self.client.get('/api/v1/crm/companies/')
        # Should be 401 because we haven't authenticated in this test yet
        self.assertEqual(response.status_code, 401)

    def test_model_fields_present(self):
        """Verify the new fields exist on the Company model."""
        company = Company.objects.create(
            name="Revenue Check", 
            tenant=self.org,
            industry="Tech",
            annual_revenue=1000000
        )
        self.assertEqual(company.industry, "Tech")
        self.assertEqual(company.annual_revenue, 1000000)
