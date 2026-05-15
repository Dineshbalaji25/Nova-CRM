import uuid
from django.db import models
from django.utils import timezone

class BaseModel(models.Model):
    """
    Abstract base model with UUID primary key and timestamping.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

class SoftDeleteModel(BaseModel):
    """
    Abstract model adding soft-delete functionality.
    """
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)

    def hard_delete(self):
        super().delete()

class TenantAwareModel(SoftDeleteModel):
    """
    Abstract model ensuring data is linked to a specific tenant (Organization).
    The tenant_id is stored directly to avoid join overhead on simple checks.
    """
    # Using specific string reference to avoid circular imports.
    # We assume 'users.Organization' will be the model.
    tenant = models.ForeignKey(
        'users.Organization', 
        on_delete=models.CASCADE, 
        related_name="%(app_label)s_%(class)s_set",
        db_index=True
    )

    class Meta:
        abstract = True
