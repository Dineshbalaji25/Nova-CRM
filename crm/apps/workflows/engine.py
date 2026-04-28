import logging
import json
from django.utils import timezone
from .models import WorkflowExecution, NodeExecution

logger = logging.getLogger(__name__)

class ActionRegistry:
    """
    Repository of available actions for the workflow engine.
    """
    _actions = {}

    @classmethod
    def register(cls, key):
        def decorator(func):
            cls._actions[key] = func
            return func
        return decorator

    @classmethod
    def get_action(cls, key):
        return cls._actions.get(key)

from django.apps import apps

# -----------------------------------------------------------------------------
# Context Resolver
# -----------------------------------------------------------------------------

def resolve_variable(context, path):
    """
    Resolves dot-notation path against context dict.
    Ex: path="deal.amount" -> context["deal"]["amount"]
    """
    if not path or not isinstance(path, str):
        return None
    
    # Simple template substitution handling e.g., "{{ deal.id }}"
    if path.startswith("{{") and path.endswith("}}"):
        path = path.strip("{} ")
        
    parts = path.split('.')
    current = context
    try:
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
    except Exception as e:
        logger.warning(f"Failed to resolve variable {path}: {str(e)}")
        return None

# -----------------------------------------------------------------------------
# Standard Actions
# -----------------------------------------------------------------------------

@ActionRegistry.register('utils.log')
def action_log(context, config):
    """Simple debug action."""
    logger.info(f"WORKFLOW LOG: {config.get('message', 'No message')} | Context: {context.keys()}")
    return {"status": "logged"}

@ActionRegistry.register('crm.update_record')
def action_update_record(context, config):
    """
    Update record dynamically.
    config = {"model": "deal", "id": "{{ deal.id }}", "fields": {"stage_id": 2}}
    """
    model_name = config.get('model')
    record_id_str = config.get('id', '')
    fields_to_update = config.get('fields', {})
    
    record_id = resolve_variable(context, record_id_str) if '{{' in record_id_str else record_id_str
    
    if not model_name or not record_id:
        return {"updated": False, "error": "Missing model or id"}
        
    try:
        Model = apps.get_model('crm', model_name)
        record = Model.objects.get(id=record_id)
        
        for field, raw_value in fields_to_update.items():
            # Resolve dynamic values if needed
            val = resolve_variable(context, str(raw_value)) if isinstance(raw_value, str) and '{{' in raw_value else raw_value
            setattr(record, field, val)
            
        record.save()
        return {"updated": True, "model": model_name, "id": str(record_id)}
    except Exception as e:
        logger.error(f"Error updating record: {str(e)}")
        return {"updated": False, "error": str(e)}

@ActionRegistry.register('crm.create_task')
def action_create_task(context, config):
    """
    Create a task.
    config = {"title": "Call {{ contact.first_name }}", "assigned_to": "{{ deal.owner_id }}"}
    """
    try:
        Task = apps.get_model('crm', 'Task')
        
        # Simple string replacement for title/description
        title = config.get('title', 'Automated Task')
        for key in context.keys():
            if isinstance(context[key], dict):
                for subkey, subval in context[key].items():
                    placeholder = f"{{{{ {key}.{subkey} }}}}"
                    if placeholder in title:
                        title = title.replace(placeholder, str(subval))
                        
        task = Task.objects.create(
            title=title,
            description=config.get('description', ''),
            # ... other fields mapped here
        )
        return {"created": True, "task_id": str(task.id)}
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        return {"created": False, "error": str(e)}

# -----------------------------------------------------------------------------
# Condition Evaluator
# -----------------------------------------------------------------------------

def evaluate_condition(context, config):
    """
    Evaluates a logic rule against the context.
    Config Ex: {"field": "deal.amount", "operator": "gt", "value": 1000}
    """
    field_path = config.get('field', '')
    operator = config.get('operator', 'eq')
    target_value = config.get('value')
    
    actual_value = resolve_variable(context, field_path)
    
    if actual_value is None:
        return False
        
    try:
        # Basic type casting for comparison
        if isinstance(target_value, int) or isinstance(target_value, float):
            actual_value = float(actual_value)
        
        if operator == 'eq':
            return actual_value == target_value
        elif operator == 'neq':
            return actual_value != target_value
        elif operator == 'gt':
            return actual_value > target_value
        elif operator == 'lt':
            return actual_value < target_value
        elif operator == 'contains':
            return str(target_value).lower() in str(actual_value).lower()
    except (ValueError, TypeError):
        return False
        
    return False

# -----------------------------------------------------------------------------
# Execution Core
# -----------------------------------------------------------------------------

def run_node(execution_id, node_id):
    """
    The atomic unit of work for the worker.
    """
    try:
        execution = WorkflowExecution.objects.get(id=execution_id)
        node = execution.workflow.nodes.get(id=node_id)
        
        # Log Start
        log = NodeExecution.objects.create(
            execution=execution,
            node=node,
            input_data=execution.trigger_context
        )
        
        result = {}
        next_step_id = node.next_node_id
        
        # Execute logic based on type
        if node.node_type == 'action':
            handler = ActionRegistry.get_action(node.action_key)
            if handler:
                result = handler(execution.trigger_context, node.config)
            else:
                raise ValueError(f"Unknown action: {node.action_key}")
                
        elif node.node_type == 'condition':
            passed = evaluate_condition(execution.trigger_context, node.config)
            result = {"passed": passed}
            if not passed:
                next_step_id = node.false_next_node_id
        
        # Log Success
        log.status = 'success'
        log.output_data = result
        log.completed_at = timezone.now()
        log.save()
        
        # Trigger Next Step
        if next_step_id:
            from .tasks import process_workflow_step
            execution.current_node_id = next_step_id
            execution.save()
            process_workflow_step.delay(execution.id, next_step_id)
        else:
            execution.status = 'completed'
            execution.completed_at = timezone.now()
            execution.save()

    except Exception as e:
        logger.exception("Workflow Node Failed")
        if 'log' in locals():
            log.status = 'failure'
            log.error_message = str(e)
            log.save()
        
        execution.status = 'failed'
        execution.save()
