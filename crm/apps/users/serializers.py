from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Organization, OrganizationMember, APIKey, Profile, Role

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
