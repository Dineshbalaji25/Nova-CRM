from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    WorkflowViewSet, WorkflowExecutionViewSet, WorkflowMetadataView,
    BlueprintViewSet, BlueprintStateViewSet, BlueprintTransitionViewSet,
    BlueprintRecordContextViewSet, BlueprintRecordStatusView, BlueprintExecuteTransitionView
)

router = DefaultRouter()
router.register(r'definitions', WorkflowViewSet)
router.register(r'executions', WorkflowExecutionViewSet)
router.register(r'blueprints', BlueprintViewSet, basename='blueprint')
router.register(r'blueprint-states', BlueprintStateViewSet, basename='blueprintstate')
router.register(r'blueprint-transitions', BlueprintTransitionViewSet, basename='blueprinttransition')
router.register(r'blueprint-records', BlueprintRecordContextViewSet, basename='blueprintrecordcontext')

urlpatterns = [
    path('metadata/', WorkflowMetadataView.as_view(), name='workflow_metadata'),
    path('blueprints/record/<str:model_name>/<uuid:record_id>/', BlueprintRecordStatusView.as_view(), name='blueprint_record_status'),
    path('blueprints/transition/', BlueprintExecuteTransitionView.as_view(), name='blueprint_transition'),
] + router.urls
