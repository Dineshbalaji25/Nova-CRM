from rest_framework import authentication
from rest_framework import exceptions
from django.utils import timezone
from .models import APIKey

class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication for API Keys.
    Expects header: Authorization: Api-Key sk_live_...
    """
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        if not auth_header.startswith('Api-Key '):
            return None

        key_value = auth_header.split(' ')[1]
        try:
            api_key = APIKey.objects.select_related('organization').get(key=key_value, is_active=True)
        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API Key')

        # Find an owner to represent the API request
        owner_membership = api_key.organization.memberships.filter(role='owner').first()
        if not owner_membership:
            # Fallback to any member if no owner
            owner_membership = api_key.organization.memberships.first()
            
        if not owner_membership:
            raise exceptions.AuthenticationFailed('Organization has no active members')

        # Update last used
        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=['last_used_at'])

        # Set tenant_id on request for models/middleware
        request.tenant_id = str(api_key.organization.id)
        
        return (owner_membership.user, None)
