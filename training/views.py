from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import TrainingBlock, TrainingSession, Exercise, AthleteProgress
from .serializers import TrainingBlockSerializer, TrainingSessionSerializer, ExerciseSerializer, AthleteProgressSerializer


class TrainingBlockViewSet(viewsets.ModelViewSet):
    queryset = TrainingBlock.objects.all()
    serializer_class = TrainingBlockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # 🚨 Solo los coaches pueden crear bloques
        if self.request.user.role != "coach":
            raise PermissionDenied("Solo los coaches pueden crear bloques")

        # Asignar automáticamente al coach que lo creó
        serializer.save(coach=self.request.user)

    def get_queryset(self):
        user = self.request.user

        if user.role == "coach":
            # Coach solo ve los bloques que él mismo creó
            return TrainingBlock.objects.filter(coach=user)

        if user.role == "athlete":
            # Atleta solo ve sus propios bloques
            return TrainingBlock.objects.filter(athlete=user)

        if user.role == "admin":
            return TrainingBlock.objects.all()

        return TrainingBlock.objects.none()


class TrainingSessionViewSet(viewsets.ModelViewSet):
    queryset = TrainingSession.objects.all()
    serializer_class = TrainingSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.role != "coach":
            raise PermissionDenied("Solo los coaches pueden crear sesiones")

        serializer.save()

    def get_queryset(self):
        user = self.request.user

        if user.role == "coach":
            # Coach ve sesiones de sus bloques
            return TrainingSession.objects.filter(block__coach=user)

        if user.role == "athlete":
            # Atleta ve sesiones de sus bloques
            return TrainingSession.objects.filter(block__athlete=user)

        if user.role == "admin":
            return TrainingSession.objects.all()

        return TrainingSession.objects.none()


class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticated]

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
