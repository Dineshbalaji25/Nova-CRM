from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

class AuthCheckView(APIView):
    """Check if user is authenticated via JWT."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'authenticated': True,
            'user': {
                'id': str(request.user.id),
                'email': request.user.email,
                'full_name': getattr(request.user, 'full_name', ''),
            }
        })

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
    path('auth/check/', AuthCheckView.as_view(), name='auth_check'),
    path('users/profile/', AuthCheckView.as_view(), name='legacy_profile_alias'), # Support legacy calls
    path('oauth/token/', TokenExchangeView.as_view(), name='oauth_token_exchange'),
    path('oauth/scopes/', OAuthScopeListView.as_view(), name='oauth_scopes'),
    path('my-organizations/', MyOrganizationsView.as_view(), name='my-organizations'),
    path('switch-tenant/', SwitchTenantView.as_view(), name='switch-tenant'),
    path('', include(router.urls)),
]
