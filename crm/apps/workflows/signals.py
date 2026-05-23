from django.dispatch import receiver
from django.db.models.signals import post_save
from apps.crm.models import Deal, Contact, Lead
from .models import Workflow
from .tasks import process_workflow_step

from .engine import evaluate_condition

def trigger_workflow(sender, instance, created, **kwargs):
    """
    Generic Dispatcher: Listens to CRM model changes and spawns workflows.
    """
    model_name = sender._meta.model_name # e.g., 'deal'
    event_type = f"{model_name}.created" if created else f"{model_name}.updated"
    
    # 1. Find Active Workflows for this tenant & event
    workflows = Workflow.objects.filter(
        tenant_id=instance.tenant_id,
        is_active=True,
        trigger_type='event',
        trigger_config__event=event_type
    )
    
    for wf in workflows:
        # Serialize primitive context
        obj_context = {}
        for field in instance._meta.fields:
            val = getattr(instance, field.name)
            if isinstance(val, (str, int, float, bool)) or val is None:
                obj_context[field.name] = val
            else:
                # UUID, Decimal, datetime, etc.
                obj_context[field.name] = str(val)
            
            # Also ensure ForeignKey id is explicitly set
            if field.is_relation and val:
                obj_context[f"{field.name}_id"] = str(val.id)
                
        context = {
            model_name: obj_context,
            "tenant_id": str(instance.tenant_id)
        }

        # 2. Check filters in trigger_config
        filters = wf.trigger_config.get('filters', [])
        passed_filters = True
        for f in filters:
            if not evaluate_condition(context, f):
                passed_filters = False
                break
                
        if not passed_filters:
            continue
        
        # 3. Create Execution
        from .models import WorkflowExecution
        
        execution = WorkflowExecution.objects.create(
            workflow=wf,
            trigger_context=context
        )
        
        # 4. Start First Node (DAG root resolution)
        all_nodes = list(wf.nodes.all())
        target_ids = {n.next_node_id for n in all_nodes if n.next_node_id} | {n.false_next_node_id for n in all_nodes if n.false_next_node_id}
        start_nodes = [n for n in all_nodes if n.id not in target_ids]
        first_node = start_nodes[0] if start_nodes else (all_nodes[0] if all_nodes else None)
        
        if first_node:
            execution.current_node = first_node
            execution.save()
            process_workflow_step.delay(execution.id, first_node.id)

    # Add Blueprint evaluation hook
    from .services import BlueprintService
    BlueprintService.evaluate_entry(instance, model_name)

# Register Signals
post_save.connect(trigger_workflow, sender=Deal)
post_save.connect(trigger_workflow, sender=Contact)
post_save.connect(trigger_workflow, sender=Lead)
