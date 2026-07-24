import logging
from apps.crm.models import Contact, Deal, Company, Activity, Pipeline, Stage
from django.utils import timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

class TalesTimelineSyncService:
    def __init__(self, tenant):
        self.tenant = tenant

    def handle_order_completed(self, data):
        """
        Maps a TalesTimeline order completion to Nova-CRM.
        """
        customer_email = data.get('customer_email')
        order_total = data.get('order_total', 0)
        order_id = data.get('order_id')
        currency = data.get('currency', 'INR')

        # 1. Get or Create Contact
        contact, _ = Contact.objects.get_or_create(
            tenant=self.tenant,
            email=customer_email,
            defaults={
                'first_name': data.get('first_name', 'Unknown'),
                'last_name': data.get('last_name', ''),
                'phone': data.get('phone', ''),
            }
        )

        # 2. Get Default Pipeline and 'Won' Stage
        pipeline = Pipeline.objects.filter(tenant=self.tenant, is_default=True).first()
        if not pipeline:
            pipeline = Pipeline.objects.filter(tenant=self.tenant).first()
        
        if not pipeline:
            logger.error(f"No pipeline found for tenant {self.tenant}")
            return False

        # Assuming the stage with highest position or name 'Won' is the closed stage
        stage = Stage.objects.filter(pipeline=pipeline, win_probability=100).first()
        if not stage:
            stage = Stage.objects.filter(pipeline=pipeline).order_by('-position').first()

        # 3. Create Deal
        deal = Deal.objects.create(
            tenant=self.tenant,
            title=f"Order {order_id} - TalesTimeline",
            amount=Decimal(str(order_total)),
            currency=currency,
            pipeline=pipeline,
            stage=stage,
            primary_contact=contact,
            expected_close_date=timezone.now().date(),
            probability=100
        )

        # 4. Create Activity
        Activity.objects.create(
            tenant=self.tenant,
            activity_type='task',
            subject=f"New Sale: Order {order_id}",
            body=f"Order completed in TalesTimeline. Total: {order_total} {currency}",
            occurred_at=timezone.now(),
            contact=contact,
            deal=deal,
            is_completed=True
        )

        return True

    def handle_contact_updated(self, data):
        """
        Updates or creates a contact from TalesTimeline.
        """
        email = data.get('email')
        if not email:
            return False

        contact, created = Contact.objects.update_or_create(
            tenant=self.tenant,
            email=email,
            defaults={
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'phone': data.get('phone', ''),
                'custom_data': {**data.get('custom_data', {}), 'source': 'TalesTimeline'}
            }
        )
        return True

class TalesTimelineOutboundSyncService:
    def __init__(self, tenant):
        self.tenant = tenant
        from .models import IntegrationProvider
        # Look for active TalesTimeline provider to get the outgoing webhook URL
        self.provider = IntegrationProvider.objects.filter(
            tenant=tenant, 
            provider_type='tales_timeline', 
            is_active=True
        ).first()

    def _send_webhook(self, event_type, payload):
        if not self.provider:
            return False
            
        webhook_url = self.provider.config_data.get('outgoing_webhook_url')
        if not webhook_url:
            logger.warning(f"No outgoing_webhook_url configured for TalesTimeline on tenant {self.tenant}")
            return False
            
        import requests
        from .models import IntegrationLog
        
        headers = {'Content-Type': 'application/json'}
        secret = self.provider.config_data.get('outgoing_webhook_secret')
        if secret:
            headers['X-Webhook-Secret'] = secret
            
        data = {
            'event': event_type,
            'data': payload
        }
        
        try:
            response = requests.post(webhook_url, json=data, headers=headers, timeout=5)
            response.raise_for_status()
            IntegrationLog.objects.create(
                provider=self.provider,
                event_type=f"outbound:{event_type}",
                payload=data,
                status="success"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send outbound webhook to TalesTimeline: {str(e)}")
            IntegrationLog.objects.create(
                provider=self.provider,
                event_type=f"outbound:{event_type}",
                payload=data,
                status="failed",
                error_message=str(e)
            )
            return False

    def sync_deal(self, deal):
        """ Syncs a Deal (Order) to TalesTimeline """
        payload = {
            'id': str(deal.id),
            'title': deal.title,
            'amount': str(deal.amount),
            'currency': deal.currency,
            'stage': deal.stage.name if deal.stage else None,
            'expected_close_date': str(deal.expected_close_date) if deal.expected_close_date else None,
            'probability': deal.probability
        }
        return self._send_webhook('crm.deal.updated', payload)

    def sync_company(self, company):
        """ Syncs a Company (Partner) to TalesTimeline """
        payload = {
            'id': str(company.id),
            'name': company.name,
            'domain': company.domain,
            'industry': company.industry,
            'annual_revenue': str(company.annual_revenue) if company.annual_revenue else None
        }
        return self._send_webhook('crm.company.updated', payload)

    def sync_invoice(self, invoice):
        """ Syncs a BillingInvoice (Payment) to TalesTimeline """
        payload = {
            'id': str(invoice.id),
            'gateway_invoice_id': invoice.gateway_invoice_id,
            'amount_paid_cents': invoice.amount_paid_cents,
            'status': invoice.status,
            'paid_at': str(invoice.paid_at) if invoice.paid_at else None
        }
        return self._send_webhook('crm.invoice.updated', payload)

