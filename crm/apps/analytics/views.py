from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Report, Dashboard, DashboardComponent
from .serializers import (
    ReportSerializer, DashboardSerializer, DashboardComponentSerializer
)
from apps.crm.views import BaseTenantViewSet
from .services import ReportExecutor
from rest_framework.decorators import action
from rest_framework.response import Response
import csv
from django.http import HttpResponse

class ReportViewSet(BaseTenantViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'target_model']

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        report = self.get_object()
        date_range = request.data.get('date_range')
        
        try:
            data = ReportExecutor.execute(report, request.tenant_id, date_range)
            return Response({
                "report_name": report.name,
                "data": data
            })
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        report = self.get_object()
        try:
            data = ReportExecutor.execute(report, request.tenant_id)
            
            if not data:
                return Response({"message": "No data to export"}, status=200)
                
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{report.name}.csv"'
            
            writer = csv.DictWriter(response, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
            return response
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class DashboardViewSet(BaseTenantViewSet):
    queryset = Dashboard.objects.prefetch_related('components').all()
    serializer_class = DashboardSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']

    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        dashboard = self.get_object()
        components_data = []
        
        for component in dashboard.components.all():
            try:
                data = ReportExecutor.execute(component.report, request.tenant_id)
                components_data.append({
                    "id": component.id,
                    "name": component.name,
                    "chart_type": component.chart_type,
                    "data": data
                })
            except Exception as e:
                components_data.append({
                    "id": component.id,
                    "name": component.name,
                    "error": str(e)
                })
                
        return Response({
            "dashboard_name": dashboard.name,
            "components": components_data
        })

class DashboardComponentViewSet(viewsets.ModelViewSet):
    queryset = DashboardComponent.objects.all()
    serializer_class = DashboardComponentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['dashboard', 'report']
