from django.db import models
from django.conf import settings
from apps.core.models import TenantAwareModel, BaseModel

class Workflow(TenantAwareModel):
    TRIGGER_CHOICES = (
        ('event', 'Event Based'),
        ('schedule', 'Time Based'),
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_CHOICES)
    # Configuration for the trigger.
    # Ex: {"event": "deal.created", "filters": {"pipeline_id": 1}}
    trigger_config = models.JSONField(default=dict)
    
    def __str__(self):
        return self.name

class WorkflowNode(BaseModel):
    """
    A single step in the workflow DAG/Chain.
    """
    TYPE_CHOICES = (
        ('action', 'Action'),
        ('condition', 'Condition'),
        ('delay', 'Delay'),
    )
    
    # Not TenantAware directly, strictly linked to Workflow which is TenantAware
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='nodes')
    
    node_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    # Label for UI
    label = models.CharField(max_length=100)
    
    # Key for the Action Registry (e.g. 'email.send', 'crm.update_deal')
    action_key = models.CharField(max_length=100, blank=True)
    
    # Configuration for the action/condition
    # Ex: {"template_id": 123, "to": "{{ contact.email }}"}
    config = models.JSONField(default=dict, blank=True)
    
    # Pointer to next step (Simple Linked List for MVP, Graph for full version)
    next_node = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_nodes')
    
    # For branching (true/false path), we might need secondary pointers.
    false_next_node = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='false_previous_nodes')
    
    def __str__(self):
        return f"{self.workflow.name} -> {self.label}"

class WorkflowExecution(BaseModel):
    """
    Represents a single run of a workflow.
    """
    STATUS_CHOICES = (
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')
    
    # Snapshot of data at time of trigger
    trigger_context = models.JSONField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Current Head
    current_node = models.ForeignKey(WorkflowNode, on_delete=models.SET_NULL, null=True, blank=True)

class NodeExecution(BaseModel):
    """
    Log of a single step execution.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('skipped', 'Skipped'),
    )
    
    execution = models.ForeignKey(WorkflowExecution, on_delete=models.CASCADE, related_name='node_logs')
    node = models.ForeignKey(WorkflowNode, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    input_data = models.JSONField(null=True, blank=True)
    output_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

# -----------------------------------------------------------------------------
# Blueprint (State Machine) Models
# -----------------------------------------------------------------------------

class Blueprint(TenantAwareModel):
    """
    State machine definition for enforcing strict process flows (e.g., Lead Qualification).
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # e.g., 'crm.Deal', 'sales.Quote'
    target_model = models.CharField(max_length=100)
    
    # NEW: Which field on the target model does this blueprint control?
    # e.g. 'stage_id' for Deal blueprints, 'status' for Lead blueprints
    controlled_field = models.CharField(
        max_length=100,
        blank=True,
        help_text="Field name on the target model that transitions update. E.g. 'stage_id' or 'status'"
    )
    
    # When criteria is met, a record enters the blueprint
    # e.g. {"pipeline_id": 1}
    entry_criteria = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} ({self.target_model})"

class BlueprintState(BaseModel):
    blueprint = models.ForeignKey(Blueprint, on_delete=models.CASCADE, related_name='states')
    name = models.CharField(max_length=100) # e.g., "Negotiate"
    
    # The actual db value this maps to (e.g. Stage ID or Status string)
    reference_value = models.CharField(max_length=255, blank=True)
    
    # Visual coordinates for the UI builder
    ui_x = models.IntegerField(default=0)
    ui_y = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name

class BlueprintTransition(BaseModel):
    """
    A specific button a user can click to move from one state to another.
    """
    blueprint = models.ForeignKey(Blueprint, on_delete=models.CASCADE, related_name='transitions')
    name = models.CharField(max_length=100) # e.g., "Approve Discount"
    
    from_state = models.ForeignKey(BlueprintState, on_delete=models.CASCADE, related_name='outgoing_transitions')
    to_state = models.ForeignKey(BlueprintState, on_delete=models.CASCADE, related_name='incoming_transitions')
    
    # BEFORE: conditions that must be true to even show the button
    criteria = models.JSONField(default=dict, blank=True) 
    
    # DURING: Pop-up fields the user MUST fill out (e.g., 'amount', 'expected_close_date')
    required_fields = models.JSONField(default=list, blank=True)
    
    # AFTER: Actions to trigger (e.g., {"type": "email", "template": "X"})
    actions = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.name}: {self.from_state.name} -> {self.to_state.name}"

class BlueprintRecordContext(TenantAwareModel):
    """
    Tracks a specific record (e.g., a Deal) that is currently locked in a Blueprint.
    """
    blueprint = models.ForeignKey(Blueprint, on_delete=models.CASCADE)
    
    # Pointer to the external record
    record_model = models.CharField(max_length=100)
    record_id = models.UUIDField()
    
    current_state = models.ForeignKey(BlueprintState, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('record_model', 'record_id')

