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
