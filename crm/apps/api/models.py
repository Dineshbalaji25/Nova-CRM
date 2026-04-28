import secrets
from django.db import models
from apps.core.models import TenantAwareModel, BaseModel

class WebhookEndpoint(TenantAwareModel):
    """
    A User-registered URL that wants to receive events.
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('disabled', 'Disabled'), # Manually disabled
        ('failing', 'Failing'),   # Automatically disabled after too many failures
    )
    
    url = models.URLField()
    description = models.CharField(max_length=255, blank=True)
    
    # Secret used for HMAC signature verification
    secret = models.CharField(max_length=64, editable=False)
    
    # Event filters (e.g. ['contact.created', 'deal.*'])
    events = models.JSONField(default=list)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    failure_count = models.PositiveIntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if not self.secret:
            self.secret = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.url} ({self.status})"

class WebhookEventLog(BaseModel):
    """
    Immutable log of a webhook delivery attempt.
    """
    endpoint = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE, related_name='logs')
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    
    response_status = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    
    attempt = models.PositiveIntegerField(default=1)
    is_success = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
