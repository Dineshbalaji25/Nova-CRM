from django.contrib import admin
from .models import Report, Dashboard, DashboardComponent

admin.site.register(Report)
admin.site.register(Dashboard)
admin.site.register(DashboardComponent)
