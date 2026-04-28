from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WebhookEndpointViewSet, WebhookLogViewSet

# Create a router for the base API app (webhooks)
router = DefaultRouter()
router.register(r'webhooks', WebhookEndpointViewSet)
router.register(r'webhook-logs', WebhookLogViewSet, basename='webhook-logs')

urlpatterns = [
    # Include other apps' URLs with prefixes
    path('', include('apps.users.urls')),
    path('crm/', include('apps.crm.urls')),
    path('billing/', include('apps.billing.urls')),
    path('workflows/', include('apps.workflows.urls')),
    path('audit/', include('apps.audit.urls')),
    path('sales/', include('apps.sales.urls')),
    path('marketing/', include('apps.marketing.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('omnichannel/', include('apps.omnichannel.urls')),
    path('portal/', include('apps.portals.urls')),
    
    # Base API routes (webhooks)
    path('', include(router.urls)),
]
