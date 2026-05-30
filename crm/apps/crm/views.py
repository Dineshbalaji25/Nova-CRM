from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from apps.users.permissions import IsOrganizationMember
from .models import (
    Pipeline, Stage, Tag, CustomFieldDefinition,
    Company, Contact, Lead, Deal, Note, Activity,
    Territory, AssignmentRule, ScoringRule, AppliedScoringRule
)
from .serializers import (
    PipelineSerializer, StageSerializer, TagSerializer, CustomFieldDefinitionSerializer,
    CompanySerializer, ContactSerializer, LeadSerializer, DealSerializer, 
    NoteSerializer, ActivitySerializer, TerritorySerializer, AssignmentRuleSerializer,
    ScoringRuleSerializer, AppliedScoringRuleSerializer
)
from apps.users.rbac import get_visible_user_ids

class BaseTenantViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet ensuring all operations are scoped to the current Tenant.
    """
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    def get_queryset(self):
        model = self.queryset.model
        kwargs = {}
        
        # Check if model supports tenant scoping
        if hasattr(model, 'tenant_id') or hasattr(model, 'tenant'):
            kwargs['tenant_id'] = self.request.tenant_id
            
        # Check if model supports soft delete
        if hasattr(model, 'is_deleted'):
            kwargs['is_deleted'] = False
            
        qs = self.queryset.filter(**kwargs)
        if hasattr(model, 'owner'):
            visible_ids = get_visible_user_ids(self.request.user, self.request.tenant_id)
            if visible_ids is not None:
                qs = qs.filter(owner_id__in=visible_ids)
        return qs

    def perform_create(self, serializer):
        # Automatically inject tenant and owner
        # We try to determine the correct field name (usually 'tenant' or 'organization')
        model = serializer.Meta.model
        save_kwargs = {}
        
        # Determine tenant field name
        tenant_field = None
        if hasattr(model, 'tenant'):
            tenant_field = 'tenant_id'
        elif hasattr(model, 'organization'):
            tenant_field = 'organization_id'
            
        if tenant_field and self.request.tenant_id:
            save_kwargs[tenant_field] = self.request.tenant_id
        
        # Auto-assign ownership if model supports it
        if hasattr(model, 'owner'):
             save_kwargs['owner'] = self.request.user
        if hasattr(model, 'author'):
             save_kwargs['author'] = self.request.user
             
        serializer.save(**save_kwargs)

    def perform_destroy(self, instance):
        # Soft delete
        instance.delete()

# -----------------------------------------------------------------------------
# Metadata ViewSets
# -----------------------------------------------------------------------------

class PipelineViewSet(BaseTenantViewSet):
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer

class StageViewSet(BaseTenantViewSet):
    queryset = Stage.objects.all()
    serializer_class = StageSerializer
    filterset_fields = ['pipeline']

class TagViewSet(BaseTenantViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class CustomFieldDefinitionViewSet(BaseTenantViewSet):
    queryset = CustomFieldDefinition.objects.all()
    serializer_class = CustomFieldDefinitionSerializer
    filterset_fields = ['target_model']

# -----------------------------------------------------------------------------
# Core Entity ViewSets
# -----------------------------------------------------------------------------

class CompanyViewSet(BaseTenantViewSet):
    queryset = Company.objects.select_related('owner').prefetch_related('tags', 'territories', 'contacts', 'deals')
    serializer_class = CompanySerializer
    search_fields = ['name', 'domain']
    filterset_fields = ['owner', 'industry']

from rest_framework.decorators import action
from rest_framework.response import Response
import csv
import io

class ContactViewSet(BaseTenantViewSet):
    queryset = Contact.objects.select_related('company', 'owner').prefetch_related('tags', 'territories')
    serializer_class = ContactSerializer
    search_fields = ['first_name', 'last_name', 'email']
    filterset_fields = ['company', 'owner']

    @action(detail=False, methods=['post'], url_path='import-csv')
    def import_csv(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=400)
        
        try:
            decoded_file = file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            contacts_to_create = []
            for row in reader:
                # Basic mapping: first_name, last_name, email, phone
                contact = Contact(
                    tenant_id=request.tenant_id,
                    owner=request.user,
                    first_name=row.get('first_name', 'Imported'),
                    last_name=row.get('last_name', ''),
                    email=row.get('email', ''),
                    phone=row.get('phone', ''),
                )
                contacts_to_create.append(contact)
            
            Contact.objects.bulk_create(contacts_to_create)
            return Response({'message': f'Successfully imported {len(contacts_to_create)} contacts'})
        except Exception as e:
            return Response({'error': str(e)}, status=400)

class LeadViewSet(BaseTenantViewSet):
    queryset = Lead.objects.select_related('owner', 'converted_contact').prefetch_related('tags', 'territories')
    serializer_class = LeadSerializer
    search_fields = ['first_name', 'last_name', 'company_name']
    filterset_fields = ['status', 'owner']

    @action(detail=True, methods=['post'])
    def convert(self, request, pk=None):
        lead = self.get_object()
        create_deal = request.data.get('create_deal', False)
        deal_data = request.data.get('deal_data', {})
        
        from .services import LeadConversionService
        try:
            result = LeadConversionService.convert(lead, create_deal=create_deal, deal_data=deal_data)
            return Response(result)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

class DealViewSet(BaseTenantViewSet):
    queryset = Deal.objects.select_related(
        'pipeline', 'stage', 'company', 'primary_contact', 'owner'
    ).prefetch_related('tags', 'territories')
    serializer_class = DealSerializer
    search_fields = ['title']
    filterset_fields = ['pipeline', 'stage', 'owner', 'company']

class NoteViewSet(BaseTenantViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    filterset_fields = ['contact', 'deal', 'company', 'lead']

class ActivityViewSet(BaseTenantViewSet):
    queryset = Activity.objects.select_related('contact', 'company', 'deal', 'completed_by')
    serializer_class = ActivitySerializer
    filterset_fields = ['contact', 'deal', 'company', 'activity_type', 'is_completed']

# -----------------------------------------------------------------------------
# Territory & Assignment ViewSets
# -----------------------------------------------------------------------------

class TerritoryViewSet(BaseTenantViewSet):
    queryset = Territory.objects.all()
    serializer_class = TerritorySerializer
    search_fields = ['name']

class AssignmentRuleViewSet(BaseTenantViewSet):
    queryset = AssignmentRule.objects.all()
    serializer_class = AssignmentRuleSerializer
    filterset_fields = ['target_model', 'is_active']

# -----------------------------------------------------------------------------
# Scoring ViewSets
# -----------------------------------------------------------------------------

class ScoringRuleViewSet(BaseTenantViewSet):
    queryset = ScoringRule.objects.all()
    serializer_class = ScoringRuleSerializer
    filterset_fields = ['target_model', 'is_active']

from rest_framework.views import APIView

class ScoreBreakdownView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def get(self, request, model_name, record_id):
        if model_name not in ['lead', 'contact']:
            return Response({"error": "Invalid model. Scoring only applies to lead and contact."}, status=400)
            
        applied_rules = AppliedScoringRule.objects.filter(
            record_model=model_name,
            record_id=record_id
        ).select_related('rule')
        
        serializer = AppliedScoringRuleSerializer(applied_rules, many=True)
        
        # Get total score dynamically from the model
        from django.apps import apps
        try:
            Model = apps.get_model('crm', model_name)
            record = Model.objects.get(id=record_id, tenant_id=request.tenant_id)
            total_score = record.score
        except Model.DoesNotExist:
            return Response({"error": "Record not found"}, status=404)
            
        return Response({
            "total_score": total_score,
            "applied_rules": serializer.data
        })
