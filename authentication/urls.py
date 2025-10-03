from rest_framework.routers import DefaultRouter
from django.urls import path, include
from authentication.views import UserViewSet, InvitationViewSet, CoachAthleteViewSet, RegisterView, ProfileView, UpdateProfileView, ResetPasswordRequestView, ResetPasswordConfirmView
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'invitations', InvitationViewSet, basename='invitation')
router.register(r'coachathletes', CoachAthleteViewSet, basename='coachathlete')

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("update-profile/", UpdateProfileView.as_view(), name="update-profile"),
    path('reset-password-request/', ResetPasswordRequestView.as_view(), name='reset-password'),
    path('reset-password-confirm/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),

]