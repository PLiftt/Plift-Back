from django.urls import path
from .views import ContactMessageCreateView

urlpatterns = [
    path("api/contact/", ContactMessageCreateView.as_view(), name="contact-create"),
]
