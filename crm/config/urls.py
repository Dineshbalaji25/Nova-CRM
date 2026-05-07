from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve
import os

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

# Frontend page view
class FrontendPageView(TemplateView):
    def get_template_names(self):
        # Get the page name from URL or default to dashboard
        page = self.kwargs.get('page', 'dashboard')
        return [f'{page}.html']

urlpatterns = [
    # Backend routes
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.api.urls')),
    
    # Wagtail routes
    path('cms/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('docs/', include(wagtail_urls)),
    
    # Frontend routes - Landing page
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    
    # Dashboard and app pages
    path('dashboard', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('contacts', TemplateView.as_view(template_name='contacts.html'), name='contacts'),
    path('companies', TemplateView.as_view(template_name='companies.html'), name='companies'),
    path('deals', TemplateView.as_view(template_name='deals.html'), name='deals'),
    path('tasks', TemplateView.as_view(template_name='tasks.html'), name='tasks'),
    path('workflows', TemplateView.as_view(template_name='workflows.html'), name='workflows'),
    path('scoring-rules', TemplateView.as_view(template_name='scoring_rules.html'), name='scoring_rules'),
    path('settings', TemplateView.as_view(template_name='settings.html'), name='settings'),
    path('billing', TemplateView.as_view(template_name='billing.html'), name='billing'),
    path('audit', TemplateView.as_view(template_name='audit.html'), name='audit'),
    path('team', TemplateView.as_view(template_name='team.html'), name='team'),
    path('products', TemplateView.as_view(template_name='products.html'), name='products'),
    path('quotes', TemplateView.as_view(template_name='quotes.html'), name='quotes'),
    path('sales-orders', TemplateView.as_view(template_name='sales_orders.html'), name='sales_orders'),
    path('invoices', TemplateView.as_view(template_name='invoices.html'), name='invoices'),
    path('blueprints', TemplateView.as_view(template_name='blueprints.html'), name='blueprints'),
    path('campaigns', TemplateView.as_view(template_name='campaigns.html'), name='campaigns'),
    path('webforms', TemplateView.as_view(template_name='webforms.html'), name='webforms'),
    path('dashboards', TemplateView.as_view(template_name='dashboards.html'), name='dashboards'),
    path('reports', TemplateView.as_view(template_name='reports.html'), name='reports'),
    path('territories', TemplateView.as_view(template_name='territories.html'), name='territories'),
    path('roles', TemplateView.as_view(template_name='roles.html'), name='roles'),
    path('profiles', TemplateView.as_view(template_name='profiles.html'), name='profiles'),
    path('portals', TemplateView.as_view(template_name='portals.html'), name='portals'),
    path('calls', TemplateView.as_view(template_name='calls.html'), name='calls'),
    path('emails', TemplateView.as_view(template_name='emails.html'), name='emails'),
    path('login', TemplateView.as_view(template_name='login.html'), name='login'),
    path('register', TemplateView.as_view(template_name='register.html'), name='register'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
