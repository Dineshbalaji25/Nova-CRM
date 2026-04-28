from django.utils import timezone
from .models import Subscription, UsageRecord, FeatureEntitlement

class BillingService:
    
    @staticmethod
    def check_limit(tenant_id, feature_key, increment=0):
        """
        Checks if a tenant can perform an action based on their plan limits.
        Returns (Bool, Reason).
        """
        try:
            sub = Subscription.objects.select_related('plan').get(tenant_id=tenant_id)
        except Subscription.DoesNotExist:
            return False, "No Active Subscription"
            
        # 1. Check Status
        if sub.status not in ['active', 'trialing']:
            # Allow read-only?
            return False, f"Subscription is {sub.status}"
            
        # 2. Find Entitlement
        try:
            entitlement = sub.plan.entitlements.get(feature_key=feature_key)
        except FeatureEntitlement.DoesNotExist:
            # Default to Deny if not explicit? Or Allow?
            # Secure by default: Deny
            return False, "Feature not included in plan"
            
        # 3. Check Logic
        if entitlement.value_type == 'bool':
            return entitlement.limit_bool, "Feature disabled"
            
        if entitlement.value_type == 'int':
            # Check Usage
            # fetch current usage record
            now = timezone.now()
            # Simple month logic
            # In real app, align with billing period
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            usage, _ = UsageRecord.objects.get_or_create(
                tenant_id=tenant_id,
                metric=feature_key,
                period_start=start_of_month,
                defaults={'period_end': start_of_month} # Placeholder
            )
            
            if usage.count + increment > entitlement.limit_int:
                return False, f"Limit reached ({usage.count}/{entitlement.limit_int})"
                
            return True, "OK"
            
        return False, "Unknown limit type"

    @staticmethod
    def record_usage(tenant_id, metric, count=1):
        """
        Async helper to increment usage.
        """
        # Would typically be a Celery task
        # UsageRecord.objects.F('count') + count
        pass
