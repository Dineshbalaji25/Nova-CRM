from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import PhoneIntegration, CallLog, EmailIntegration, EmailMessage, SupportChatMessage
from .serializers import (
    PhoneIntegrationSerializer, CallLogSerializer, 
    EmailIntegrationSerializer, EmailMessageSerializer,
    SupportChatMessageSerializer
)
from apps.crm.views import BaseTenantViewSet
from .services import EmailProcessor, OmnichannelService
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

class PhoneIntegrationViewSet(BaseTenantViewSet):
    queryset = PhoneIntegration.objects.all()
    serializer_class = PhoneIntegrationSerializer

class CallLogViewSet(BaseTenantViewSet):
    queryset = CallLog.objects.select_related('integration', 'user', 'lead', 'contact').all()
    serializer_class = CallLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['direction', 'status', 'user', 'lead', 'contact']
    search_fields = ['from_number', 'to_number']

class EmailIntegrationViewSet(BaseTenantViewSet):
    queryset = EmailIntegration.objects.all()
    serializer_class = EmailIntegrationSerializer

class EmailMessageViewSet(BaseTenantViewSet):
    queryset = EmailMessage.objects.select_related('integration', 'lead', 'contact', 'deal').all()
    serializer_class = EmailMessageSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_read', 'lead', 'contact', 'deal']
    search_fields = ['subject', 'from_address', 'to_addresses']

    @action(detail=False, methods=['post'], url_path='simulate-receive')
    def simulate_receive(self, request):
        """
        Helper to simulate an incoming email for testing parsing logic.
        """
        integration_id = request.data.get('integration_id')
        if not integration_id:
            return Response({"error": "integration_id is required"}, status=400)
            
        try:
            integration = EmailIntegration.objects.get(id=integration_id, tenant_id=request.tenant_id)
            
            email = EmailMessage.objects.create(
                integration=integration,
                tenant_id=request.tenant_id,
                message_id=f"sim_{request.user.id}_{integration.id}",
                subject=request.data.get('subject', 'New Inquiry'),
                body_text=request.data.get('body', 'I am interested in your products.'),
                from_address=request.data.get('from_address', 'prospect@example.com'),
                to_addresses=integration.email_address,
                sent_at=request.data.get('sent_at', '2026-04-27T10:00:00Z')
            )
            
            # Trigger parsing
            EmailProcessor.process_incoming(email)
            
            return Response({
                "message": "Email received and processed",
                "email_id": email.id,
                "linked_lead": email.lead_id,
                "linked_contact": email.contact_id
            })
        except EmailIntegration.DoesNotExist:
            return Response({"error": "Integration not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class UnifiedTimelineView(APIView):
    """
    Returns a consolidated timeline of all communications for a record.
    """
    def get(self, request, model_name, record_id):
        if model_name not in ['lead', 'contact', 'deal']:
            return Response({"error": "Invalid model"}, status=400)
            
        try:
            timeline = OmnichannelService.get_timeline(request.tenant_id, model_name, record_id)
            return Response(timeline)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class SupportChatMessageViewSet(BaseTenantViewSet):
    queryset = SupportChatMessage.objects.all()
    serializer_class = SupportChatMessageSerializer

    def get_queryset(self):
        # Only fetch user's messages for the current tenant
        return self.queryset.filter(tenant_id=self.request.tenant_id, user=self.request.user).order_by('created_at')

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id, user=self.request.user, is_from_support=False)
