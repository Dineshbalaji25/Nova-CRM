from django.contrib import admin
from .models import Pipeline, Stage, Tag, CustomFieldDefinition, Company, Contact, Lead, Deal, Note, Activity, Territory, AssignmentRule

admin.site.register(Pipeline)
admin.site.register(Stage)
admin.site.register(Tag)
admin.site.register(CustomFieldDefinition)
admin.site.register(Company)
admin.site.register(Contact)
admin.site.register(Lead)
admin.site.register(Deal)
admin.site.register(Note)
admin.site.register(Activity)
admin.site.register(Territory)
admin.site.register(AssignmentRule)
