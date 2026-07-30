import logging
from apps.users.models import User
from apps.crm.models import Contact

logger = logging.getLogger(__name__)

class GDPRService:
    @staticmethod
    def anonymize_tenant_data(tenant_id):
        """
        Anonymizes all contact data for a tenant (GDPR Right to be Forgotten).
        Uses bulk operations for performance.
        """
        logger.info(f"Starting GDPR scrub for tenant {tenant_id}")

        # 1. Bulk-update all non-unique fields in one query
        Contact.objects.filter(tenant_id=tenant_id).update(
            first_name='Anonymized',
            last_name='User',
            phone='',
            custom_data={},
        )

        # 2. Anonymize email addresses individually (email must remain unique per row)
        # Use a tight loop only for the email field — much faster than the original
        # which called full model.save() (triggering signals) per contact
        contacts_qs = Contact.objects.filter(
            tenant_id=tenant_id
        ).only('id', 'email')
        
        for contact in contacts_qs.iterator(chunk_size=500):
            Contact.objects.filter(pk=contact.pk).update(
                email=f'deleted_{contact.pk}@removed.invalid'
            )

        # 3. Redact Audit Logs — anonymize the description, keep the log for compliance
        from .models import AuditLog
        AuditLog.objects.filter(tenant_id=tenant_id).update(description='[REDACTED]')

        logger.info(f"GDPR scrub completed for tenant {tenant_id}")
        return True

    @staticmethod
    def export_tenant_data(tenant_id):
        """
        Generates JSON dump.
        """
        # Placeholder
        return {"contacts": [], "deals": []}
