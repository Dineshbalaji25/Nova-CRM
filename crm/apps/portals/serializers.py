from rest_framework import serializers
from .models import Portal, PortalMember
from apps.crm.serializers import ContactSerializer

class PortalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portal
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

class PortalMemberSerializer(serializers.ModelSerializer):
    contact_details = ContactSerializer(source='contact', read_only=True)
    portal_name = serializers.CharField(source='portal.name', read_only=True)
    
    class Meta:
        model = PortalMember
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
