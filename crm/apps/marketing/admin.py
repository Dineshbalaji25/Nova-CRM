from django.contrib import admin
from .models import Campaign, CampaignMember, WebForm, WebFormField

admin.site.register(Campaign)
admin.site.register(CampaignMember)
admin.site.register(WebForm)
admin.site.register(WebFormField)
