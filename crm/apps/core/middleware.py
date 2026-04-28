import threading
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

# Thread-local storage for current tenant
_thread_locals = threading.local()

def get_current_tenant():
    """Retrieve the current tenant from thread storage."""
    return getattr(_thread_locals, 'tenant', None)

def get_current_user():
    """Retrieve the current user from thread storage (optional helper)."""
    return getattr(_thread_locals, 'user', None)

class TenantContextMiddleware(MiddlewareMixin):
    """
    Middleware to resolve and set the current tenant based on headers.
    
    Resolution Strategy:
    1. X-Tenant-ID header (API / Mobile)
    2. Subdomain (Optional future implementation)
    """

    def process_request(self, request):
        _thread_locals.tenant = None
        _thread_locals.user = request.user
        
        # 1. Skip for public endpoints (like health checks or auth login)
        # For now, we just pass. Specific filtering happens in views permissions.
        
        # 2. Extract Header
        tenant_id = request.headers.get('X-Tenant-ID')
        
        if tenant_id:
            # We delay the DB lookup to the View layer authentication normally,
            # but for true isolation we might want to check existence here.
            # However, to avoid 'Apps not loaded' issues in early middleware,
            # we simply store the ID. The Permission classes will validate it against the User.
            request.tenant_id = tenant_id
            
            # Note: For Schema-based isolation (Phase 8 optimization), 
            # we would switch the Postgres SEARCH_PATH here.
            # For now (Phase 1), we just tag the request.
        else:
            request.tenant_id = None

    def process_response(self, request, response):
        # Clean up thread locals
        if hasattr(_thread_locals, 'tenant'):
            del _thread_locals.tenant
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
        return response
