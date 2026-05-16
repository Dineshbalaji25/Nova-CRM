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

from .models import Organization, OrganizationMember, APIKey, Profile, Role, OAuthApplication, OAuthToken
from .models import OAUTH_SCOPE_CHOICES, default_oauth_scopes
from .serializers import (
    UserSerializer, 
    RegisterRequestSerializer, 
    OrganizationSerializer,
    APIKeySerializer,
    ProfileSerializer,
    RoleSerializer,
    OAuthApplicationSerializer,
    OAuthTokenSerializer
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

class OAuthApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = OAuthApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not hasattr(self.request, 'tenant_id') or not self.request.tenant_id:
            return OAuthApplication.objects.none()
        return OAuthApplication.objects.filter(organization_id=self.request.tenant_id)

    def perform_create(self, serializer):
        serializer.save(organization_id=self.request.tenant_id)


def _parse_scope_list(scope_value):
    if not scope_value:
        return []
    normalized = str(scope_value).replace(",", " ").split()
    return list(dict.fromkeys(scope for scope in normalized if scope))


class OAuthScopeListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"scopes": list(OAUTH_SCOPE_CHOICES)})

class TokenExchangeView(APIView):
    """
    Zoho-style Token Exchange Endpoint.
    Supports grant_type=authorization_code and grant_type=refresh_token.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        grant_type = request.data.get('grant_type')
        client_id = request.data.get('client_id')
        client_secret = request.data.get('client_secret')
        requested_scopes = _parse_scope_list(request.data.get('scope'))

        app = get_object_or_404(OAuthApplication, client_id=client_id, client_secret=client_secret, is_active=True)
        app_scopes = app.allowed_scopes or default_oauth_scopes()

        if grant_type == 'authorization_code':
            code = request.data.get('code')
            # For simplicity in this demo, 'code' is just a valid User ID or a special temporary token.
            # In a real app, you'd have an OAuthCode model.
            # Here we assume the 'code' was generated for the user.
            user = get_object_or_404(User, id=code)
            if requested_scopes:
                forbidden_scopes = [scope for scope in requested_scopes if scope not in app_scopes]
                if forbidden_scopes:
                    return Response(
                        {"error": "invalid_scope", "details": f"Scopes not allowed: {', '.join(forbidden_scopes)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                token_scopes = requested_scopes
            else:
                token_scopes = app_scopes

            return self._generate_tokens(app, user, token_scopes)

        elif grant_type == 'refresh_token':
            refresh_token = request.data.get('refresh_token')
            token_obj = get_object_or_404(OAuthToken, refresh_token=refresh_token, application=app, is_revoked=False)
            existing_scopes = _parse_scope_list(token_obj.scopes)
            if requested_scopes:
                invalid_refresh_scopes = [scope for scope in requested_scopes if scope not in existing_scopes or scope not in app_scopes]
                if invalid_refresh_scopes:
                    return Response(
                        {"error": "invalid_scope", "details": f"Refresh token cannot be used for: {', '.join(invalid_refresh_scopes)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                token_scopes = requested_scopes
            else:
                token_scopes = existing_scopes or app_scopes

            return self._generate_tokens(app, token_obj.user, token_scopes)

        return Response({"error": "invalid_grant_type"}, status=status.HTTP_400_BAD_REQUEST)

    def _generate_tokens(self, app, user, scopes):
        import uuid
        from django.utils import timezone
        from datetime import timedelta
        
        access_token = f"at_{uuid.uuid4().hex}"
        refresh_token = f"rt_{uuid.uuid4().hex}"
        expires_at = timezone.now() + timedelta(hours=1)

        token_obj = OAuthToken.objects.create(
            application=app,
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            scopes=", ".join(scopes)
        )

        return Response({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 3600,
            "scope": token_obj.scopes,
            "api_domain": settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "localhost:8000",
            "token_type": "Bearer"
        })

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
