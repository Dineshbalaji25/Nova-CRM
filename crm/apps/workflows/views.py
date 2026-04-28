from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.users.permissions import IsOrganizationMember
from apps.crm.views import BaseTenantViewSet
from .models import Workflow, WorkflowExecution
from .serializers import WorkflowSerializer, WorkflowExecutionSerializer
from .engine import ActionRegistry

class WorkflowMetadataView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        triggers = [
            {"key": "contact.created", "label": "When a Contact is Created"},
            {"key": "deal.updated", "label": "When a Deal is Updated"},
            {"key": "lead.assigned", "label": "When a Lead is Assigned"},
        ]
        actions = [
            {"key": "utils.log", "label": "Log to Console (System)"},
            {"key": "crm.update_record", "label": "Update CRM Record"},
            {"key": "email.send", "label": "Send Email Notification"},
        ]
        return Response({
            "triggers": triggers,
            "actions": actions
        })

class WorkflowViewSet(BaseTenantViewSet):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer

class WorkflowExecutionViewSet(BaseTenantViewSet):
    queryset = WorkflowExecution.objects.all()
    serializer_class = WorkflowExecutionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember] 
    http_method_names = ['get', 'head', 'options']

from .models import Blueprint, BlueprintState, BlueprintTransition, BlueprintRecordContext
from .serializers import (
    BlueprintSerializer, BlueprintStateSerializer, 
    BlueprintTransitionSerializer, BlueprintRecordContextSerializer
)

class BlueprintViewSet(BaseTenantViewSet):
    queryset = Blueprint.objects.prefetch_related('states', 'transitions').all()
    serializer_class = BlueprintSerializer

class BlueprintStateViewSet(viewsets.ModelViewSet):
    queryset = BlueprintState.objects.all()
    serializer_class = BlueprintStateSerializer

class BlueprintTransitionViewSet(viewsets.ModelViewSet):
    queryset = BlueprintTransition.objects.all()
    serializer_class = BlueprintTransitionSerializer

class BlueprintRecordContextViewSet(BaseTenantViewSet):
    queryset = BlueprintRecordContext.objects.select_related('blueprint', 'current_state').all()
    serializer_class = BlueprintRecordContextSerializer

from .services import BlueprintService

class BlueprintRecordStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def get(self, request, model_name, record_id):
        from django.apps import apps
        try:
            Model = apps.get_model('crm', model_name)
            instance = Model.objects.get(id=record_id)
            
            transitions = BlueprintService.get_available_transitions(instance, model_name)
            return Response({"available_transitions": transitions})
        except Model.DoesNotExist:
            return Response({"error": "Record not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class BlueprintExecuteTransitionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def post(self, request):
        model_name = request.data.get('model_name')
        record_id = request.data.get('record_id')
        transition_id = request.data.get('transition_id')
        context_data = request.data.get('context_data', {})
        
        from django.apps import apps
        try:
            Model = apps.get_model('crm', model_name)
            instance = Model.objects.get(id=record_id)
            
            result = BlueprintService.execute_transition(instance, model_name, transition_id, context_data)
            if result.get("success"):
                return Response(result)
            return Response(result, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
