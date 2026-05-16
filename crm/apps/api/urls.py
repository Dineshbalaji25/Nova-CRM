from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import WebhookEndpointViewSet, WebhookLogViewSet

router = DefaultRouter()
router.register(r'webhook-endpoints', WebhookEndpointViewSet, basename='webhook-endpoint')
router.register(r'webhook-logs', WebhookLogViewSet, basename='webhook-log')

urlpatterns = [
    path('', include('apps.users.urls')),
    path('crm/', include('apps.crm.urls')),
    path('workflows/', include('apps.workflows.urls')),
    path('billing/', include('apps.billing.urls')),
    path('audit/', include('apps.audit.urls')),
    path('sales/', include('apps.sales.urls')),
    path('marketing/', include('apps.marketing.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('stats/', include('apps.analytics.stats_urls')),
    path('omnichannel/', include('apps.omnichannel.urls')),
    path('portal/', include('apps.portals.urls')),
    path('integrations/', include('apps.integrations.urls')),
    path('', include(router.urls)),
]
