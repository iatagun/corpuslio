"""API URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from .viewsets import (
    DocumentViewSet,
    GlobalFrequencyViewSet,
    TagViewSet,
    APIKeyViewSet,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'frequency', GlobalFrequencyViewSet, basename='frequency')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'keys', APIKeyViewSet, basename='apikey')

app_name = 'api'

urlpatterns = [
    # API documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
    
    # API endpoints (v1)
    path('v1/', include(router.urls)),
]
