from rest_framework import authentication
from rest_framework import exceptions
from django.utils import timezone
from .models import APIKey, OAuthToken

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

class OAuthTokenAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication for OAuth Access Tokens.
    Expects header: Authorization: Bearer at_...
    """
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        if not auth_header.startswith('Bearer '):
            return None

        parts = auth_header.split(' ')
        if len(parts) != 2:
            return None

        token_value = parts[1]
        
        # Only handle OAuth tokens that start with our prefix 'at_'
        # This allows standard JWT tokens (which also use 'Bearer') to bypass this class 
        # and be handled by JWTAuthentication.
        if not token_value.startswith('at_'):
            return None

        try:
            token_obj = OAuthToken.objects.select_related(
                'application', 'application__organization', 'user'
            ).get(access_token=token_value, is_revoked=False)
        except OAuthToken.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid OAuth token')

        if token_obj.is_expired():
            raise exceptions.AuthenticationFailed('OAuth token has expired')

        # Set tenant_id on request for models/middleware/permissions
        request.tenant_id = str(token_obj.application.organization.id)

        return (token_obj.user, None)

    def authenticate_header(self, request):
        return 'Bearer'

