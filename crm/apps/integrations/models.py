from django.db import models
from apps.core.models import TenantAwareModel, BaseModel

class IntegrationProvider(TenantAwareModel):
    """
    Configuration for an external integration (e.g. TalesTimeline).
    """
    PROVIDER_CHOICES = (
        ('tales_timeline', 'TalesTimeline'),
        ('zoho', 'Zoho CRM'),
        ('custom', 'Custom Webhook'),
    )
    
    name = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    is_active = models.BooleanField(default=True)
    
    # Secret used for validating incoming webhooks
    webhook_secret = models.CharField(max_length=255, blank=True)
    
    # Storage for credentials/tokens
    config_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.provider_type})"

class IntegrationLog(BaseModel):
    """
    Log of integration events (incoming or outgoing).
    """
    provider = models.ForeignKey(IntegrationProvider, on_delete=models.CASCADE, related_name='logs')
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    status = models.CharField(max_length=20, default='success')
    error_message = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.provider.name} - {self.event_type} ({self.status})"
