from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TalesTimelineWebhookView
from apps.crm.views import (
    ContactViewSet, DealViewSet, CompanyViewSet, LeadViewSet, ActivityViewSet
)

# Zoho-like router
zoho_router = DefaultRouter(trailing_slash=False)
zoho_router.register(r'Contacts', ContactViewSet, basename='zoho-contacts')
zoho_router.register(r'Deals', DealViewSet, basename='zoho-deals')
zoho_router.register(r'Accounts', CompanyViewSet, basename='zoho-accounts')
zoho_router.register(r'Leads', LeadViewSet, basename='zoho-leads')
zoho_router.register(r'Tasks', ActivityViewSet, basename='zoho-tasks')

urlpatterns = [
    path('tales-timeline/webhook/', TalesTimelineWebhookView.as_view(), name='tales_timeline_webhook'),
    
    # Zoho CRM v8 style API
    path('zoho/v8/', include(zoho_router.urls)),
]
