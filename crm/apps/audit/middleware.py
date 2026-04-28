import json
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .models import AuditLog

class AuditMiddleware(MiddlewareMixin):
    """
    Automatic auditing of write operations (POST, PUT, PATCH, DELETE).
    """
    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
    
    def process_response(self, request, response):
        if request.method in self.SAFE_METHODS:
            return response
            
        if not request.user.is_authenticated:
            return response
            
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return response
            
        # Determine Status
        if 200 <= response.status_code < 300:
            
            # Simple heuristic to determine action & target
            # Real implementation would hook into Signals or Serializers for granular diffs
            # Here we capture the high-level intent.
            
            try:
                url_name = resolve(request.path_info).url_name
            except:
                url_name = "unknown"
                
            action_map = {
                'POST': 'create',
                'PUT': 'update',
                'PATCH': 'update',
                'DELETE': 'delete'
            }
            action = action_map.get(request.method, 'unknown')
            
            # We assume response data might contain the ID
            obj_id = None
            description = f"Request to {request.path}"
            
            changes = {}
            if request.method in ('POST', 'PUT', 'PATCH'):
                # Very naive sensitive data masking
                try:
                    payload = json.loads(request.body) if request.body else {}
                    cleaned_changes = {k: v for k, v in payload.items() if 'password' not in k}
                    changes = {'payload': cleaned_changes}
                except:
                    pass

            AuditLog.objects.create(
                tenant_id=tenant_id,
                actor=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                action=action,
                description=description,
                changes=changes,
                # Content Type linking requires more complex logic to resolve view -> model
            )
            
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
