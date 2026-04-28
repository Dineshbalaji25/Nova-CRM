from django.contrib import admin
from .models import Organization, User, Profile, Role, OrganizationMember, APIKey

admin.site.register(Organization)
admin.site.register(User)
admin.site.register(Profile)
admin.site.register(Role)
admin.site.register(OrganizationMember)
admin.site.register(APIKey)
