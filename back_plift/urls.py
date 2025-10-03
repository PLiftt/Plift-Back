from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView 
from authentication.urls import router as auth_router
from authentication.urls import urlpatterns as auth_urls
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from training.urls import router as training_router
from ai.urls import urlpatterns as ai_urls


schema_view = get_schema_view(
    openapi.Info(
        title="API Documentación",
        default_version='v1',
        description="Documentación de la API para proyecto Plift",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contacto@tu_dominio.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


# Router para los ViewSets
router = DefaultRouter()
router.registry.extend(auth_router.registry)
router.registry.extend(training_router.registry)

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('', include((ai_urls, 'ai'), namespace='ai')),

    
    path("", include(router.urls)),
] + auth_urls
