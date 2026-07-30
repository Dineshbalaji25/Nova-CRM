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
            # Handle race condition: two concurrent conversions of same company name
            # may both attempt INSERT and one will fail with IntegrityError
            from django.db import IntegrityError
            try:
                company, created = Company.objects.get_or_create(
                    tenant_id=lead.tenant_id,
                    name=lead.company_name,
                    defaults={'owner': lead.owner}
                )
            except IntegrityError:
                # Another request created the company between our SELECT and INSERT
                company = Company.objects.get(
                    tenant_id=lead.tenant_id,
                    name=lead.company_name
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
        Uses bulk operations to avoid N+1 queries and recursive signal loops.
        """
        rules = ScoringRule.objects.filter(
            target_model=model_name, is_active=True, tenant_id=instance.tenant_id, is_deleted=False
        )
        if not rules.exists():
            return

        # Prefetch already-applied rule IDs in a single query to avoid N+1
        applied_ids = set(
            AppliedScoringRule.objects.filter(
                record_model=model_name, record_id=instance.id
            ).values_list('rule_id', flat=True)
        )

        # Build context for evaluator
        context = {model_name: instance.__dict__}

        total_score_change = 0
        new_applications = []

        for rule in rules:
            if rule.id in applied_ids:
                continue
            if evaluate_condition(context, rule.criteria):
                total_score_change += rule.score_change
                new_applications.append(
                    AppliedScoringRule(
                        rule=rule,
                        record_model=model_name,
                        record_id=instance.id,
                    )
                )

        # Apply score change with a single save() call outside the loop
        # This prevents recursive post_save signal loops
        if total_score_change != 0:
            instance.score += total_score_change
            instance.save(update_fields=['score'])

        # Bulk-create all new AppliedScoringRule records
        if new_applications:
            AppliedScoringRule.objects.bulk_create(
                new_applications, ignore_conflicts=True
            )

class TerritoryEngine:
    @classmethod
    def process_record(cls, instance, model_name):
        """
        Evaluates territory assignment rules.
        """
        rules = AssignmentRule.objects.filter(target_model=model_name, is_active=True, tenant_id=instance.tenant_id, is_deleted=False).order_by('position')
        
        context = {model_name: instance.__dict__}
        
        for rule in rules:
            if evaluate_condition(context, rule.criteria):
                if rule.assign_to_user and hasattr(instance, 'owner'):
                    instance.owner = rule.assign_to_user
                    instance.save(update_fields=['owner'])
                    # Stop after first owner assignment to prevent subsequent rules
                    # from overwriting the assignment
                    if not rule.assign_to_territory:
                        break
                    
                if rule.assign_to_territory and hasattr(instance, 'territories'):
                    instance.territories.add(rule.assign_to_territory)
                    
                # If we assigned an owner, break after also handling territory on same rule
                if rule.assign_to_user:
                    break
