from django.urls import path
from .stats_views import DashboardStatsView as DashboardStatsViewNew

urlpatterns = [
    path('dashboard/', DashboardStatsViewNew.as_view(), name='dashboard-stats'),
]
