from django.db import models
from apps.core.models import BaseModel, TenantAwareModel

class Plan(BaseModel):
    """
    SaaS Pricing Plan.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    gateway_price_id = models.CharField(max_length=100, blank=True, help_text="Stripe Price ID")
    
    amount_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default='USD')
    interval = models.CharField(max_length=20, choices=(('month', 'Month'), ('year', 'Year')), default='month')
    
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.interval})"

class FeatureEntitlement(BaseModel):
    """
    What does this plan allow?
    """
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='entitlements')
    feature_key = models.CharField(max_length=100, db_index=True)
    
    # Value type
    value_type = models.CharField(max_length=20, choices=(('bool', 'Boolean'), ('int', 'Integer')), default='bool')
    
    # Actual limit (e.g. 5000 leads or True)
    limit_int = models.IntegerField(null=True, blank=True)
    limit_bool = models.BooleanField(null=True, blank=True)
    
    class Meta:
        unique_together = ('plan', 'feature_key')

class Subscription(BaseModel):
    """
    Tenant's active subscription.
    """
    STATUS_CHOICES = (
        ('trialing', 'Trialing'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('unpaid', 'Unpaid'),
    )

    # Link to Tenant (Organization)
    # We use a constrained ForeignKey to Organization
    tenant = models.OneToOneField('users.Organization', on_delete=models.CASCADE, related_name='subscription')
    
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, null=True)
    
    gateway_subscription_id = models.CharField(max_length=100, unique=True, blank=True)
    gateway_customer_id = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trialing')
    
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True, db_index=True)
    cancel_at_period_end = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.tenant} - {self.plan} ({self.status})"

class UsageRecord(TenantAwareModel):
    """
    Metered usage tracking (e.g., email_sent).
    """
    metric = models.CharField(max_length=100, db_index=True)
    count = models.PositiveIntegerField(default=0)
    
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    class Meta:
        unique_together = ('tenant', 'metric', 'period_start')

class BillingInvoice(TenantAwareModel):
    """
    Payment history for the subscription.
    """
    gateway_invoice_id = models.CharField(max_length=100, unique=True)
    amount_paid_cents = models.PositiveIntegerField()
    status = models.CharField(max_length=20) # paid, open, void, uncollectible
    invoice_pdf = models.URLField(blank=True)
    paid_at = models.DateTimeField(null=True)
