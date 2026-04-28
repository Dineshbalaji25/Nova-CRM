from rest_framework import viewsets, permissions
from apps.crm.views import BaseTenantViewSet
from .models import AuditLog
from .serializers import AuditLogSerializer

class AuditLogViewSet(BaseTenantViewSet):
    """
    Read-only view for Tenant Admins to see activity.
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    http_method_names = ['get']
    
    # Permission: User needs 'admin' role (check is done in permission class logic usually)
    # Using default BaseTenantViewSet logic for Multi-tenancy
