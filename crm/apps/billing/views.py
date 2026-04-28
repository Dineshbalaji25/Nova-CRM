from rest_framework import viewsets, permissions
from apps.crm.views import BaseTenantViewSet
from .models import Subscription, Invoice, Plan, UsageRecord
from .serializers import SubscriptionSerializer, InvoiceSerializer, PlanSerializer, UsageRecordSerializer

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.filter(is_public=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticated]

class UsageRecordViewSet(BaseTenantViewSet):
    queryset = UsageRecord.objects.all()
    serializer_class = UsageRecordSerializer
    http_method_names = ['get']

class SubscriptionViewSet(BaseTenantViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

class InvoiceViewSet(BaseTenantViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
