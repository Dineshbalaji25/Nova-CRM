from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from apps.core.models import TenantAwareModel, BaseModel

# -----------------------------------------------------------------------------
# Metadata Models (Pipelines, Stages, Tags, Custom Fields)
# -----------------------------------------------------------------------------

class Pipeline(TenantAwareModel):
    """
    Sales Pipeline (e.g., 'B2B Sales', 'Partnership').
    """
    name = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Stage(TenantAwareModel):
    """
    Stages within a Pipeline (e.g., 'New', 'Negotiation', 'Won').
    """
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='stages')
    name = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default=0, db_index=True)
    win_probability = models.PositiveIntegerField(default=0, help_text="0-100%")

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.pipeline.name} - {self.name}"

class Tag(TenantAwareModel):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#FFFFFF")  # Hex code

    class Meta:
        unique_together = ('tenant', 'name')

class CustomFieldDefinition(TenantAwareModel):
    """
    Defines the schema for dynamic fields.
    """
    MODEL_CHOICES = (
        ('contact', 'Contact'),
        ('company', 'Company'),
        ('deal', 'Deal'),
    )
    TYPE_CHOICES = (
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('boolean', 'Boolean'),
        ('select', 'Select'),
    )
    
    target_model = models.CharField(max_length=20, choices=MODEL_CHOICES)
    key = models.SlugField(help_text="JSON key for the field")
    label = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    options = models.JSONField(null=True, blank=True, help_text="Options for select fields")

    class Meta:
        unique_together = ('tenant', 'target_model', 'key')

# -----------------------------------------------------------------------------
# Core Entities (Company, Contact)
# -----------------------------------------------------------------------------

class Company(TenantAwareModel):
    name = models.CharField(max_length=255, db_index=True)
    domain = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    annual_revenue = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='companies')
    
    # Store dynamic fields here
    custom_data = models.JSONField(default=dict, blank=True)
    
    tags = models.ManyToManyField(Tag, blank=True)
    territories = models.ManyToManyField('Territory', blank=True)

    def __str__(self):
        return self.name

class Contact(TenantAwareModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(db_index=True, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True)
    
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='contacts')
    
    custom_data = models.JSONField(default=dict, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    territories = models.ManyToManyField('Territory', blank=True)
    score = models.IntegerField(default=0, db_index=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# -----------------------------------------------------------------------------
# Sales Entities (Lead, Deal)
# -----------------------------------------------------------------------------

class Lead(TenantAwareModel):
    """
    Unqualified prospects.
    """
    STATUS_CHOICES = (
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('disqualified', 'Disqualified'),
    )
    
    title = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    source = models.CharField(max_length=100, blank=True)
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    converted_contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    
    custom_data = models.JSONField(default=dict, blank=True)
    territories = models.ManyToManyField('Territory', blank=True)
    score = models.IntegerField(default=0, db_index=True)

class Deal(TenantAwareModel):
    """
    Revenue opportunity.
    """
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    
    pipeline = models.ForeignKey(Pipeline, on_delete=models.PROTECT)
    stage = models.ForeignKey(Stage, on_delete=models.PROTECT)
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='deals', null=True, blank=True)
    primary_contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='deals')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    expected_close_date = models.DateField(null=True, blank=True, db_index=True)
    probability = models.IntegerField(default=50) # Snapshot from Stage or override
    
    custom_data = models.JSONField(default=dict, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    territories = models.ManyToManyField('Territory', blank=True)

# -----------------------------------------------------------------------------
# Interactions (Activity, Note)
# -----------------------------------------------------------------------------

class Note(TenantAwareModel):
    body = models.TextField()
    
    # Relations (Nullable FKs)
    # Allows pinning a note to multiple entities if needed, generic but explicit
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='notes')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='notes')
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True, related_name='notes')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='notes')
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

class Activity(TenantAwareModel):
    TYPE_CHOICES = (
        ('call', 'Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('task', 'Task'),
    )
    
    activity_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    subject = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    occurred_at = models.DateTimeField(default=models.functions.Now)
    
    # Task specific fields
    due_date = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    # Relations
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

# -----------------------------------------------------------------------------
# Territory & Assignment Management
# -----------------------------------------------------------------------------

class Territory(TenantAwareModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='managed_territories')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_territories')

    def __str__(self):
        return self.name

class TerritoryMember(BaseModel):
    """
    Users belonging to a territory.
    """
    ROLE_CHOICES = (
        ('member', 'Member'),
        ('manager', 'Manager'),
    )
    territory = models.ForeignKey(Territory, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='territory_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')

    class Meta:
        unique_together = ('territory', 'user')

class AssignmentRule(TenantAwareModel):
    TARGET_CHOICES = (
        ('lead', 'Lead'),
        ('deal', 'Deal'),
        ('company', 'Company'),
        ('contact', 'Contact'),
    )
    name = models.CharField(max_length=100)
    target_model = models.CharField(max_length=20, choices=TARGET_CHOICES)
    criteria = models.JSONField(default=dict)
    
    assign_to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    assign_to_territory = models.ForeignKey(Territory, on_delete=models.SET_NULL, null=True, blank=True)
    
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['position']

# -----------------------------------------------------------------------------
# Scoring Models
# -----------------------------------------------------------------------------

class ScoringRule(TenantAwareModel):
    TARGET_CHOICES = (
        ('lead', 'Lead'),
        ('contact', 'Contact'),
    )
    name = models.CharField(max_length=100)
    target_model = models.CharField(max_length=20, choices=TARGET_CHOICES)
    
    # Ex: {"field": "lead.title", "operator": "eq", "value": "CEO"}
    criteria = models.JSONField(default=dict)
    
    score_change = models.IntegerField(default=10, help_text="Points to add (e.g., 10) or subtract (e.g., -5)")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.score_change})"

class AppliedScoringRule(BaseModel):
    rule = models.ForeignKey(ScoringRule, on_delete=models.CASCADE, related_name='applied_records')
    record_model = models.CharField(max_length=50)
    record_id = models.UUIDField()
    
    class Meta:
        unique_together = ('rule', 'record_model', 'record_id')
        indexes = [
            models.Index(fields=['record_model', 'record_id']),
        ]
