import requests
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

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


def _create_organization_for_user(user, organization_name):
    base_slug = slugify(organization_name) or 'organization'
    org = Organization.objects.create(
        name=organization_name,
        slug=f"{base_slug}-{user.id.hex[:4]}"
    )
    OrganizationMember.objects.create(
        user=user,
        organization=org,
        role='owner'
    )
    user.default_organization = org
    user.save(update_fields=['default_organization'])
    return org


def _auth_response_for_user(user):
    refresh = RefreshToken.for_user(user)
    response_data = {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'email': user.email,
            'full_name': user.full_name,
        }
    }

    if user.default_organization:
        response_data['tenant_id'] = str(user.default_organization.id)
        response_data['organization_name'] = user.default_organization.name
    else:
        first_membership = user.memberships.filter(is_active=True).first()
        if first_membership:
            response_data['tenant_id'] = str(first_membership.organization.id)
            response_data['organization_name'] = first_membership.organization.name

    return response_data

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
                org = _create_organization_for_user(user, data['organization_name'])

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


class GoogleAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        id_token = request.data.get('id_token')
        organization_name = (request.data.get('organization_name') or '').strip()
        if not id_token:
            return Response({'error': 'id_token is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not settings.GOOGLE_CLIENT_ID:
            return Response(
                {'error': 'Google login is not configured'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        try:
            token_info_response = requests.get(
                'https://oauth2.googleapis.com/tokeninfo',
                params={'id_token': id_token},
                timeout=5
            )
        except requests.RequestException:
            return Response({'error': 'Unable to verify Google token'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if token_info_response.status_code != 200:
            return Response({'error': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)

        token_info = token_info_response.json()
        email = token_info.get('email')
        audience = token_info.get('aud')
        raw_email_verified = token_info.get('email_verified', False)
        email_verified = raw_email_verified is True or str(raw_email_verified).lower() == 'true'

        if not email or not email_verified:
            return Response({'error': 'Google account email must be verified'}, status=status.HTTP_400_BAD_REQUEST)

        if audience != settings.GOOGLE_CLIENT_ID:
            return Response({'error': 'Invalid Google token audience'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if user is None and not organization_name:
            return Response(
                {'error': 'organization_name is required to register with Google'},
                status=status.HTTP_400_BAD_REQUEST
            )

        full_name = (token_info.get('name') or '').strip()
        if not full_name:
            given_name = (token_info.get('given_name') or '').strip()
            family_name = (token_info.get('family_name') or '').strip()
            full_name = f'{given_name} {family_name}'.strip()

        created = False
        with transaction.atomic():
            if user is None:
                user = User.objects.create_user(
                    email=email,
                    password=None,
                    full_name=full_name
                )
                _create_organization_for_user(user, organization_name)
                created = True
            elif full_name and not user.full_name:
                user.full_name = full_name
                user.save(update_fields=['full_name'])

            if not user.default_organization:
                first_membership = user.memberships.filter(is_active=True).first()
                if first_membership:
                    user.default_organization = first_membership.organization
                    user.save(update_fields=['default_organization'])

        auth_data = _auth_response_for_user(user)
        auth_data['created'] = created
        return Response(auth_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

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
