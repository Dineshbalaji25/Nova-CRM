from celery import shared_task
from .engine import run_node

@shared_task(queue='default')
def process_workflow_step(execution_id, node_id):
    """
    Async wrapper for the engine.
    """
    run_node(execution_id, node_id)
