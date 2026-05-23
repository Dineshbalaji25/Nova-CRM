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
        Activity = apps.get_model('crm', 'Activity')
        
        # Simple string replacement for title/description
        title = config.get('title', 'Automated Task')
        description = config.get('description', '')
        for key in context.keys():
            if isinstance(context[key], dict):
                for subkey, subval in context[key].items():
                    placeholder = f"{{{{ {key}.{subkey} }}}}"
                    if placeholder in title:
                        title = title.replace(placeholder, str(subval))
                    if placeholder in description:
                        description = description.replace(placeholder, str(subval))
                        
        kwargs = {
            "activity_type": "task",
            "subject": title,
            "body": description,
        }
        
        # Try to resolve relation fields (deal, contact, company) from config/context
        model_name = config.get('model')
        raw_id = config.get('id', '')
        record_id = resolve_variable(context, raw_id) if '{{' in raw_id else raw_id
        
        if model_name and record_id:
            fk_field = f"{model_name}_id"
            kwargs[fk_field] = record_id
        else:
            # Fallback: look at context keys to see if any matches contact, deal, company
            for model_key in ['contact', 'deal', 'company']:
                if model_key in context and isinstance(context[model_key], dict) and 'id' in context[model_key]:
                    kwargs[f"{model_key}_id"] = context[model_key]['id']
        
        # Set tenant_id
        tenant_id = context.get('tenant_id')
        if not tenant_id:
            for key, val in context.items():
                if isinstance(val, dict) and 'tenant_id' in val:
                    tenant_id = val['tenant_id']
                    break
        if tenant_id:
            kwargs['tenant_id'] = tenant_id
            
        # Try to resolve completed_by/owner
        assigned_to_str = config.get('assigned_to', '')
        assigned_to_id = resolve_variable(context, assigned_to_str) if '{{' in assigned_to_str else assigned_to_str
        if assigned_to_id:
            kwargs['completed_by_id'] = assigned_to_id
            
        task = Activity.objects.create(**kwargs)
        return {"created": True, "task_id": str(task.id)}
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        return {"created": False, "error": str(e)}

@ActionRegistry.register('email.send')
def action_send_email(context, config):
    """
    Send an email via Django's send_mail (which uses settings.EMAIL_BACKEND).
    config = {"to": "{{ contact.email }}", "subject": "Hello", "body": "Welcome to Nova CRM!"}
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        raw_to = config.get('to', '')
        to_email = resolve_variable(context, raw_to) if '{{' in raw_to else raw_to
        
        if not to_email:
            return {"sent": False, "error": "No valid recipient email resolved."}
            
        subject = config.get('subject', 'Notification')
        body = config.get('body', '')
        
        # basic interpolation for body
        for key in context.keys():
            if isinstance(context[key], dict):
                for subkey, subval in context[key].items():
                    placeholder = f"{{{{ {key}.{subkey} }}}}"
                    if placeholder in body:
                        body = body.replace(placeholder, str(subval))
                        
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
        return {"sent": True, "to": to_email}
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return {"sent": False, "error": str(e)}

@ActionRegistry.register('crm.create_note')
def action_create_note(context, config):
    """
    Create a note for a record.
    config = {"body": "Automated note: {{ deal.title }} changed.", "model": "deal", "id": "{{ deal.id }}"}
    """
    try:
        model_name = config.get('model')
        raw_id = config.get('id', '')
        record_id = resolve_variable(context, raw_id) if '{{' in raw_id else raw_id
        
        if not model_name or not record_id:
            return {"created": False, "error": "Missing model or record id"}
            
        body = config.get('body', 'Automated note')
        # basic interpolation
        for key in context.keys():
            if isinstance(context[key], dict):
                for subkey, subval in context[key].items():
                    placeholder = f"{{{{ {key}.{subkey} }}}}"
                    if placeholder in body:
                        body = body.replace(placeholder, str(subval))
                        
        Note = apps.get_model('crm', 'Note')
        kwargs = {"body": body}
        # Assuming the note model has FKs like deal_id, contact_id, etc.
        fk_field = f"{model_name}_id"
        kwargs[fk_field] = record_id
        
        # Set tenant_id
        tenant_id = context.get('tenant_id')
        if not tenant_id:
            for key, val in context.items():
                if isinstance(val, dict) and 'tenant_id' in val:
                    tenant_id = val['tenant_id']
                    break
        if tenant_id:
            kwargs['tenant_id'] = tenant_id
            
        # Try to resolve author
        author_id = context.get('author_id')
        if not author_id:
            for key, val in context.items():
                if isinstance(val, dict) and 'owner_id' in val:
                    author_id = val['owner_id']
                    break
        if author_id:
            kwargs['author_id'] = author_id
            
        note = Note.objects.create(**kwargs)
        return {"created": True, "note_id": str(note.id)}
    except Exception as e:
        logger.error(f"Error creating note: {str(e)}")
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

        elif node.node_type == 'delay':
            # E.g. {"minutes": 15}
            delay_minutes = int(node.config.get('minutes', 0))
            result = {"delayed_minutes": delay_minutes}
            
            log.status = 'success'
            log.output_data = result
            log.completed_at = timezone.now()
            log.save()
            
            if next_step_id:
                from .tasks import process_workflow_step
                execution.current_node_id = next_step_id
                execution.save()
                # Apply delay using Celery's countdown
                process_workflow_step.apply_async(
                    args=[execution.id, next_step_id],
                    countdown=delay_minutes * 60
                )
            return  # Stop executing synchronously
        
        # Log Success for action/condition
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
