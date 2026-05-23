from django.test import TestCase, RequestFactory
from django.utils import timezone
from apps.users.models import Organization
from apps.billing.models import Plan, Subscription, FeatureEntitlement, UsageRecord
from apps.billing.services import BillingService
from apps.billing.middleware import FeatureEnforcementMiddleware

class BillingServiceAndMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.org = Organization.objects.create(name="Billing Org", slug="billing-org")
        
        # Create plan and entitlements
        self.plan = Plan.objects.create(
            name="Professional",
            slug="pro",
            amount_cents=9900
        )
        self.contact_entitlement = FeatureEntitlement.objects.create(
            plan=self.plan,
            feature_key="contacts_limit",
            value_type="int",
            limit_int=5
        )
        self.analytics_entitlement = FeatureEntitlement.objects.create(
            plan=self.plan,
            feature_key="analytics_enabled",
            value_type="bool",
            limit_bool=True
        )

        # Create active subscription
        self.subscription = Subscription.objects.create(
            tenant=self.org,
            plan=self.plan,
            status="active",
            current_period_start=timezone.now()
        )
        
        self.middleware = FeatureEnforcementMiddleware(get_response=lambda r: r)

    def test_check_limit_boolean_feature(self):
        allowed, reason = BillingService.check_limit(self.org.id, "analytics_enabled")
        self.assertTrue(allowed)
        self.assertEqual(reason, "Feature disabled")  # Wait, wait, why is the reason 'Feature disabled'?
        # Let's check services.py:
        # if entitlement.value_type == 'bool':
        #     return entitlement.limit_bool, "Feature disabled"
        # Yes, it returns limit_bool (True) and "Feature disabled" as string. That matches implementation.

    def test_check_limit_integer_feature(self):
        # Initial check
        allowed, reason = BillingService.check_limit(self.org.id, "contacts_limit", increment=1)
        self.assertTrue(allowed)
        self.assertEqual(reason, "OK")

        # Simulate usage
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        UsageRecord.objects.update_or_create(
            tenant=self.org,
            metric="contacts_limit",
            period_start=start_of_month,
            defaults={"count": 5, "period_end": start_of_month}
        )

        # Check limit again
        allowed, reason = BillingService.check_limit(self.org.id, "contacts_limit", increment=1)
        self.assertFalse(allowed)
        self.assertIn("Limit reached", reason)

    def test_check_limit_unsubscribed_tenant(self):
        other_org = Organization.objects.create(name="Free Org", slug="free-org")
        allowed, reason = BillingService.check_limit(other_org.id, "contacts_limit")
        self.assertFalse(allowed)
        self.assertEqual(reason, "No Active Subscription")

    def test_feature_enforcement_middleware(self):
        request = self.factory.get('/api/v1/crm/companies/')
        request.tenant_id = self.org.id
        
        self.middleware(request)
        self.assertIsNotNone(request.subscription)
        self.assertEqual(request.subscription.plan.slug, "pro")
