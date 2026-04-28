from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.core.models import BaseModel, TenantAwareModel

class AuditLog(TenantAwareModel):
    """
    Immutable security log of WHO did WHAT to WHICH object.
    TRUTH SOURCE for compliance.
    """
    ACTION_CHOICES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('view', 'View'), # Use sparingly for high-sensitivity data
    )
    
    actor = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    # Target Object (Polymorphic)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    object_id = models.UUIDField(null=True) # Assuming UUIDs for all models
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # What changed?
    # Format: {"field_name": {"old": "A", "new": "B"}}
    changes = models.JSONField(default=dict, blank=True)
    
    description = models.TextField(blank=True) # Human readable summary

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'actor', 'action']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.created_at} - {self.actor} - {self.action}"
