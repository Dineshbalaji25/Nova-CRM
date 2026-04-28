from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PortalViewSet, PortalUserViewSet, PortalDealViewSet, PortalBillingInvoiceViewSet
)

router = DefaultRouter()
router.register(r'admin', PortalViewSet, basename='portal-admin')
router.register(r'user', PortalUserViewSet, basename='portal-user')
router.register(r'deals', PortalDealViewSet, basename='portal-deals')
router.register(r'invoices', PortalBillingInvoiceViewSet, basename='portal-invoices')

app_name = 'portals'

urlpatterns = [
    path('', include(router.urls)),
]
