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
        
        has_membership = OrganizationMember.objects.filter(
            user=request.user,
            organization_id=tenant_id,
            is_active=True
        ).exists()

        if has_membership:
            request.user.current_role = OrganizationMember.objects.get(
                user=request.user, organization_id=tenant_id
            ).role
            return True
        
        return False
