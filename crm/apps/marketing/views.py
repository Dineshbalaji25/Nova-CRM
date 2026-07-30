from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Campaign, CampaignMember, WebForm, WebFormField
from .serializers import (
    CampaignSerializer, CampaignMemberSerializer, 
    WebFormSerializer, WebFormFieldSerializer
)
from apps.crm.views import BaseTenantViewSet

class CampaignViewSet(BaseTenantViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'status']

class CampaignMemberViewSet(BaseTenantViewSet):
    queryset = CampaignMember.objects.select_related('lead', 'contact', 'campaign').all()
    serializer_class = CampaignMemberSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['campaign', 'status', 'lead', 'contact']

class WebFormViewSet(BaseTenantViewSet):
    queryset = WebForm.objects.prefetch_related('fields').all()
    serializer_class = WebFormSerializer

class WebFormFieldViewSet(viewsets.ModelViewSet):
    queryset = WebFormField.objects.all()
    serializer_class = WebFormFieldSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['webform']

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from django.db import transaction

# Allowlists for web form field mapping — prevents mass assignment attacks
LEAD_SAFE_FIELDS = frozenset({
    'first_name', 'last_name', 'email', 'phone',
    'company_name', 'source', 'title',
})
CONTACT_SAFE_FIELDS = frozenset({
    'first_name', 'last_name', 'email', 'phone',
})

class WebFormSubmitView(APIView):
    """
    Public endpoint for submitting webforms.
    Maps to /api/marketing/forms/{slug}/submit/
    """
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request, slug):
        webform = get_object_or_404(WebForm, slug=slug, is_active=True)
        data = request.data

        # Basic mapping logic based on target_model
        # For a full implementation, we'd map fields according to WebFormField records
        
        target_kwargs = {
            'tenant_id': webform.tenant_id,
            'owner': webform.assign_to,
        }
        
        safe_fields = LEAD_SAFE_FIELDS if webform.target_model == 'lead' else CONTACT_SAFE_FIELDS
        custom_data = {}
        for key, value in data.items():
            if key in safe_fields:
                target_kwargs[key] = value
            else:
                custom_data[key] = value
                
        if custom_data:
            target_kwargs['custom_data'] = custom_data

        if webform.target_model == 'lead':
            from apps.crm.models import Lead
            Lead.objects.create(**target_kwargs)
        else:
            from apps.crm.models import Contact
            Contact.objects.create(**target_kwargs)

        if webform.return_url:
            return Response({"success": True, "redirect_url": webform.return_url})
        return Response({"success": True, "message": "Form submitted successfully."})
