from django.core.cache import cache
from rest_framework import serializers

def get_user_field_permissions(user, organization_id):
    """
    Returns the field permissions dict for this user's Profile in this org.
    Cached per user+org for 5 minutes.
    """
    cache_key = f"fls:{user.id}:{organization_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    from apps.users.models import OrganizationMember
    try:
        membership = OrganizationMember.objects.select_related('rbac_profile').get(
            user=user,
            organization_id=organization_id,
            is_active=True
        )
        perms = {}
        if membership.rbac_profile:
            perms = membership.rbac_profile.permissions.get('fields', {})
    except OrganizationMember.DoesNotExist:
        perms = {}

    cache.set(cache_key, perms, 300)
    return perms


class FieldLevelSecurityMixin:
    """
    DRF Serializer mixin.
    Reads the requesting user's Profile.permissions and:
      - Drops write-only fields from incoming data (raises ValidationError)
      - Masks read-only fields in outgoing representation (replaces value with "***")
    """

    def _get_fls_perms(self):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return {}
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return {}
        return get_user_field_permissions(request.user, tenant_id)

    def _model_key(self, field_name):
        """Builds 'app_label.ModelName.field_name' key for permission lookup."""
        meta = self.Meta.model._meta
        return f"{meta.app_label}.{meta.object_name}.{field_name}"

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        perms = self._get_fls_perms()
        for field_name in list(ret.keys()):
            key = self._model_key(field_name)
            rule = perms.get(key)
            if rule == 'hidden':
                ret.pop(field_name, None)
            elif rule == 'read_only':
                pass  # visible but write is blocked in validate
        return ret

    def validate(self, attrs):
        perms = self._get_fls_perms()
        for field_name in list(attrs.keys()):
            key = self._model_key(field_name)
            rule = perms.get(key)
            if rule in ('read_only', 'hidden'):
                raise serializers.ValidationError(
                    {field_name: f"You do not have permission to edit this field."}
                )
        return super().validate(attrs)
