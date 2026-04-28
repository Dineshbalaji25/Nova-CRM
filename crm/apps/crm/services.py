from django.db import transaction
from .models import Lead, Contact, Company, Deal

class LeadConversionService:
    @classmethod
    @transaction.atomic
    def convert(cls, lead, create_deal=False, deal_data=None):
        """
        Converts a Lead into a Contact, and optionally a Company and Deal.
        """
        if lead.status == 'qualified':
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
        Stub for scoring logic.
        """
        # In a real implementation, this would fetch ScoringRules
        # and update instance.score
        pass

class TerritoryEngine:
    @classmethod
    def process_record(cls, instance, model_name):
        """
        Stub for territory assignment logic.
        """
        # In a real implementation, this would fetch AssignmentRules
        # and update instance.territories
        pass
