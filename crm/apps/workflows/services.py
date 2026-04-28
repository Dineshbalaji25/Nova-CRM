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
        Executes a blueprint transition.
        1. Validates the record is in the correct from_state.
        2. Validates all required_fields are present.
        3. Updates required fields on the instance.
        4. Updates the actual controlled_field on the instance using to_state.reference_value.
        5. Fires post-transition actions.
        6. Moves BlueprintRecordContext to new state.
        """
        try:
            transition = BlueprintTransition.objects.select_related(
                'from_state', 'to_state', 'blueprint'
            ).get(id=transition_id)
            
            ctx = BlueprintRecordContext.objects.get(
                blueprint=transition.blueprint,
                record_model=model_name,
                record_id=instance.id
            )

            if ctx.current_state != transition.from_state:
                return {"success": False, "error": f"Record is in state '{ctx.current_state.name}', expected '{transition.from_state.name}'."}

            # Validate and apply required fields
            for req in transition.required_fields:
                field_name = req.get('name') if isinstance(req, dict) else req
                if field_name not in context_data:
                    return {"success": False, "error": f"Missing required field: {field_name}"}
                try:
                    setattr(instance, field_name, context_data[field_name])
                except AttributeError:
                    return {"success": False, "error": f"Field '{field_name}' does not exist on {model_name}."}

            # --- KEY FIX: Apply to_state.reference_value to the controlled_field ---
            blueprint = transition.blueprint
            controlled_field = blueprint.controlled_field
            reference_value = transition.to_state.reference_value

            if controlled_field and reference_value:
                # Handle FK fields (e.g. 'stage_id' expects an integer/UUID)
                # Try to cast reference_value to the appropriate type
                field_obj = instance._meta.get_field(controlled_field.replace('_id', ''))
                from django.db.models import ForeignKey
                if isinstance(field_obj, ForeignKey) and not controlled_field.endswith('_id'):
                    controlled_field = controlled_field + '_id'
                
                # Try numeric cast for FK IDs, else use string
                try:
                    casted_value = int(reference_value)
                except (ValueError, TypeError):
                    try:
                        import uuid
                        casted_value = uuid.UUID(reference_value)
                    except (ValueError, AttributeError):
                        casted_value = reference_value

                setattr(instance, controlled_field, casted_value)

            instance.save()

            # Fire post-transition actions
            action_context = {
                model_name: {
                    "id": str(instance.id),
                    **context_data,
                    "new_state": transition.to_state.name,
                }
            }
            for action_config in transition.actions:
                action_type = action_config.get("type")
                handler = ActionRegistry.get_action(action_type)
                if handler:
                    try:
                        handler(action_context, action_config)
                    except Exception as e:
                        logger.error(f"Post-transition action '{action_type}' failed: {e}")

            # Advance the state context
            ctx.current_state = transition.to_state
            ctx.save()

            return {
                "success": True,
                "new_state": ctx.current_state.name,
                "new_state_id": str(ctx.current_state.id)
            }

        except BlueprintTransition.DoesNotExist:
            return {"success": False, "error": "Transition not found."}
        except BlueprintRecordContext.DoesNotExist:
            return {"success": False, "error": "Record is not enrolled in this blueprint."}
        except Exception as e:
            logger.exception("Transition execution failed")
            return {"success": False, "error": str(e)}
