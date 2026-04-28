from celery import shared_task
from .services import WebhookDispatcher
from .models import WebhookEndpoint

@shared_task(bind=True, max_retries=5)
def send_webhook(self, endpoint_id, event_type, data, attempt=1):
    """
    Celery task with exponential backoff.
    """
    success = WebhookDispatcher.dispatch(endpoint_id, event_type, data, attempt)
    
    if not success:
        # Retry in 30s, 5m, 30m, 6h
        # 2^attempt * 30 roughly
        delay = 30 * (2 ** (attempt - 1))
        raise self.retry(countdown=delay, args=[endpoint_id, event_type, data, attempt + 1])

@shared_task
def broadcast_event(tenant_id, event_type, data):
    """
    Finds all matching endpoints for a tenant and queues delivery.
    """
    # 1. Broad match
    endpoints = WebhookEndpoint.objects.filter(tenant_id=tenant_id, status='active')
    
    for ep in endpoints:
        # Simple wildcard filter check (e.g. "deal.*" matches "deal.created")
        matched = False
        if '*' in ep.events:
            matched = True
        else:
            for pattern in ep.events:
                if pattern == event_type or (pattern.endswith('*') and event_type.startswith(pattern[:-1])):
                    matched = True
                    break
        
        if matched:
            send_webhook.delay(ep.id, event_type, data)
