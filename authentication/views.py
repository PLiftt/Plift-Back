from rest_framework import generics, viewsets, permissions, status
from django.contrib.auth import get_user_model
from .serializer import CoachAthleteSerializer, RegisterSerializer, UserSerializer, InvitationSerializer
from .models import CustomUser, Invitation
from training.models import CoachAthlete
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

User = get_user_model()

class IsAdminOrSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # El admin puede ver todo
        if request.user.is_staff or request.user.is_superuser:
            return True
        # El usuario normal solo puede ver su propio perfil
        return obj == request.user

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny] 

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        # Solo admin puede listar todos los usuarios
        if self.action in ["list", "create", "destroy"]:
            permission_classes = [permissions.IsAdminUser]
        else:  # retrieve, update, partial_update → aplica regla personalizada
            permission_classes = [IsAdminOrSelf]
        return [permission() for permission in permission_classes]

class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    # GenerateInvitationView
    def perform_create(self, serializer):
        if self.request.user.role != CustomUser.Role.COACH:
            raise PermissionDenied("Solo los coaches pueden crear invitaciones.")
        athlete_email = self.request.data.get("athlete_email")
        try:
            athlete = CustomUser.objects.get(email=athlete_email, role=CustomUser.Role.ATHLETE)
        except CustomUser.DoesNotExist:
            raise serializer.ValidationError({"athlete_email": "Atleta no encontrado"})
        serializer.save(coach=self.request.user, athlete=athlete)

    # JoinAthleteView   
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
    permission_classes = [permissions.IsAuthenticated]

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = UserSerializer(user).data  

        if user.role == CustomUser.Role.COACH:
            athletes = CoachAthlete.objects.filter(coach=user)
            data["athletes"] = CoachAthleteSerializer(athletes, many=True).data

        elif user.role == CustomUser.Role.ATHLETE:
            coach_relation = CoachAthlete.objects.filter(athlete=user).first()
            data["coach"] = (
                CoachAthleteSerializer(coach_relation).data
                if coach_relation else None
            )

        return Response(data)