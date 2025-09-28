from rest_framework import generics, viewsets, permissions, status
from django.contrib.auth import get_user_model
from .serializer import CoachAthleteSerializer, RegisterSerializer, UserSerializer, InvitationSerializer, UserUpdateSerializer
from .models import CustomUser, Invitation
from training.models import CoachAthlete
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings

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

    @swagger_auto_schema(
        operation_description="Registrar un nuevo usuario",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response("Usuario registrado correctamente", UserSerializer),
            400: "Error en los datos enviados"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class UpdateProfileView(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["list", "create", "destroy"]:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [IsAdminOrSelf]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        operation_description="Listar todos los usuarios (solo admin).",
        responses={200: UserSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Obtener un usuario por ID (admin o el mismo usuario).",
        responses={200: UserSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Actualizar un usuario (admin o el mismo usuario).",
        request_body=UserSerializer,
        responses={200: UserSerializer()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Eliminar un usuario (solo admin).",
        responses={204: "Eliminado correctamente"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()
        out_serializer = self.get_serializer(invitation)
        return Response(out_serializer.data, status=201)

    @action(detail=False, methods=["post"])
    def accept(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"code": "Se requiere el código de invitación."}, status=400)

        try:
            invitation = Invitation.objects.get(code=code)
        except Invitation.DoesNotExist:
            return Response({"code": "Código inválido."}, status=404)

        if invitation.accepted:
            return Response({"detail": "Invitación ya aceptada."}, status=400)

        if invitation.athlete is None:
            invitation.athlete = request.user

        elif invitation.athlete != request.user:
            return Response({"detail": "No autorizado para aceptar esta invitación."}, status=403)

        invitation.accepted = True
        invitation.save()

        CoachAthlete.objects.get_or_create(
            coach=invitation.coach,
            athlete=invitation.athlete
        )

        serializer = self.get_serializer(invitation)
        return Response(serializer.data, status=200)


class CoachAthleteViewSet(viewsets.ModelViewSet):
    queryset = CoachAthlete.objects.all()
    serializer_class = CoachAthleteSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Listar relaciones coach-atleta",
        responses={200: CoachAthleteSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Obtener el perfil del usuario autenticado junto con sus atletas (si es coach) o su coach (si es atleta).",
        responses={200: UserSerializer()}
    )
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

class EmailTestView(APIView):
    """
    Envía un correo de prueba y muestra cualquier error en la respuesta.
    """
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Debes enviar un email"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            for i in range(10):
                send_mail(
                    subject=f"Correo de prueba #{i+1}",
                    message=f"Este es el correo de prueba número {i+1} WENA GERMAN",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Correo enviado 10 veces correctamente"}, status=status.HTTP_200_OK)