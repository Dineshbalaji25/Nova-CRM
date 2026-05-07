from rest_framework import serializers
from .models import PhoneIntegration, CallLog, EmailIntegration, EmailMessage, SupportChatMessage

class PhoneIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneIntegration
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

class CallLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallLog
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

class EmailIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailIntegration
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')
        extra_kwargs = {
            'password': {'write_only': True}
        }

class EmailMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailMessage
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at', 'received_at')

class SupportChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportChatMessage
        fields = ('id', 'user', 'is_from_support', 'message', 'is_read', 'created_at')
        read_only_fields = ('id', 'user', 'created_at', 'tenant')
