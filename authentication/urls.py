from rest_framework.routers import DefaultRouter
from django.urls import path, include
from authentication.views import UserViewSet, InvitationViewSet, CoachAthleteViewSet, RegisterView, ProfileView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'invitations', InvitationViewSet, basename='invitation')
router.register(r'coachathletes', CoachAthleteViewSet, basename='coachathlete')

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
]