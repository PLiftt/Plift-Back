from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView 
from authentication.urls import router as auth_router
from authentication.urls import urlpatterns as auth_urls

# Router para los ViewSets
router = DefaultRouter()
router.registry.extend(auth_router.registry)

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    
    path("", include(router.urls)),
] + auth_urls
