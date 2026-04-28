from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Lead, Contact, Company, Deal
from .services import ScoringEngine, TerritoryEngine

@receiver(post_save, sender=Lead)
@receiver(post_save, sender=Contact)
def evaluate_scoring_rules(sender, instance, created, **kwargs):
    """
    Evaluates scoring rules on post_save for Lead and Contact.
    """
    model_name = sender._meta.model_name
    ScoringEngine.process_record(instance, model_name)

@receiver(post_save, sender=Lead)
@receiver(post_save, sender=Contact)
@receiver(post_save, sender=Company)
@receiver(post_save, sender=Deal)
def evaluate_territory_assignment(sender, instance, created, **kwargs):
    """
    Evaluates territory assignment rules on post_save.
    """
    model_name = sender._meta.model_name
    TerritoryEngine.process_record(instance, model_name)
