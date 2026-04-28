from rest_framework.throttling import UserRateLimit

class TenantRateLimit(UserRateLimit):
    """
    Limits API requests based on Tenant Tier.
    """
    def allow_request(self, request, view):
        # In a real app, this would read from the Organization.plan.limit
        # For MVP, we hardcode.
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return True # Or strict fallback
            
        self.rate = '1000/hour' # Default
        return super().allow_request(request, view)
