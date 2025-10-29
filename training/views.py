from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import TrainingBlock, TrainingSession, Exercise, AthleteProgress
from .serializers import TrainingBlockSerializer, TrainingSessionSerializer, ExerciseSerializer, AthleteProgressSerializer
from django_filters.rest_framework import DjangoFilterBackend
from notification.models import PushToken
from notification.utils import send_push_notification


class TrainingBlockViewSet(viewsets.ModelViewSet):
    queryset = TrainingBlock.objects.all()
    serializer_class = TrainingBlockSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["athlete", "coach"]  # ahora permite ?athlete=<id> o ?coach=<id>

    def perform_create(self, serializer):
        if self.request.user.role != "coach":
            raise PermissionDenied("Solo los coaches pueden crear bloques")
        bloque = serializer.save(coach=self.request.user)

        # 🚀 Enviar notificación push solo al atleta correspondiente
        athlete = bloque.athlete
        if athlete:
            tokens = PushToken.objects.filter(user=athlete)
            for t in tokens:
                send_push_notification(
                    t.token,
                    "Nuevo bloque asignado",
                    "Tu coach ha creado un nuevo bloque.",
                    {"event": "NEW_BLOCK", "blockId": bloque.id},
                )
    def get_queryset(self):
        user = self.request.user

        if user.role == "coach":
            return TrainingBlock.objects.filter(coach=user)

        if user.role == "athlete":
            return TrainingBlock.objects.filter(athlete=user)

        if user.role == "admin":
            return TrainingBlock.objects.all()

        return TrainingBlock.objects.none()


class TrainingSessionViewSet(viewsets.ModelViewSet):
    queryset = TrainingSession.objects.all()
    serializer_class = TrainingSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["block"]  # ahora permite ?block=<id>

    def perform_create(self, serializer):
        if self.request.user.role != "coach":
            raise PermissionDenied("Solo los coaches pueden crear sesiones")
        serializer.save()

    def get_queryset(self):
        user = self.request.user

        if user.role == "coach":
            return TrainingSession.objects.filter(block__coach=user)

        if user.role == "athlete":
            return TrainingSession.objects.filter(block__athlete=user)

        if user.role == "admin":
            return TrainingSession.objects.all()

        return TrainingSession.objects.none()
    
    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        session = self.get_object()
        if session.status == "in_progress":
            return Response({"detail": "La sesión ya está iniciada."}, status=status.HTTP_400_BAD_REQUEST)
        session.status = "in_progress"
        session.save()
        return Response({"detail": f"Sesión {session.id} iniciada."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def finish(self, request, pk=None):
        session = self.get_object()
        if session.status != "in_progress":
            return Response({"detail": "Solo puedes finalizar una sesión en progreso."}, status=status.HTTP_400_BAD_REQUEST)
        session.status = "completed"
        session.save()
        return Response({"detail": f"Sesión {session.id} finalizada."}, status=status.HTTP_200_OK)


class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["session"]  # ahora permite ?session=<id>

    def perform_create(self, serializer):
        if self.request.user.role != "coach":
            raise PermissionDenied("Solo los coaches pueden crear ejercicios")
        serializer.save()

    def get_queryset(self):
        user = self.request.user

        if user.role == "coach":
            return Exercise.objects.filter(session__block__coach=user)

        if user.role == "athlete":
            return Exercise.objects.filter(session__block__athlete=user)

        if user.role == "admin":
            return Exercise.objects.all()

        return Exercise.objects.none()


class AthleteProgressViewSet(viewsets.ModelViewSet):
    queryset = AthleteProgress.objects.all()
    serializer_class = AthleteProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # ✅ Tanto atleta como coach pueden registrar progreso
        # pero si es atleta, se asegura que el progreso quede asociado a él mismo
        if self.request.user.role == "athlete":
            serializer.save(athlete=self.request.user)
        elif self.request.user.role == "coach":
            serializer.save()
        else:
            raise PermissionDenied("Solo coaches o atletas pueden registrar progreso")

    def get_queryset(self):
        user = self.request.user

        if user.role == "coach":
            # Un coach debería ver solo progreso de sus atletas (opcional)
            return AthleteProgress.objects.filter(
                athlete__coaches__coach=user
            )

        if user.role == "athlete":
            return AthleteProgress.objects.filter(athlete=user)

        if user.role == "admin":
            return AthleteProgress.objects.all()

        return AthleteProgress.objects.none()
