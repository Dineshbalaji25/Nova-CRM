import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel, SoftDeleteModel

class Organization(SoftDeleteModel):
    """
    The Tenant entity. Represents a Company/Team.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, help_text="Unique identifier for subdomains or URL paths")
    
    # Billing info (Detailed billing in Phase 6)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'organizations'

    def __str__(self):
        return self.name

class UserManager(BaseUserManager):
    """Custom manager for Email-based User model."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser, BaseModel):
    """
    Global Identity. One User entity can likely access multiple Organizations.
    """
    username = None  # Remove username, use email
    email = models.EmailField(_('email address'), unique=True, db_index=True)
    
    # Profile fields
    full_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Global settings
    default_organization = models.ForeignKey(
        Organization, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="default_users"
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email

# -----------------------------------------------------------------------------
# Advanced Security (Roles & Profiles)
# -----------------------------------------------------------------------------

class Profile(BaseModel):
    """
    Field-Level Security & Module Access definitions.
    e.g. "Standard Profile" cannot delete Deals or view "Annual Revenue".
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='profiles')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # JSON definition of permissions
    # { "entities": { "crm.Deal": {"create": true, "read": true, "update": true, "delete": false} },
    #   "fields": { "crm.Deal.amount": "read_only" } }
    permissions = models.JSONField(default=dict)
    
    is_custom = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

class Role(BaseModel):
    """
    Data Hierarchy Security.
    e.g. "CEO" > "VP Sales" > "Sales Exec".
    Users can only see records owned by users below them in the hierarchy.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100)
    
    # Adjacency list for hierarchy (Manager -> Subordinates)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    
    # "Share data with peers" (Allows peer-to-peer visibility in same role)
    share_with_peers = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

class OrganizationMember(BaseModel):
    """
    The link between Users and Organizations (Many-to-Many).
    Stores Role-Based Access Control (RBAC) data.
    """
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Advanced Security Links
    rbac_role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    rbac_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'organization_members'
        unique_together = ('organization', 'user')
        indexes = [
            models.Index(fields=['user', 'organization']),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.organization.name}"

class APIKey(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=255, default='Default Key')
    key = models.CharField(max_length=64, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = f"sk_live_{uuid.uuid4().hex}{uuid.uuid4().hex}"[:64]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.organization.name})"
