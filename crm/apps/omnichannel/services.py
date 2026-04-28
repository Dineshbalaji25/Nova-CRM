import logging
from django.db.models import Q
from apps.crm.models import Lead, Contact, Deal
from .models import EmailMessage, CallLog

logger = logging.getLogger(__name__)

class EmailProcessor:
    """
    Logic for processing incoming emails and linking them to CRM entities.
    """
    @classmethod
    def process_incoming(cls, email_msg):
        """
        Links an EmailMessage to a Lead or Contact.
        If no match is found, creates a new Lead.
        """
        from_email = email_msg.from_address.lower()
        tenant_id = email_msg.integration.tenant_id
        
        # 1. Try to find a Contact
        contact = Contact.objects.filter(tenant_id=tenant_id, email=from_email).first()
        if contact:
            email_msg.contact = contact
            email_msg.save()
            logger.info(f"Email {email_msg.id} linked to Contact {contact.id}")
            return
            
        # 2. Try to find a Lead
        lead = Lead.objects.filter(tenant_id=tenant_id, email=from_email).first()
        if lead:
            email_msg.lead = lead
            email_msg.save()
            logger.info(f"Email {email_msg.id} linked to Lead {lead.id}")
            return
            
        # 3. Create a new Lead (Email Parsing)
        # Extract name from from_address if possible (e.g. "John Doe <john@example.com>")
        # Simplification: just use the email prefix as name for now
        name_part = from_email.split('@')[0]
        new_lead = Lead.objects.create(
            tenant_id=tenant_id,
            first_name=name_part.capitalize(),
            email=from_email,
            source='Email Parsing',
            title=f"New Lead from {from_email}"
        )
        email_msg.lead = new_lead
        email_msg.save()
        logger.info(f"Email {email_msg.id} parsed into new Lead {new_lead.id}")

class OmnichannelService:
    """
    Consolidates communication logs into a single timeline.
    """
    @classmethod
    def get_timeline(cls, tenant_id, entity_type, entity_id):
        """
        Returns a sorted list of Emails and Calls for a specific entity.
        entity_type: 'lead', 'contact', or 'deal'
        """
        filter_kwargs = {f"{entity_type}_id": entity_id, "tenant_id": tenant_id}
        
        emails = EmailMessage.objects.filter(**filter_kwargs)
        calls = CallLog.objects.filter(**filter_kwargs)
        
        timeline = []
        
        # Normalize Emails
        for email in emails:
            timeline.append({
                "type": "email",
                "id": str(email.id),
                "timestamp": email.sent_at,
                "subject": email.subject,
                "direction": "inbound" if email.from_address != email.integration.email_address else "outbound",
                "summary": email.body_text[:200] if email.body_text else "",
                "sender": email.from_address,
                "is_read": email.is_read
            })
            
        # Normalize Calls
        for call in calls:
            timeline.append({
                "type": "call",
                "id": str(call.id),
                "timestamp": call.created_at, # Using created_at since it's the start of the log
                "direction": call.direction,
                "status": call.status,
                "duration": call.duration_seconds,
                "summary": call.notes,
                "from": call.from_number,
                "to": call.to_number
            })
            
        # Sort by timestamp descending
        timeline.sort(key=lambda x: x['timestamp'], reverse=True)
        return timeline
