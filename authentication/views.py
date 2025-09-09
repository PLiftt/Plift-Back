from rest_framework import generics
from django.contrib.auth import get_user_model
from .serializer import RegisterSerializer, UserSerializer
from rest_framework import viewsets, permissions
from .models import CustomUser

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    # permission_classes = [permissions.IsAuthenticated]
