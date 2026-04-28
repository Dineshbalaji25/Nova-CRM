from rest_framework import serializers
from .models import Report, Dashboard, DashboardComponent

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

class DashboardComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardComponent
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class DashboardSerializer(serializers.ModelSerializer):
    components = DashboardComponentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Dashboard
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')
