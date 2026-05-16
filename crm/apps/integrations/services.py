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
