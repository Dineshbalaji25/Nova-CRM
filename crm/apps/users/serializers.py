from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Organization,
    OrganizationMember,
    APIKey,
    Profile,
    Role,
    OAuthApplication,
    OAuthToken,
    OAUTH_SCOPE_CHOICES,
    default_oauth_scopes,
)

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ('organization', 'created_at', 'updated_at')

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'
        read_only_fields = ('organization', 'created_at', 'updated_at')
class APIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = ('id', 'name', 'key', 'is_active', 'last_used_at', 'created_at')
        read_only_fields = ('id', 'key', 'last_used_at', 'created_at')

class OAuthApplicationSerializer(serializers.ModelSerializer):
    allowed_scopes = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=False,
    )

    class Meta:
        model = OAuthApplication
        fields = (
            'id',
            'name',
            'client_id',
            'client_secret',
            'redirect_uri',
            'allowed_scopes',
            'is_active',
            'created_at'
        )
        read_only_fields = ('id', 'client_id', 'client_secret', 'created_at')

    def validate_allowed_scopes(self, value):
        invalid_scopes = [scope for scope in value if scope not in OAUTH_SCOPE_CHOICES]
        if invalid_scopes:
            raise serializers.ValidationError(f"Invalid scopes: {', '.join(invalid_scopes)}")
        return list(dict.fromkeys(value))

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if 'allowed_scopes' not in attrs and self.instance is None:
            attrs['allowed_scopes'] = default_oauth_scopes()
        return attrs

class OAuthTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = OAuthToken
        fields = ('id', 'application', 'access_token', 'refresh_token', 'expires_at', 'scopes', 'is_revoked')
        read_only_fields = ('id', 'access_token', 'refresh_token', 'expires_at')

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'created_at')
        read_only_fields = ('id', 'email', 'created_at')

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'name', 'slug', 'is_active', 'created_at')

class OrganizationMemberSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    
    class Meta:
        model = OrganizationMember
        fields = ('id', 'organization', 'role', 'joined_at', 'is_active')
        # Note: joined_at comes from BaseModel.created_at

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        if user.default_organization:
            token['tenant_id'] = str(user.default_organization.id)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add extra info to response
        data['user'] = {
            'email': self.user.email,
            'full_name': self.user.full_name,
        }
        if self.user.default_organization:
            data['tenant_id'] = str(self.user.default_organization.id)
            data['organization_name'] = self.user.default_organization.name
        else:
            # Fallback to first organization if no default
            first_org = self.user.memberships.first()
            if first_org:
                data['tenant_id'] = str(first_org.organization.id)
                data['organization_name'] = first_org.organization.name
        
        return data

class RegisterRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    full_name = serializers.CharField(required=False)
    organization_name = serializers.CharField(required=True)
