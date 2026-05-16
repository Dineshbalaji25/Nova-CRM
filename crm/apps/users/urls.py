from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

def auth_check(request):
    """Simple endpoint to check if user is authenticated"""
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'user': {
                'email': request.user.email,
                'full_name': getattr(request.user, 'full_name', ''),
            }
        })
    return JsonResponse({'authenticated': False}, status=401)

from .serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

from rest_framework.routers import DefaultRouter
from .views import APIKeyViewSet, ProfileViewSet, RoleViewSet
from .views import (
    RegisterView, GoogleAuthView, MyOrganizationsView, SwitchTenantView,
    ProfileViewSet, RoleViewSet, APIKeyViewSet, OAuthApplicationViewSet, TokenExchangeView, OAuthScopeListView
)

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profiles')
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'api-keys', APIKeyViewSet, basename='api-keys')
router.register(r'oauth-apps', OAuthApplicationViewSet, basename='oauth-apps')

urlpatterns = [
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_login'), # Alias for frontend
    path('register/', RegisterView.as_view(), name='register'),
    path('auth/google/', GoogleAuthView.as_view(), name='google_auth'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/check/', auth_check, name='auth_check'),
    path('users/profile/', auth_check, name='legacy_profile_alias'), # Support legacy calls
    path('oauth/token/', TokenExchangeView.as_view(), name='oauth_token_exchange'),
    path('oauth/scopes/', OAuthScopeListView.as_view(), name='oauth_scopes'),
    path('', include(router.urls)),
]
