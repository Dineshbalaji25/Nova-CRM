from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Portal, PortalMember
from .serializers import PortalSerializer, PortalMemberSerializer
from .permissions import IsPortalUser, PortalFilterMixin
from apps.crm.views import BaseTenantViewSet, DealViewSet
from apps.billing.models import Invoice
from apps.billing.serializers import InvoiceSerializer # Assuming this exists or will be created

class PortalViewSet(BaseTenantViewSet):
    queryset = Portal.objects.all()
    serializer_class = PortalSerializer

class PortalUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for portal users to see their own profile and related data.
    """
    permission_classes = [permissions.IsAuthenticated, IsPortalUser]
    serializer_class = PortalMemberSerializer

    def get_queryset(self):
        return PortalMember.objects.filter(
            user=self.request.user,
            portal__tenant_id=self.request.tenant_id,
            is_active=True
        )

    @action(detail=False, methods=['get'])
    def profile(self, request):
        member = self.get_queryset().first()
        if not member:
            return Response({"error": "Portal profile not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(member)
        return Response(serializer.data)

class PortalDataViewSet(PortalFilterMixin, viewsets.ReadOnlyModelViewSet):
    """
    Generic ViewSet for Portal users to access CRM data securely.
    """
    permission_classes = [permissions.IsAuthenticated, IsPortalUser]
    
    # We will use this ViewSet for multiple models by dynamically setting queryset/serializer
    pass

# Specialized Portal ViewSets
class PortalDealViewSet(PortalFilterMixin, viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsPortalUser]
    from apps.crm.models import Deal
    from apps.crm.serializers import DealSerializer
    queryset = Deal.objects.all()
    serializer_class = DealSerializer

class PortalInvoiceViewSet(PortalFilterMixin, viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsPortalUser]
    queryset = Invoice.objects.all()
    # Need to verify if InvoiceSerializer exists
    from apps.billing.serializers import InvoiceSerializer
    serializer_class = InvoiceSerializer
