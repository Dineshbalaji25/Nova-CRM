from django.db import models
from django.conf import settings
from apps.core.models import TenantAwareModel, BaseModel

class Portal(TenantAwareModel):
    """
    Configuration for a specific portal (e.g., 'Customer Portal', 'Partner Portal').
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, help_text="Used in the portal URL (e.g., client-portal)")
    
    logo = models.FileField(upload_to='portals/logos/', null=True, blank=True)
    theme_color = models.CharField(max_length=7, default='#2563EB') # Hex code
    
    is_active = models.BooleanField(default=True)
    
    # Enabled Modules
    allow_deals = models.BooleanField(default=True)
    allow_invoices = models.BooleanField(default=True)
    allow_profile_edit = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

class PortalMember(BaseModel):
    """
    The link between a User (Identity) and a specific Portal + Contact.
    One User can be a portal member in multiple portals/tenants.
    """
    portal = models.ForeignKey(Portal, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portal_memberships')
    
    # The CRM record this user represents
    contact = models.ForeignKey('crm.Contact', on_delete=models.CASCADE, related_name='portal_access')
    
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('portal', 'user')
        indexes = [
            models.Index(fields=['user', 'portal']),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.portal.name}"
