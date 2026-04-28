from django.contrib import admin
from .models import Plan, FeatureEntitlement, Subscription, UsageRecord, BillingInvoice

admin.site.register(Plan)
admin.site.register(FeatureEntitlement)
admin.site.register(Subscription)
admin.site.register(UsageRecord)
admin.site.register(BillingInvoice)
