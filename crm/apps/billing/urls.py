from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import SubscriptionViewSet, BillingInvoiceViewSet, PlanViewSet, UsageRecordViewSet
from .webhooks import stripe_webhook

router = DefaultRouter()
router.register(r'plans', PlanViewSet)
router.register(r'my-subscription', SubscriptionViewSet)
router.register(r'invoices', BillingInvoiceViewSet)
router.register(r'usage', UsageRecordViewSet)

urlpatterns = [
    path('webhooks/stripe/', stripe_webhook, name='stripe_webhook'),
] + router.urls
