from rest_framework import generics, viewsets, permissions, status
from django.contrib.auth import get_user_model
from .serializer import CoachAthleteSerializer, RegisterSerializer, UserSerializer, InvitationSerializer
from .models import CustomUser, Invitation
from training.models import CoachAthlete
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    # permission_classes = [permissions.IsAuthenticated]

class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.role != CustomUser.Role.COACH:
            raise PermissionDenied("Solo los coaches pueden crear invitaciones.")
        athlete_email = self.request.data.get("athlete_email")
        try:
            athlete = CustomUser.objects.get(email=athlete_email, role=CustomUser.Role.ATHLETE)
        except CustomUser.DoesNotExist:
            raise serializer.ValidationError({"athlete_email": "Atleta no encontrado"})
        serializer.save(coach=self.request.user, athlete=athlete)

        
    @action(detail=False, methods=["post"])
    def accept(self, request):
        code = request.data.get("code")
        try:
            invitation = Invitation.objects.get(code=code, accepted=False, athlete=request.user)
        except Invitation.DoesNotExist:
            return Response(
                {"error": "Invitación no válida o no eres el atleta invitado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Marcar invitación como aceptada
        invitation.accepted = True
        invitation.save()

        # Crear la relación CoachAthlete si no existe
        CoachAthlete.objects.get_or_create(
            coach=invitation.coach,
            athlete=invitation.athlete
        )

        return Response(InvitationSerializer(invitation).data)
    
    @action(detail=False, methods=["post"])
    def reject(self, request):
        code = request.data.get("code")
        try:
            invitation = Invitation.objects.get(code=code, accepted=False, athlete=request.user)
        except Invitation.DoesNotExist:
            return Response(
                {"error": "Invitación no válida o no eres el atleta invitado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation.delete()
        return Response({"message": "Invitación rechazada"})

class CoachAthleteViewSet(viewsets.ModelViewSet):
    queryset = CoachAthlete.objects.all()
    serializer_class = CoachAthleteSerializer
    # permission_classes = [permissions.IsAuthenticated]
