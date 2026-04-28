from rest_framework import serializers
from .models import (
    Pipeline, Stage, Tag, CustomFieldDefinition,
    Company, Contact, Lead, Deal, Note, Activity,
    Territory, AssignmentRule, ScoringRule, AppliedScoringRule
)

class TerritorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Territory
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

class AssignmentRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentRule
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

class StageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stage
        fields = ('id', 'name', 'position', 'win_probability')

class PipelineSerializer(serializers.ModelSerializer):
    stages = StageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Pipeline
        fields = ('id', 'name', 'is_default', 'stages')

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color')

class CustomFieldDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomFieldDefinition
        fields = ('id', 'target_model', 'key', 'label', 'field_type', 'options')

# Helper Mixin for Custom Data validation could go here
# For now, we allow generic dicts

class ContactSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Contact
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

class CompanySerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)

    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

class DealSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    stage_name = serializers.CharField(source='stage.name', read_only=True)

    class Meta:
        model = Deal
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

class NoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.full_name', read_only=True)

    class Meta:
        model = Note
        fields = '__all__'
        read_only_fields = ('tenant', 'author', 'created_at')

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at')

class ScoringRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoringRule
        fields = '__all__'
        read_only_fields = ('tenant', 'created_at', 'updated_at')

class AppliedScoringRuleSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    score_change = serializers.IntegerField(source='rule.score_change', read_only=True)
    
    class Meta:
        model = AppliedScoringRule
        fields = '__all__'
