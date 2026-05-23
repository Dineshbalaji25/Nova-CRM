from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from apps.users.models import Organization
from apps.crm.models import Contact
from apps.audit.models import AuditLog
from apps.audit.middleware import AuditMiddleware
from apps.audit.utils import GDPRService

User = get_user_model()

class AuditAndGdprTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.org = Organization.objects.create(name="Audit Org", slug="audit-org")
        self.user = User.objects.create_user(email="audit@example.com", password="password")
        self.middleware = AuditMiddleware(get_response=lambda r: HttpResponse(status=200))

    def test_audit_middleware_creates_log(self):
        request = self.factory.post('/api/v1/crm/contacts/', data={'first_name': 'Test'}, content_type='application/json')
        request.user = self.user
        request.tenant_id = self.org.id
        
        response = HttpResponse(status=201)
        self.middleware.process_response(request, response)

        # Verify AuditLog created
        logs = AuditLog.objects.filter(tenant_id=self.org.id)
        self.assertEqual(logs.count(), 1)
        log = logs.first()
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.action, "create")
        self.assertIn("payload", log.changes)

    def test_gdpr_anonymization(self):
        contact = Contact.objects.create(
            tenant=self.org,
            first_name="John",
            last_name="Doe",
            email="john@doe.com",
            phone="12345"
        )
        
        # Create an audit log
        log = AuditLog.objects.create(
            tenant=self.org,
            actor=self.user,
            action="update",
            description="Updated contact Doe"
        )

        # Run GDPR scrub
        result = GDPRService.anonymize_tenant_data(self.org.id)
        self.assertTrue(result)

        # Verify contact anonymized
        contact.refresh_from_db()
        self.assertEqual(contact.first_name, "Anonymized")
        self.assertEqual(contact.last_name, "User")
        self.assertNotEqual(contact.email, "john@doe.com")
        self.assertEqual(contact.phone, "")

        # Verify log redacted
        log.refresh_from_db()
        self.assertEqual(log.description, "[REDACTED]")
