from rest_framework import serializers
from .models import WebhookEndpoint, WebhookEventLog

class WebhookEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEndpoint
        fields = ('id', 'url', 'description', 'secret', 'events', 'status', 'created_at')
        read_only_fields = ('secret', 'status', 'created_at')

class WebhookEventLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEventLog
        fields = '__all__'
