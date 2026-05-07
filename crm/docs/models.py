from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel

class APIDocumentationPage(Page):
    intro = RichTextField(blank=True)
    endpoint = models.CharField(max_length=255, help_text="The API endpoint URL (e.g., /api/v1/resource/)")
    method = models.CharField(max_length=10, choices=[
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ], default='GET')
    request_format = RichTextField(blank=True, help_text="Detailed explanation of how the data should be sent, required fields, etc.")
    response_format = RichTextField(blank=True, help_text="Expected response format")

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('endpoint'),
        FieldPanel('method'),
        FieldPanel('request_format'),
        FieldPanel('response_format'),
    ]
