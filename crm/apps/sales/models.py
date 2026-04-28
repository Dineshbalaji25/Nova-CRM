from django.db import models
from django.conf import settings
from apps.core.models import TenantAwareModel, BaseModel
from apps.crm.models import Deal, Contact, Company

# -----------------------------------------------------------------------------
# Products & Price Books
# -----------------------------------------------------------------------------

class Product(TenantAwareModel):
    """
    Items or services sold by the organization.
    """
    name = models.CharField(max_length=255)
    product_code = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Inventory Tracking
    qty_in_stock = models.IntegerField(default=0)
    qty_in_demand = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='products')

    def __str__(self):
        return f"{self.product_code} - {self.name}" if self.product_code else self.name


class PriceBook(TenantAwareModel):
    """
    Multiple pricing tiers (e.g., 'Retail', 'Wholesale', 'Partner').
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class PriceBookEntry(TenantAwareModel):
    """
    Maps a Product to a Price Book with a specific price.
    """
    price_book = models.ForeignKey(PriceBook, on_delete=models.CASCADE, related_name='entries')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_book_entries')
    list_price = models.DecimalField(max_digits=14, decimal_places=2)
    
    class Meta:
        unique_together = ('price_book', 'product')

    def __str__(self):
        return f"{self.product.name} @ {self.list_price}"


# -----------------------------------------------------------------------------
# Quotes
# -----------------------------------------------------------------------------

class Quote(TenantAwareModel):
    """
    Proposed price for products/services given to a potential customer.
    """
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('negotiation', 'Negotiation'),
        ('delivered', 'Delivered'),
        ('on_hold', 'On Hold'),
        ('confirmed', 'Confirmed'),
        ('closed_won', 'Closed Won'),
        ('closed_lost', 'Closed Lost'),
    )

    subject = models.CharField(max_length=255)
    quote_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotes')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='quotes')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotes')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    valid_until = models.DateField(null=True, blank=True)
    
    # Financials (Calculated fields)
    sub_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    terms_and_conditions = models.TextField(blank=True)
    
    def __str__(self):
        return self.subject


class QuoteLineItem(BaseModel):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='line_items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    description = models.CharField(max_length=255, blank=True)
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    list_price = models.DecimalField(max_digits=14, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Calculated per line
    total = models.DecimalField(max_digits=14, decimal_places=2)


# -----------------------------------------------------------------------------
# Sales Orders & Invoices
# -----------------------------------------------------------------------------

class SalesOrder(TenantAwareModel):
    """
    Confirmed order from customer.
    """
    STATUS_CHOICES = (
        ('created', 'Created'),
        ('approved', 'Approved'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    subject = models.CharField(max_length=255)
    so_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    
    quote = models.ForeignKey(Quote, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders')
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    sub_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)


class Invoice(TenantAwareModel):
    """
    Bill issued to the customer.
    """
    STATUS_CHOICES = (
        ('created', 'Created'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('void', 'Void'),
    )

    subject = models.CharField(max_length=255)
    invoice_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    invoice_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    
    sub_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=14, decimal_places=2, default=0)
