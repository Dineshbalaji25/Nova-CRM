from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CampaignViewSet, CampaignMemberViewSet, 
    WebFormViewSet, WebFormFieldViewSet
)

router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'campaign-members', CampaignMemberViewSet, basename='campaignmember')
router.register(r'webforms', WebFormViewSet, basename='webform')
router.register(r'webform-fields', WebFormFieldViewSet, basename='webformfield')

app_name = 'marketing'

urlpatterns = [
    path('', include(router.urls)),
]
