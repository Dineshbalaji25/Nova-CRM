from django.db import models
from django.conf import settings
from apps.core.models import TenantAwareModel, BaseModel
from apps.crm.models import Lead, Contact, Deal
from encrypted_model_fields.fields import EncryptedCharField

# -----------------------------------------------------------------------------
# Telephony Integration (Twilio / Plivo)
# -----------------------------------------------------------------------------

class PhoneIntegration(TenantAwareModel):
    name = models.CharField(max_length=100) # e.g. "Primary Twilio Account"
    provider = models.CharField(max_length=50, default='twilio')
    account_sid = models.CharField(max_length=255)
    auth_token = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

class CallLog(TenantAwareModel):
    DIRECTION_CHOICES = (
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    )
    STATUS_CHOICES = (
        ('completed', 'Completed'),
        ('missed', 'Missed'),
        ('voicemail', 'Voicemail'),
        ('failed', 'Failed'),
    )

    integration = models.ForeignKey(PhoneIntegration, on_delete=models.SET_NULL, null=True, blank=True)
    external_call_id = models.CharField(max_length=255, blank=True) # e.g. CallSid from Twilio
    
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    from_number = models.CharField(max_length=50)
    to_number = models.CharField(max_length=50)
    
    duration_seconds = models.IntegerField(default=0)
    recording_url = models.URLField(blank=True, null=True)
    
    # Internal relations
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    
    notes = models.TextField(blank=True)

    # NEW: Transcription
    transcript = models.TextField(blank=True)
    transcript_status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('done', 'Done'),
            ('failed', 'Failed'),
        ),
        default='pending'
    )
    
    # NEW: Sentiment Analysis
    sentiment = models.CharField(
        max_length=20,
        choices=(
            ('positive', 'Positive'),
            ('neutral', 'Neutral'),
            ('negative', 'Negative'),
        ),
        blank=True
    )
    sentiment_score = models.FloatField(null=True, blank=True)  # -1.0 to 1.0
    
    # NEW: Key topics/keywords extracted
    key_topics = models.JSONField(default=list, blank=True)  # e.g. ["pricing", "timeline", "objection"]
    
    # NEW: Action items extracted from call
    action_items = models.JSONField(default=list, blank=True)  # e.g. ["Send proposal by Friday", "Schedule demo"]
    
    # NEW: AI summary
    call_summary = models.TextField(blank=True)
    
    transcribed_at = models.DateTimeField(null=True, blank=True)


# -----------------------------------------------------------------------------
# Email IMAP/SMTP Integration
# -----------------------------------------------------------------------------

class EmailIntegration(TenantAwareModel):
    """
    Credentials for syncing emails from an IMAP server (like Zoho Mail, Gmail, Outlook).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email_address = models.EmailField()
    
    imap_server = models.CharField(max_length=255)
    imap_port = models.IntegerField(default=993)
    smtp_server = models.CharField(max_length=255)
    smtp_port = models.IntegerField(default=587)
    
    password = EncryptedCharField(max_length=255) 
    
    is_active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)

class EmailMessage(TenantAwareModel):
    """
    A mirrored email natively stored in the CRM, linked exactly to a Lead/Contact based on the from/to headers.
    """
    integration = models.ForeignKey(EmailIntegration, on_delete=models.CASCADE)
    message_id = models.CharField(max_length=255, db_index=True) # Unique ID from the email server
    
    subject = models.CharField(max_length=500)
    body_text = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    
    from_address = models.EmailField()
    to_addresses = models.TextField() # JSON list or comma separated
    cc_addresses = models.TextField(blank=True)
    
    sent_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)
    
    # Link to entities (Automated logic looks up email addresses from Leads/Contacts)
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')
    deal = models.ForeignKey(Deal, on_delete=models.SET_NULL, null=True, blank=True, related_name='emails')
    
    is_read = models.BooleanField(default=False)

# -----------------------------------------------------------------------------
# Live Support Chat
# -----------------------------------------------------------------------------

class SupportChatMessage(TenantAwareModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_chats')
    is_from_support = models.BooleanField(default=False)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
