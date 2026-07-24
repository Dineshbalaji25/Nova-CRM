from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.crm.models import Deal, Company
from apps.billing.models import BillingInvoice
from .services import TalesTimelineOutboundSyncService

@receiver(post_save, sender=Deal)
def sync_deal_to_tales_timeline(sender, instance, created, **kwargs):
    if hasattr(instance, 'tenant'):
        service = TalesTimelineOutboundSyncService(tenant=instance.tenant)
        service.sync_deal(instance)

@receiver(post_save, sender=Company)
def sync_company_to_tales_timeline(sender, instance, created, **kwargs):
    if hasattr(instance, 'tenant'):
        service = TalesTimelineOutboundSyncService(tenant=instance.tenant)
        service.sync_company(instance)

@receiver(post_save, sender=BillingInvoice)
def sync_invoice_to_tales_timeline(sender, instance, created, **kwargs):
    if hasattr(instance, 'tenant'):
        service = TalesTimelineOutboundSyncService(tenant=instance.tenant)
        service.sync_invoice(instance)
