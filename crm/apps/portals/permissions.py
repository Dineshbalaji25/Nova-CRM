from rest_framework import permissions
from .models import PortalMember

class IsPortalUser(permissions.BasePermission):
    """
    Permission that allows access only to portal members.
    The user must have a PortalMember record for the current tenant.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has any portal membership in this organization
        return PortalMember.objects.filter(
            user=request.user, 
            portal__tenant_id=request.tenant_id,
            is_active=True
        ).exists()

class PortalFilterMixin:
    """
    Mixin for ViewSets to automatically filter data for portal users.
    Limits data to records associated with the user's linked Contact or Company.
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # If accessing via portal, filter strictly
        portal_member = PortalMember.objects.filter(
            user=self.request.user,
            portal__tenant_id=self.request.tenant_id,
            is_active=True
        ).select_related('contact').first()
        
        if portal_member:
            contact = portal_member.contact
            model = self.queryset.model
            
            # Filtering logic based on model type
            if hasattr(model, 'contact'):
                queryset = queryset.filter(contact=contact)
            elif hasattr(model, 'primary_contact'):
                queryset = queryset.filter(primary_contact=contact)
            elif hasattr(model, 'company') and contact.company:
                queryset = queryset.filter(company=contact.company)
            elif model._meta.model_name == 'contact':
                queryset = queryset.filter(id=contact.id)
            elif model._meta.model_name == 'invoice':
                # Invoice often links to contact or company
                if hasattr(model, 'contact'):
                    queryset = queryset.filter(contact=contact)
                elif hasattr(model, 'company') and contact.company:
                    queryset = queryset.filter(company=contact.company)
                    
        return queryset
