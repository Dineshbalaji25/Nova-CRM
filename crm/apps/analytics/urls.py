from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportViewSet, DashboardViewSet, DashboardComponentViewSet
)

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'dashboards', DashboardViewSet, basename='dashboard')
router.register(r'dashboard-components', DashboardComponentViewSet, basename='dashboardcomponent')

app_name = 'analytics'

urlpatterns = [
    path('', include(router.urls)),
]
