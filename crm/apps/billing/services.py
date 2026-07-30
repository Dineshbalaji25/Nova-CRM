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
        Atomically increments usage counter for a metric in the current billing period.
        Uses F() expressions to avoid race conditions.
        """
        from django.db.models import F
        from datetime import timedelta

        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Calculate end of month
        if now.month == 12:
            end_of_month = start_of_month.replace(year=now.year + 1, month=1)
        else:
            end_of_month = start_of_month.replace(month=now.month + 1)

        # Try atomic increment first
        updated = UsageRecord.objects.filter(
            tenant_id=tenant_id,
            metric=metric,
            period_start=start_of_month,
        ).update(count=F('count') + count)

        if not updated:
            # Record doesn't exist yet — create it
            UsageRecord.objects.get_or_create(
                tenant_id=tenant_id,
                metric=metric,
                period_start=start_of_month,
                defaults={
                    'count': count,
                    'period_end': end_of_month,
                }
            )
