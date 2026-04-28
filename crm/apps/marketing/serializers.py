from rest_framework import serializers
from .models import Campaign, CampaignMember, WebForm, WebFormField

class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

class CampaignMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignMember
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

class WebFormFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebFormField
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class WebFormSerializer(serializers.ModelSerializer):
    fields = WebFormFieldSerializer(many=True, read_only=True)
    
    class Meta:
        model = WebForm
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')
