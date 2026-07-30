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
    
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
    if not sig_header or not webhook_secret:
        return HttpResponseBadRequest("Missing Stripe signature or webhook secret")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except Exception as e:
        return HttpResponseBadRequest(f"Webhook error: {str(e)}")
    
    evt_type = event.get('type')
    data = event.get('data', {}).get('object', {})
    
    if evt_type == 'customer.subscription.updated':
        # Sync Status
        sub_id = data.get('id')
        new_status = data.get('status')
        current_period_end = data.get('current_period_end')

        try:
            sub = Subscription.objects.get(gateway_subscription_id=sub_id)
            sub.status = new_status
            if current_period_end:
                sub.current_period_end = timezone.datetime.fromtimestamp(
                    current_period_end, tz=timezone.utc
                )
            sub.save()
        except Subscription.DoesNotExist:
            pass

    elif evt_type == 'invoice.paid':
        # Reactivate subscription when a previously failed invoice is now paid
        sub_id = data.get('subscription')
        if sub_id:
            Subscription.objects.filter(
                gateway_subscription_id=sub_id
            ).update(status='active')

    elif evt_type == 'invoice.payment_failed':
        # Mark subscription as past_due when payment collection fails
        sub_id = data.get('subscription')
        if sub_id:
            Subscription.objects.filter(
                gateway_subscription_id=sub_id
            ).update(status='past_due')

    return HttpResponse(status=200)
