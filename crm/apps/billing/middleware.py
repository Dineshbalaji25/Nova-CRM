from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import Subscription

class FeatureEnforcementMiddleware(MiddlewareMixin):
    """
    Blocks access if subscription is unpaid or expired.
    Also injects 'subscription' into the request for views to check limits.
    """
    
    def process_request(self, request):
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return
            
        # Optimization: Fetch from cache in real prod
        try:
            sub = Subscription.objects.select_related('plan').get(tenant_id=tenant_id)
            request.subscription = sub
            
            # Check for hard lock (Post-dunning)
            if sub.status in ['unpaid', 'canceled']:
                if not request.path.startswith('/api/v1/billing/'):
                    from django.http import JsonResponse
                    return JsonResponse({"error": "Payment required. Subscription unpaid or canceled."}, status=402)
                
        except Subscription.DoesNotExist:
            request.subscription = None
            # Allow access? Or redirect to onboarding?
            pass
