from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404

from .models import Organization, OrganizationMember, APIKey, Profile, Role
from .serializers import (
    UserSerializer, 
    RegisterRequestSerializer, 
    OrganizationSerializer,
    APIKeySerializer,
    ProfileSerializer,
    RoleSerializer
)
from rest_framework import viewsets

class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not hasattr(self.request, 'tenant_id') or not self.request.tenant_id:
            return Profile.objects.none()
        return Profile.objects.filter(organization_id=self.request.tenant_id)

    def perform_create(self, serializer):
        serializer.save(organization_id=self.request.tenant_id)

class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not hasattr(self.request, 'tenant_id') or not self.request.tenant_id:
            return Role.objects.none()
        return Role.objects.filter(organization_id=self.request.tenant_id)

    def perform_create(self, serializer):
        serializer.save(organization_id=self.request.tenant_id)

class APIKeyViewSet(viewsets.ModelViewSet):
    serializer_class = APIKeySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not hasattr(self.request, 'tenant_id') or not self.request.tenant_id:
            return APIKey.objects.none()
        return APIKey.objects.filter(organization_id=self.request.tenant_id)

    def perform_create(self, serializer):
        serializer.save(organization_id=self.request.tenant_id)

User = get_user_model()

class RegisterView(APIView):
    """
    Onboarding: Registers a User AND creates their first Organization (Tenant).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            with transaction.atomic():
                # 1. Create User
                if User.objects.filter(email=data['email']).exists():
                   return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
                
                user = User.objects.create_user(
                    email=data['email'],
                    password=data['password'],
                    full_name=data.get('full_name', '')
                )

                # 2. Create Organization
                from django.utils.text import slugify
                base_slug = slugify(data['organization_name'])
                # Simple slug uniqueness for MVP
                org = Organization.objects.create(
                    name=data['organization_name'],
                    slug=f"{base_slug}-{user.id.hex[:4]}"
                )

                # 3. Link them as Owner
                OrganizationMember.objects.create(
                    user=user,
                    organization=org,
                    role='owner'
                )
                
                user.default_organization = org
                user.save()

            # 4. Generate Tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "user": UserSerializer(user).data,
                "tenant_id": str(org.id),
                "organization": OrganizationSerializer(org).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MyOrganizationsView(generics.ListAPIView):
    """
    List all organizations the authenticated user belongs to.
    This is a 'Global' endpoint (does not require X-Tenant-ID).
    """
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return orgs via Membership
        return Organization.objects.filter(
            memberships__user=self.request.user,
            memberships__is_active=True
        )

class SwitchTenantView(APIView):
    """
    Returns a short-lived access token scoped to a specific Tenant.
    (Optional implementation if using strict token scopes later).
    For Phase 2, we just verify access.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        tenant_id = request.data.get('tenant_id')
        member = get_object_or_404(
            OrganizationMember, 
            user=request.user, 
            organization_id=tenant_id,
            is_active=True
        )
        
        # In a real impl, we would embed the 'tid' claim into a new JWT here.
        return Response({
            "message": f"Switched to {member.organization.name}",
            "role": member.role
        })
