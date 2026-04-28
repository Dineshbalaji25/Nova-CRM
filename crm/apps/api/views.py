from rest_framework import viewsets, permissions
from apps.users.permissions import IsOrganizationMember
from apps.crm.views import BaseTenantViewSet
from .models import WebhookEndpoint, WebhookEventLog
from .serializers import WebhookEndpointSerializer, WebhookEventLogSerializer

class WebhookEndpointViewSet(BaseTenantViewSet):
    queryset = WebhookEndpoint.objects.all()
    serializer_class = WebhookEndpointSerializer

class WebhookLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only view for webhook logs. 
    Only shows logs for endpoints belonging to the user's tenant.
    """
    queryset = WebhookEventLog.objects.all()
    serializer_class = WebhookEventLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]
    
    def get_queryset(self):
        # Filter logs belonging to the tenant's valid endpoints
        return self.queryset.filter(endpoint__tenant_id=self.request.tenant_id)
