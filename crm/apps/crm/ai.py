import logging
import json
from django.conf import settings
from .models import AINextAction, Lead, Deal, Note, Activity
import openai

logger = logging.getLogger(__name__)

class AISuggestionService:
    @classmethod
    def generate_suggestion(cls, target_model, target_id, tenant_id):
        """
        Uses OpenAI (or Anthropic) to analyze record history and suggest next steps.
        """
        try:
            if target_model == 'lead':
                instance = Lead.objects.get(id=target_id, tenant_id=tenant_id)
                context_name = f"{instance.first_name} {instance.last_name} from {instance.company_name}"
            else:
                instance = Deal.objects.get(id=target_id, tenant_id=tenant_id)
                context_name = instance.title
                
            # Gather history
            notes = list(Note.objects.filter(**{target_model: instance}).values_list('body', flat=True)[:5])
            activities = list(Activity.objects.filter(**{target_model: instance}).values('activity_type', 'subject', 'body', 'occurred_at')[:5])
            
            history_summary = f"Record: {context_name}\n"
            history_summary += f"Status: {getattr(instance, 'status', 'N/A')}\n"
            history_summary += "Recent Notes:\n" + "\n".join(notes) + "\n"
            history_summary += "Recent Activities:\n" + json.dumps(activities, default=str)
            
            # Call AI
            client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENROUTER_API_KEY
            )
            response = client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a senior sales assistant. Analyze the CRM record history and suggest the single best next action. Return JSON with 'suggestion', 'reasoning', and 'confidence' (0-1)."},
                    {"role": "user", "content": history_summary}
                ],
                response_format={"type": "json_object"},
                extra_headers={
                    "HTTP-Referer": "https://novacrm.io", # Optional, for OpenRouter rankings
                    "X-Title": "Nova CRM", # Optional
                }
            )
            
            ai_data = json.loads(response.choices[0].message.content)
            
            # Save suggestion
            suggestion = AINextAction.objects.create(
                tenant_id=tenant_id,
                target_model=target_model,
                target_id=target_id,
                suggestion=ai_data.get('suggestion'),
                reasoning=ai_data.get('reasoning'),
                confidence_score=ai_data.get('confidence', 0.5)
            )
            
            return suggestion
            
        except Exception as e:
            logger.exception(f"AI Suggestion failed for {target_model} {target_id}")
            return None
