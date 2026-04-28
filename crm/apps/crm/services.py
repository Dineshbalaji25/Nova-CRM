import logging
from .models import ScoringRule, AppliedScoringRule, AssignmentRule, Territory
from apps.workflows.engine import evaluate_condition

logger = logging.getLogger(__name__)

class ScoringEngine:
    @classmethod
    def process_record(cls, instance, model_name):
        """
        Evaluates a record against all active ScoringRules for its model type.
        Adds/removes points dynamically.
        """
        if model_name not in ['lead', 'contact']:
            return
            
        rules = ScoringRule.objects.filter(
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
        
        score_changed = False
        current_score = instance.score or 0
        
        for rule in rules:
            criteria_matched = False
            # Criteria is either a list of conditions or a dict
            if isinstance(rule.criteria, dict) and rule.criteria:
                criteria_matched = evaluate_condition(context, rule.criteria)
            elif isinstance(rule.criteria, list) and rule.criteria:
                criteria_matched = True
                for c in rule.criteria:
                    if not evaluate_condition(context, c):
                        criteria_matched = False
                        break
            
            # Check if rule is already applied
            applied = AppliedScoringRule.objects.filter(
                rule=rule,
                record_model=model_name,
                record_id=instance.id
            ).exists()
            
            if criteria_matched and not applied:
                # Apply rule
                current_score += rule.score_change
                AppliedScoringRule.objects.create(
                    rule=rule,
                    record_model=model_name,
                    record_id=instance.id
                )
                score_changed = True
                logger.info(f"ScoringRule applied: {rule.name} (+{rule.score_change}) to {model_name} {instance.id}")
                
            elif not criteria_matched and applied:
                # Remove rule
                current_score -= rule.score_change
                AppliedScoringRule.objects.filter(
                    rule=rule,
                    record_model=model_name,
                    record_id=instance.id
                ).delete()
                score_changed = True
                logger.info(f"ScoringRule removed: {rule.name} (-{rule.score_change}) from {model_name} {instance.id}")
                
        if score_changed:
            instance.score = current_score
            # Save without triggering signals again
            instance.save(update_fields=['score'])

class TerritoryEngine:
    """
    Logic for automated assignment of records to Territories and Owners.
    """
    @classmethod
    def process_record(cls, instance, model_name):
        """
        Evaluates a record against active AssignmentRules.
        """
        rules = AssignmentRule.objects.filter(
            target_model=model_name,
            is_active=True,
            tenant_id=instance.tenant_id
        ).order_by('position')
        
        if not rules:
            return

        # Prepare context for criteria evaluation
        context = {
            model_name: {
                field.name: getattr(instance, field.name) for field in instance._meta.fields if isinstance(getattr(instance, field.name), (str, int, float, bool)) or getattr(instance, field.name) is None
            }
        }
        context[model_name]["id"] = str(instance.id)

        update_fields = []
        
        for rule in rules:
            criteria_matched = False
            if isinstance(rule.criteria, dict) and rule.criteria:
                criteria_matched = evaluate_condition(context, rule.criteria)
            elif isinstance(rule.criteria, list) and rule.criteria:
                criteria_matched = True
                for c in rule.criteria:
                    if not evaluate_condition(context, c):
                        criteria_matched = False
                        break
            
            if criteria_matched:
                # 1. Assign Territory if specified
                if rule.assign_to_territory:
                    # check if already in territory to avoid duplicate M2M entry
                    if not instance.territories.filter(id=rule.assign_to_territory.id).exists():
                        instance.territories.add(rule.assign_to_territory)
                        logger.info(f"Assigned {model_name} {instance.id} to Territory {rule.assign_to_territory.name}")
                
                # 2. Assign Owner if specified
                if rule.assign_to_user and instance.owner != rule.assign_to_user:
                    instance.owner = rule.assign_to_user
                    update_fields.append('owner')
                    logger.info(f"Reassigned {model_name} {instance.id} to Owner {rule.assign_to_user.email}")
                
                # In standard assignment, we often stop after the first match
                # depending on whether rule.stop_after_match is True (optional enhancement)
                # For now, we continue to allow multiple territory assignments
                
        if update_fields:
            instance.save(update_fields=update_fields)
