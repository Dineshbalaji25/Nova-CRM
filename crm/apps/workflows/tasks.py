from celery import shared_task
from .engine import run_node

@shared_task(queue='default')
def process_workflow_step(execution_id, node_id):
    """
    Async wrapper for the engine.
    """
    run_node(execution_id, node_id)

@shared_task(queue='default')
def evaluate_scheduled_workflows():
    """
    Evaluates scheduled workflows (e.g. running every hour).
    Only fires each workflow if its configured interval has elapsed since last execution.
    """
    from .models import Workflow, WorkflowExecution
    from django.utils import timezone

    now = timezone.now()
    workflows = Workflow.objects.filter(is_active=True, trigger_type='schedule')

    fired = 0
    for wf in workflows:
        # Check if enough time has elapsed since last execution
        interval_minutes = wf.trigger_config.get('interval_minutes', 60)
        if wf.last_executed_at is not None:
            elapsed = (now - wf.last_executed_at).total_seconds() / 60
            if elapsed < interval_minutes:
                continue  # Not time yet

        execution = WorkflowExecution.objects.create(
            workflow=wf,
            trigger_context={"trigger": "schedule", "time": str(now)}
        )
        first_node = wf.nodes.first()
        if first_node:
            execution.current_node = first_node
            execution.save()
            process_workflow_step.delay(execution.id, first_node.id)

        # Record the execution time
        wf.last_executed_at = now
        wf.save(update_fields=['last_executed_at'])
        fired += 1

    return f"Fired {fired} scheduled workflows"

@shared_task(queue='default')
def trigger_workflow_event(event_name, model_name, record_id, tenant_id):
    from .models import Workflow, WorkflowExecution
    from django.apps import apps
    from django.core.serializers.json import DjangoJSONEncoder
    import json
    
    workflows = Workflow.objects.filter(
        is_active=True, 
        trigger_type='event',
        tenant_id=tenant_id
    )
    
    for wf in workflows:
        if wf.trigger_config.get('event') == event_name:
            Model = apps.get_model('crm', model_name)
            record = Model.objects.filter(id=record_id).values().first()
            if not record:
                continue
            
            # Serialize dates properly
            record_dict = json.loads(json.dumps(record, cls=DjangoJSONEncoder))
                
            execution = WorkflowExecution.objects.create(
                workflow=wf,
                trigger_context={"event": event_name, model_name: record_dict, "tenant_id": tenant_id}
            )
            # Find root node
            first_node = wf.nodes.filter(previous_nodes__isnull=True).first()
            if first_node:
                execution.current_node = first_node
                execution.save()
                process_workflow_step.delay(execution.id, first_node.id)
