from django.contrib import admin
from .models import PhoneIntegration, CallLog, EmailIntegration, EmailMessage

admin.site.register(PhoneIntegration)
admin.site.register(CallLog)
admin.site.register(EmailIntegration)
admin.site.register(EmailMessage)
