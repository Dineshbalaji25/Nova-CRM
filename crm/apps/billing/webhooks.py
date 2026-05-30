import json
import stripe
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from .models import Subscription

@csrf_exempt
def stripe_webhook(request):
    """
    Handlers events from Stripe (invoice.paid, customer.subscription.updated)
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponseBadRequest()
    except stripe.error.SignatureVerificationError as e:
        return HttpResponseBadRequest()
    
    evt_type = event.get('type')
    data = event.get('data', {}).get('object', {})
    
    if evt_type == 'customer.subscription.updated':
        # Sync Status
        sub_id = data.get('id')
        status = data.get('status')
        current_period_end = data.get('current_period_end')
        
        try:
            sub = Subscription.objects.get(gateway_subscription_id=sub_id)
            sub.status = status
            if current_period_end:
                sub.current_period_end = timezone.datetime.fromtimestamp(current_period_end, tz=timezone.utc)
            sub.save()
        except Subscription.DoesNotExist:
            pass

    return HttpResponse(status=200)
