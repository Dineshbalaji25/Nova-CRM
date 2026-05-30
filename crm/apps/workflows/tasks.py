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
    """
    from .models import Workflow, WorkflowExecution
    from django.utils import timezone
    
    workflows = Workflow.objects.filter(is_active=True, trigger_type='schedule')
    for wf in workflows:
        # In MVP, we just create an execution and start the first node.
        # In a real engine, we'd evaluate the schedule criteria (e.g. "every day at 8am")
        execution = WorkflowExecution.objects.create(
            workflow=wf,
            trigger_context={"trigger": "schedule", "time": str(timezone.now())}
        )
        first_node = wf.nodes.first()
        if first_node:
            execution.current_node = first_node
            execution.save()
            process_workflow_step.delay(execution.id, first_node.id)

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
