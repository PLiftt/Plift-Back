from django.urls import path
from .views import athlete_feedback

urlpatterns = [
    path("feedback/", athlete_feedback, name="athlete_feedback"),
]
