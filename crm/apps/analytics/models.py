from django.db import models
from django.conf import settings
from apps.core.models import TenantAwareModel, BaseModel

# -----------------------------------------------------------------------------
# Reports
# -----------------------------------------------------------------------------

class Report(TenantAwareModel):
    """
    Custom tabular report definition based on a target model.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Target model for the driving table (e.g. 'crm.Lead')
    target_model = models.CharField(max_length=100)
    
    # Columns to select
    selected_columns = models.JSONField(default=list)
    
    # Filtering criteria
    filters = models.JSONField(default=dict)
    
    # Grouping & Aggregation settings
    group_by = models.CharField(max_length=100, blank=True)
    aggregate_functions = models.JSONField(default=dict, help_text="e.g. {'amount': 'sum'}")
    
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

# -----------------------------------------------------------------------------
# Dashboards
# -----------------------------------------------------------------------------

class Dashboard(TenantAwareModel):
    """
    A collection of visualizations (BI Builder).
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

class DashboardComponent(BaseModel):
    CHART_TYPES = (
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('line', 'Line Chart'),
        ('funnel', 'Funnel Chart'),
        ('metric', 'Key Metric'),
        ('table', 'Data Table'),
    )
    
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='components')
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    
    name = models.CharField(max_length=255)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES)
    
    # UI Positioning (Grid Layout)
    grid_x = models.IntegerField(default=0)
    grid_y = models.IntegerField(default=0)
    grid_width = models.IntegerField(default=4)
    grid_height = models.IntegerField(default=4)

    def __str__(self):
        return f"{self.dashboard.name} - {self.name}"
