from rest_framework import serializers
from .models import Product, PriceBook, PriceBookEntry, Quote, QuoteLineItem, SalesOrder, Invoice
from apps.crm.serializers import CompanySerializer, ContactSerializer, DealSerializer
from apps.users.serializers import UserSerializer

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('tenant',)

class PriceBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceBook
        fields = '__all__'
        read_only_fields = ('tenant',)

class PriceBookEntrySerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = PriceBookEntry
        fields = '__all__'
        read_only_fields = ('tenant',)

class QuoteLineItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = QuoteLineItem
        fields = '__all__'

class QuoteSerializer(serializers.ModelSerializer):
    line_items = QuoteLineItemSerializer(many=True, read_only=True)
    company_details = CompanySerializer(source='company', read_only=True)
    deal_details = DealSerializer(source='deal', read_only=True)
    
    class Meta:
        model = Quote
        fields = '__all__'
        read_only_fields = ('tenant',)

class SalesOrderSerializer(serializers.ModelSerializer):
    company_details = CompanySerializer(source='company', read_only=True)
    quote_details = QuoteSerializer(source='quote', read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = '__all__'
        read_only_fields = ('tenant',)

class InvoiceSerializer(serializers.ModelSerializer):
    company_details = CompanySerializer(source='company', read_only=True)
    sales_order_details = SalesOrderSerializer(source='sales_order', read_only=True)
    
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ('tenant',)
