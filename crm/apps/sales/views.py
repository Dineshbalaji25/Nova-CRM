from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, PriceBook, Quote, SalesOrder, Invoice
from .serializers import (
    ProductSerializer, PriceBookSerializer, QuoteSerializer, 
    SalesOrderSerializer, InvoiceSerializer
)
from apps.crm.views import BaseTenantViewSet

class BaseSalesViewSet(BaseTenantViewSet):
    pass

class ProductViewSet(BaseSalesViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    search_fields = ['name', 'product_code']
    ordering_fields = ['name', 'unit_price', 'created_at']

class PriceBookViewSet(BaseSalesViewSet):
    queryset = PriceBook.objects.all()
    serializer_class = PriceBookSerializer
    search_fields = ['name']
    
class QuoteViewSet(BaseSalesViewSet):
    queryset = Quote.objects.select_related('company', 'deal').prefetch_related('line_items').all()
    serializer_class = QuoteSerializer
    search_fields = ['subject', 'quote_number', 'company__name']
    ordering_fields = ['created_at', 'valid_until', 'grand_total']

class SalesOrderViewSet(BaseSalesViewSet):
    queryset = SalesOrder.objects.select_related('company', 'quote').all()
    serializer_class = SalesOrderSerializer
    search_fields = ['subject', 'so_number', 'company__name']

class InvoiceViewSet(BaseSalesViewSet):
    queryset = Invoice.objects.select_related('company', 'sales_order').all()
    serializer_class = InvoiceSerializer
    search_fields = ['subject', 'invoice_number', 'company__name']
