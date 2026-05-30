from django.dispatch import receiver
from django.db.models.signals import post_save
from apps.crm.models import Deal, Contact, Lead, Company
from .tasks import trigger_workflow_event
from .services import BlueprintService

def trigger_workflow(sender, instance, created, **kwargs):
    """
    Generic Dispatcher: Listens to CRM model changes and spawns workflows asynchronously.
    """
    model_name = sender._meta.model_name
    event_type = f"{model_name}.created" if created else f"{model_name}.updated"
    
    tenant_id = str(instance.tenant_id) if instance.tenant_id else None
    
    # 1. Trigger asynchronous workflow evaluation
    trigger_workflow_event.delay(
        event_name=event_type,
        model_name=sender.__name__,
        record_id=str(instance.id),
        tenant_id=tenant_id
    )

    # 2. Evaluate Blueprint Entry (Sync for now or could also be async)
    BlueprintService.evaluate_entry(instance, model_name)

# Register Signals
post_save.connect(trigger_workflow, sender=Deal)
post_save.connect(trigger_workflow, sender=Contact)
post_save.connect(trigger_workflow, sender=Lead)
post_save.connect(trigger_workflow, sender=Company)
