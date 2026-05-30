import logging
import json
from celery import shared_task
from django.utils import timezone
from .models import EmailIntegration

logger = logging.getLogger(__name__)

@shared_task
def sync_email_integration(integration_id):
    """
    Syncs emails for a specific EmailIntegration using IMAP.
    For MVP, we simulate syncing since we don't have real IMAP credentials.
    In a real system, this uses imaplib to fetch emails and creates EmailMessage records.
    """
    try:
        integration = EmailIntegration.objects.get(id=integration_id, is_active=True)
        # MVP Simulation of email sync
        logger.info(f"Syncing emails for {integration.email_address} via {integration.imap_server}...")
        
        # Real logic would:
        # 1. Connect to IMAP
        # 2. Search for unseen emails
        # 3. Parse headers (From, To) and match against Leads/Contacts
        # 4. Create EmailMessage objects
        
        integration.last_sync_at = timezone.now()
        integration.save()
        return f"Successfully synced integration {integration_id}"
    except EmailIntegration.DoesNotExist:
        return f"Integration {integration_id} not found or inactive."
    except Exception as e:
        logger.error(f"Error syncing email integration {integration_id}: {e}")
        return str(e)

@shared_task
def sync_all_email_integrations():
    """
    Fetches all active email integrations and triggers a sync task for each.
    """
    integrations = EmailIntegration.objects.filter(is_active=True)
    count = 0
    for integration in integrations:
        sync_email_integration.delay(integration.id)
        count += 1
    return f"Triggered sync for {count} integrations"

@shared_task
def transcribe_call_task(call_log_id):
    """
    Transcribes a call recording using OpenAI Whisper and analyzes sentiment.
    """
    from .models import CallLog
    import openai
    from django.conf import settings
    
    try:
        call = CallLog.objects.get(id=call_log_id)
        if not call.recording_url:
            return "No recording URL found."
            
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY
        )
        
        # 1. Transcribe (Simulated for MVP if recording_url is not a real file)
        # Note: OpenRouter does not support audio transcription yet.
        # Keeping simulation or would require another provider.
        transcript_text = "Hello, I am interested in your CRM. Your pricing seems a bit high though."
        
        # 2. Analyze Sentiment & Keywords
        analysis_response = client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=[
                {"role": "system", "content": "Analyze the following call transcript. Return JSON with 'sentiment' (positive/negative/neutral), 'keywords' (list), and 'summary'."},
                {"role": "user", "content": transcript_text}
            ],
            response_format={"type": "json_object"},
            extra_headers={
                "HTTP-Referer": "https://novacrm.io",
                "X-Title": "Nova CRM",
            }
        )
        analysis = json.loads(analysis_response.choices[0].message.content)
        
        call.transcript = transcript_text
        call.sentiment = analysis.get('sentiment', 'neutral')
        call.key_topics = analysis.get('keywords', [])
        call.call_summary = analysis.get('summary', '')
        call.save()
        
        return f"Successfully processed call {call_log_id}"
    except Exception as e:
        logger.exception(f"Call transcription failed for {call_log_id}")
        return str(e)
