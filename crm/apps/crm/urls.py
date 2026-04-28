from rest_framework.routers import DefaultRouter
from .views import (
    PipelineViewSet, TagViewSet, CustomFieldDefinitionViewSet,
    CompanyViewSet, ContactViewSet, LeadViewSet, DealViewSet,
    NoteViewSet, ActivityViewSet, TerritoryViewSet, AssignmentRuleViewSet,
    ScoringRuleViewSet, ScoreBreakdownView
)

router = DefaultRouter()

# Meta
router.register(r'pipelines', PipelineViewSet)
router.register(r'tags', TagViewSet)
router.register(r'custom-fields', CustomFieldDefinitionViewSet)

# Core
router.register(r'companies', CompanyViewSet)
router.register(r'contacts', ContactViewSet)
router.register(r'leads', LeadViewSet)
router.register(r'deals', DealViewSet)

# Interactions
router.register(r'notes', NoteViewSet)
router.register(r'activities', ActivityViewSet)

# Territories
router.register(r'territories', TerritoryViewSet)
router.register(r'assignment-rules', AssignmentRuleViewSet)

# Scoring
router.register(r'scoring-rules', ScoringRuleViewSet)

from django.urls import path

urlpatterns = [
    path('scoring/<str:model_name>/<uuid:record_id>/breakdown/', ScoreBreakdownView.as_view(), name='score_breakdown'),
] + router.urls
