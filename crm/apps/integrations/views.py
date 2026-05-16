from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import IntegrationProvider, IntegrationLog
from .services import TalesTimelineSyncService
import json

@login_required(login_url='/login')
def integrations_dashboard(request):
    """
    Renders the integrations dashboard with real-time data.
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        # Fallback to user's default organization if middleware didn't catch it
        tenant = request.user.default_organization or request.user.memberships.first().organization

    providers = IntegrationProvider.objects.filter(tenant=tenant)
    
    # Calculate stats for each provider
    for p in providers:
        p.event_count = p.logs.count()
        p.last_event = p.logs.first()
    
    recent_logs = IntegrationLog.objects.filter(provider__tenant=tenant).select_related('provider').order_by('-created_at')[:10]
    
    return render(request, 'integrations.html', {
        'providers': providers,
        'recent_logs': recent_logs,
    })

class TalesTimelineWebhookView(APIView):
    """
    Endpoint for real-time sync from TalesTimeline.
    """
    permission_classes = [permissions.AllowAny] # Validation done via secret/API key

    def post(self, request, *args, **kwargs):
        # 1. Validate Secret / Find Tenant
        # For simplicity, we expect an X-Webhook-Secret header or a secret in the payload
        secret = request.headers.get('X-Webhook-Secret')
        if not secret:
            return Response({"error": "Missing secret"}, status=status.HTTP_401_UNAUTHORIZED)
        
        provider = IntegrationProvider.objects.filter(webhook_secret=secret, is_active=True).first()
        if not provider:
            return Response({"error": "Invalid secret"}, status=status.HTTP_401_UNAUTHORIZED)
        
        tenant = provider.tenant
        data = request.data
        event_type = data.get('event')

        # 2. Log the event
        log = IntegrationLog.objects.create(
            provider=provider,
            event_type=event_type or 'unknown',
            payload=data
        )

        # 3. Process the event
        service = TalesTimelineSyncService(tenant=tenant)
        success = False
        error_msg = None

        try:
            if event_type == 'order.completed':
                success = service.handle_order_completed(data.get('data', {}))
            elif event_type == 'contact.updated' or event_type == 'contact.created':
                success = service.handle_contact_updated(data.get('data', {}))
            else:
                error_msg = f"Unsupported event type: {event_type}"
        except Exception as e:
            success = False
            error_msg = str(e)

        if not success:
            log.status = 'failed'
            log.error_message = error_msg
            log.save()
            return Response({"status": "failed", "error": error_msg}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": "success"}, status=status.HTTP_200_OK)
