from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PhoneIntegrationViewSet, CallLogViewSet, 
    EmailIntegrationViewSet, EmailMessageViewSet,
    UnifiedTimelineView
)

router = DefaultRouter()
router.register(r'phone-integrations', PhoneIntegrationViewSet, basename='phoneintegration')
router.register(r'call-logs', CallLogViewSet, basename='calllog')
router.register(r'email-integrations', EmailIntegrationViewSet, basename='emailintegration')
router.register(r'email-messages', EmailMessageViewSet, basename='emailmessage')

app_name = 'omnichannel'

urlpatterns = [
    path('timeline/<str:model_name>/<uuid:record_id>/', UnifiedTimelineView.as_view(), name='timeline'),
    path('', include(router.urls)),
]
