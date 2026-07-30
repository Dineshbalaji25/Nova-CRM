from rest_framework import permissions

class IsOrganizationMember(permissions.BasePermission):
    """
    Validates that the logged-in User is a member of the requested Tenant (X-Tenant-ID).
    Example:
        Users can only see data if they belong to organization X.
    """

    def has_permission(self, request, view):
        # 1. Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. Check if Tenant ID is present (Middleware should have captured it)
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            # If no tenant ID provided, deny unless it's a generic "list my tenants" endpoint
            # For strictness, we require it for most views.
            return False

        # 3. Validation Logic
        # We check if the relationship exists in the DB.
        # Ideally cached (Phase 8: Add Redis caching here)
        from apps.users.models import OrganizationMember
        
        membership = OrganizationMember.objects.filter(
            user=request.user,
            organization_id=tenant_id,
            is_active=True
        ).first()

        if membership:
            request.user.current_role = membership.role
            return True
        
        return False


class HasOAuthScope(permissions.BasePermission):
    """
    Enforces OAuth scope restrictions on token-authenticated requests.
    
    Usage on a ViewSet:
        permission_classes = [IsAuthenticated, HasOAuthScope]
        required_scopes = ['NovaCRM.modules.contacts.READ']
    
    If the request was not made with an OAuth token (no request.oauth_scopes),
    this permission defers to other permission classes (passes through).
    """
    required_scopes = []

    def has_permission(self, request, view):
        # Only enforce if this is an OAuth token request
        if not hasattr(request, 'oauth_scopes'):
            return True  # Non-OAuth request — let other permissions decide

        # NovaCRM.modules.ALL grants unrestricted access
        if 'NovaCRM.modules.ALL' in request.oauth_scopes:
            return True

        # Check view-level required_scopes attribute
        view_scopes = getattr(view, 'required_scopes', self.required_scopes)
        if not view_scopes:
            return True  # No specific scopes required

        # Grant access if any required scope is present
        return any(scope in request.oauth_scopes for scope in view_scopes)
