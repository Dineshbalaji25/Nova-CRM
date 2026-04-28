from django.contrib import admin
from .models import WebhookEndpoint, WebhookEventLog

admin.site.register(WebhookEndpoint)
admin.site.register(WebhookEventLog)
