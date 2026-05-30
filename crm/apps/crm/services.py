from django.db import transaction
from .models import Lead, Contact, Company, Deal, ScoringRule, AppliedScoringRule, AssignmentRule
from apps.workflows.engine import evaluate_condition

class LeadConversionService:
    @classmethod
    @transaction.atomic
    def convert(cls, lead, create_deal=False, deal_data=None):
        """
        Converts a Lead into a Contact, and optionally a Company and Deal.
        """
        if lead.converted_contact is not None:
            raise ValueError("Lead is already qualified/converted.")

        # 1. Create or Find Company
        company = None
        if lead.company_name:
            # Simple match by name and tenant
            company, created = Company.objects.get_or_create(
                tenant_id=lead.tenant_id,
                name=lead.company_name,
                defaults={'owner': lead.owner}
            )

        # 2. Create Contact
        contact = Contact.objects.create(
            tenant_id=lead.tenant_id,
            owner=lead.owner,
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            company=company,
            custom_data=lead.custom_data,
            score=lead.score
        )

        # 3. Create Deal (Optional)
        deal = None
        if create_deal and deal_data:
            deal = Deal.objects.create(
                tenant_id=lead.tenant_id,
                owner=lead.owner,
                company=company,
                primary_contact=contact,
                title=deal_data.get('title', f"{company.name if company else contact.last_name} - Deal"),
                amount=deal_data.get('amount', 0),
                pipeline_id=deal_data.get('pipeline_id'),
                stage_id=deal_data.get('stage_id'),
                expected_close_date=deal_data.get('expected_close_date')
            )

        # 4. Update Lead Status
        lead.status = 'qualified'
        lead.converted_contact = contact
        lead.save()

        return {
            "contact_id": contact.id,
            "company_id": company.id if company else None,
            "deal_id": deal.id if deal else None
        }

class ScoringEngine:
    @classmethod
    def process_record(cls, instance, model_name):
        """
        Evaluates scoring rules and applies points.
        """
        rules = ScoringRule.objects.filter(target_model=model_name, is_active=True, tenant_id=instance.tenant_id)
        
        # Build context for evaluator
        context = {model_name: instance.__dict__}
        
        for rule in rules:
            # Check if already applied
            if AppliedScoringRule.objects.filter(rule=rule, record_model=model_name, record_id=instance.id).exists():
                continue
                
            if evaluate_condition(context, rule.criteria):
                instance.score += rule.score_change
                instance.save(update_fields=['score'])
                AppliedScoringRule.objects.create(rule=rule, record_model=model_name, record_id=instance.id)

class TerritoryEngine:
    @classmethod
    def process_record(cls, instance, model_name):
        """
        Evaluates territory assignment rules.
        """
        rules = AssignmentRule.objects.filter(target_model=model_name, is_active=True, tenant_id=instance.tenant_id).order_by('position')
        
        context = {model_name: instance.__dict__}
        
        for rule in rules:
            if evaluate_condition(context, rule.criteria):
                if rule.assign_to_user and hasattr(instance, 'owner'):
                    instance.owner = rule.assign_to_user
                    instance.save(update_fields=['owner'])
                    
                if rule.assign_to_territory and hasattr(instance, 'territories'):
                    instance.territories.add(rule.assign_to_territory)
                    
                # If rule matches, do we stop? Usually yes for assignment, but since it's territories we can just apply all matches or first match.
                # Standard CRM usually stops at first match for Owner, but can add multiple territories. Let's not break loop to allow multiple unless specified.
                pass
