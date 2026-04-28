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
