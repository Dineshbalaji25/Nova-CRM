from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, PriceBookViewSet, QuoteViewSet, 
    SalesOrderViewSet, InvoiceViewSet
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'price-books', PriceBookViewSet, basename='pricebook')
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'sales-orders', SalesOrderViewSet, basename='salesorder')
router.register(r'invoices', InvoiceViewSet, basename='invoice')

app_name = 'sales'

urlpatterns = [
    path('', include(router.urls)),
]
