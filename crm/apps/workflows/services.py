import logging
from django.apps import apps
from .models import Blueprint, BlueprintRecordContext, BlueprintTransition
from .engine import evaluate_condition, ActionRegistry

logger = logging.getLogger(__name__)

class BlueprintService:
    @classmethod
    def evaluate_entry(cls, instance, model_name):
        """
        Checks if a record should enter any active blueprints.
        Called on post_save.
        """
        # Ex: entry_criteria = {"field": "deal.amount", "operator": "gt", "value": 1000}
        active_blueprints = Blueprint.objects.filter(
            target_model=model_name, 
            is_active=True,
            tenant_id=instance.tenant_id
        )
        
        context = {
            model_name: {
                field.name: getattr(instance, field.name) for field in instance._meta.fields if isinstance(getattr(instance, field.name), (str, int, float, bool)) or getattr(instance, field.name) is None
            }
        }
        context[model_name]["id"] = str(instance.id)
        
        for bp in active_blueprints:
            # Check if already in this blueprint
            if BlueprintRecordContext.objects.filter(blueprint=bp, record_model=model_name, record_id=instance.id).exists():
                continue
                
            criteria = bp.entry_criteria
            if not criteria:
                continue # Require criteria to enter automatically? Or allow manual entry?
                
            # For MVP, assume entry_criteria is a list of conditions like in workflows
            # or a single dict.
            if isinstance(criteria, dict) and criteria:
                if evaluate_condition(context, criteria):
                    cls.enter_blueprint(bp, instance, model_name)
            elif isinstance(criteria, list):
                passed = True
                for c in criteria:
                    if not evaluate_condition(context, c):
                        passed = False
                        break
                if passed:
                    cls.enter_blueprint(bp, instance, model_name)

    @classmethod
    def enter_blueprint(cls, blueprint, instance, model_name):
        # Find start state (state with no incoming transitions, or just the first one)
        # For simplicity, assume the first state created is the start state or we look for one.
        start_state = blueprint.states.first()
        if not start_state:
            return None
            
        return BlueprintRecordContext.objects.create(
            blueprint=blueprint,
            record_model=model_name,
            record_id=instance.id,
            current_state=start_state,
            tenant_id=instance.tenant_id
        )

    @classmethod
    def get_available_transitions(cls, instance, model_name):
        """
        Returns list of transitions available for the current record.
        """
        contexts = BlueprintRecordContext.objects.filter(
            record_model=model_name, 
            record_id=instance.id
        ).select_related('current_state')
        
        available = []
        for ctx in contexts:
            state = ctx.current_state
            if not state:
                continue
                
            transitions = state.outgoing_transitions.all()
            for t in transitions:
                # evaluate t.criteria
                # MVP: assume criteria is empty or passes
                available.append({
                    "id": t.id,
                    "name": t.name,
                    "required_fields": t.required_fields,
                    "blueprint_id": ctx.blueprint_id
                })
        return available

    @classmethod
    def execute_transition(cls, instance, model_name, transition_id, context_data):
        """
        Executes a transition if valid.
        context_data contains required_fields values.
        """
        try:
            transition = BlueprintTransition.objects.get(id=transition_id)
            ctx = BlueprintRecordContext.objects.get(
                blueprint=transition.blueprint,
                record_model=model_name,
                record_id=instance.id
            )
            
            if ctx.current_state != transition.from_state:
                return {"success": False, "error": "Invalid current state."}
                
            # Validate required fields
            for req in transition.required_fields:
                field_name = req.get('name')
                if field_name not in context_data:
                    return {"success": False, "error": f"Missing required field: {field_name}"}
                    
                # Update the instance
                setattr(instance, field_name, context_data[field_name])
                
            # Update instance reference_value if state maps to one
            if transition.to_state.reference_value:
                # E.g. 'stage_id'
                # For MVP, we need to know WHICH field on instance maps to the state.
                # Assuming the blueprint target_model handles this, or hardcode for now.
                # We'll just update the BlueprintRecordContext
                pass
                
            instance.save()
            
            # Execute post-transition actions
            action_context = {
                model_name: {
                    "id": str(instance.id)
                }
            }
            action_context[model_name].update(context_data)
            
            for action_config in transition.actions:
                action_type = action_config.get("type")
                handler = ActionRegistry.get_action(action_type)
                if handler:
                    handler(action_context, action_config)
            
            # Move to next state
            ctx.current_state = transition.to_state
            ctx.save()
            
            return {"success": True, "new_state": ctx.current_state.name}
            
        except Exception as e:
            logger.exception("Transition execution failed")
            return {"success": False, "error": str(e)}
