from rest_framework import generics, viewsets, permissions
from django.contrib.auth import get_user_model
from .serializer import CoachAthleteSerializer, RegisterSerializer, UserSerializer, InvitationSerializer
from .models import CustomUser, Invitation
from training.models import CoachAthlete
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

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

    @swagger_auto_schema(
        operation_description="Crear una invitación (solo coaches)",
        request_body=InvitationSerializer,
        responses={201: InvitationSerializer()}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        method="post",
        operation_description="Aceptar una invitación como atleta",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "code": openapi.Schema(type=openapi.TYPE_STRING, description="Código de invitación")
            },
            required=["code"]
        ),
        responses={200: InvitationSerializer()}
    )
    @action(detail=False, methods=["post"])
    def accept(self, request):
        return super().accept(request)

    @swagger_auto_schema(
        method="post",
        operation_description="Rechazar una invitación como atleta",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "code": openapi.Schema(type=openapi.TYPE_STRING, description="Código de invitación")
            },
            required=["code"]
        ),
        responses={200: "Invitación rechazada"}
    )
    @action(detail=False, methods=["post"])
    def reject(self, request):
        return super().reject(request)


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