import logging
from celery import shared_task
from django.utils import timezone
from .models import Deal
from apps.crm.models import AINextAction
from django.conf import settings
import openai

logger = logging.getLogger(__name__)

@shared_task
def generate_ai_suggestions_for_all_deals():
    """
    Generate AI suggestions for open deals periodically.
    """
    deals = Deal.objects.filter(stage__pipeline__is_default=True, stage__win_probability__lt=100)
    for deal in deals:
        try:
            client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENROUTER_API_KEY
            )
            
            prompt = f"Analyze deal '{deal.title}' for amount {deal.amount}. What should the next action be to close it?"
            
            analysis_response = client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a sales assistant. Give a short next action recommendation for this deal."},
                    {"role": "user", "content": prompt}
                ],
                extra_headers={
                    "HTTP-Referer": "https://novacrm.io",
                    "X-Title": "Nova CRM",
                }
            )
            
            suggestion = analysis_response.choices[0].message.content
            
            AINextAction.objects.create(
                tenant=deal.tenant,
                target_model='deal',
                target_id=deal.id,
                suggestion=suggestion,
                confidence_score=0.85
            )
        except Exception as e:
            logger.error(f"Error generating AI suggestion for deal {deal.id}: {str(e)}")
    
    return f"Triggered AI suggestions for {deals.count()} deals"
