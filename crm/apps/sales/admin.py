from django.contrib import admin
from .models import Product, PriceBook, PriceBookEntry, Quote, QuoteLineItem, SalesOrder, Invoice

admin.site.register(Product)
admin.site.register(PriceBook)
admin.site.register(PriceBookEntry)
admin.site.register(Quote)
admin.site.register(QuoteLineItem)
admin.site.register(SalesOrder)
admin.site.register(Invoice)
