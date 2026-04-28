from rest_framework import serializers
from .models import Plan, Subscription, BillingInvoice, UsageRecord

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ('id', 'name', 'amount_cents', 'interval', 'currency')

class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    
    class Meta:
        model = Subscription
        fields = ('id', 'status', 'current_period_end', 'plan', 'plan_name', 'cancel_at_period_end')

class BillingInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingInvoice
        fields = '__all__'

class UsageRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageRecord
        fields = '__all__'
