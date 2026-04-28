from django.db import models
from django.conf import settings
from apps.core.models import TenantAwareModel, BaseModel
from apps.crm.models import Lead, Contact

# -----------------------------------------------------------------------------
# Campaign Management
# -----------------------------------------------------------------------------

class Campaign(TenantAwareModel):
    STATUS_CHOICES = (
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    expected_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    budgeted_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='campaigns')

    def __str__(self):
        return self.name

class CampaignMember(TenantAwareModel):
    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('responded', 'Responded'),
        ('bounced', 'Bounced'),
        ('opted_out', 'Opted Out'),
    )
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='members')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='campaigns')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='campaigns')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')

# -----------------------------------------------------------------------------
# Web Forms (Web-to-Lead, Web-to-Contact)
# -----------------------------------------------------------------------------

class WebForm(TenantAwareModel):
    """
    Form definition for generating leads/contacts.
    """
    TARGET_CHOICES = (
        ('lead', 'Lead'),
        ('contact', 'Contact'),
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    target_model = models.CharField(max_length=20, choices=TARGET_CHOICES, default='lead')
    return_url = models.URLField(blank=True, help_text="Redirect URL after submission")
    
    assign_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    embed_code = models.TextField(blank=True)

    def __str__(self):
        return self.name

class WebFormField(BaseModel):
    webform = models.ForeignKey(WebForm, on_delete=models.CASCADE, related_name='fields')
    field_name = models.CharField(max_length=100) # Mapping to fields like first_name, email, etc.
    label = models.CharField(max_length=100)
    is_required = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['position']
