from django.urls import path
from .views import athlete_feedback, confirm_feedback

urlpatterns = [
    path("feedback/", athlete_feedback, name="athlete_feedback"),
    path("feedback/confirm/", confirm_feedback, name="confirm_feedback"),
]
