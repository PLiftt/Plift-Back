from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import TrainingBlock, TrainingSession, Exercise, AthleteProgress
from .serializers import TrainingBlockSerializer, TrainingSessionSerializer, ExerciseSerializer, AthleteProgressSerializer
from django_filters.rest_framework import DjangoFilterBackend
from notification.models import PushToken
from notification.utils import send_push_notification
from django.db.models import Avg
from django.db.models.functions import TruncWeek
from rest_framework.exceptions import PermissionDenied
import matplotlib.pyplot as plt
from django.http import JsonResponse
import io
import base64
from datetime import date

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
        if self.request.user.role == "athlete":
            serializer.save(athlete=self.request.user)
        elif self.request.user.role == "coach":
            serializer.save()
        else:
            raise PermissionDenied("Solo coaches o atletas pueden registrar progreso")

    def get_queryset(self):
        user = self.request.user
        if user.role == "coach":
            return AthleteProgress.objects.filter(athlete__coaches__coach=user)
        if user.role == "athlete":
            return AthleteProgress.objects.filter(athlete=user)
        if user.role == "admin":
            return AthleteProgress.objects.all()
        return AthleteProgress.objects.none()

    @action(detail=False, methods=["get"])
    def strength_progress(self, request):
        """Devuelve la evolución semanal del 1RM promedio por ejercicio."""
        athlete = request.user

        if athlete.role != "athlete":
            return Response({"detail": "Solo atletas pueden ver su progreso."}, status=403)
        
        rpe_table = {
            10:  [1.00, 0.95, 0.92, 0.89, 0.86, 0.84, 0.81, 0.79],
            9.5: [0.98, 0.94, 0.90, 0.87, 0.84, 0.81, 0.79, 0.76],
            9:   [0.96, 0.92, 0.89, 0.86, 0.81, 0.79, 0.76, 0.74],
            8.5: [0.94, 0.90, 0.87, 0.84, 0.79, 0.76, 0.74, 0.71],
            8:   [0.92, 0.89, 0.86, 0.81, 0.79, 0.76, 0.74, 0.71],
            7.5: [0.91, 0.87, 0.84, 0.79, 0.76, 0.74, 0.71, 0.69],
            7:   [0.89, 0.86, 0.84, 0.79, 0.74, 0.71, 0.69, 0.67],
            6.5: [0.86, 0.84, 0.81, 0.76, 0.71, 0.69, 0.67, 0.64],
            6:   [0.84, 0.81, 0.79, 0.74, 0.69, 0.67, 0.64, 0.62],
            5:   [0.81, 0.79, 0.76, 0.71, 0.67, 0.64, 0.62, 0.59],
            4:   [0.79, 0.76, 0.74, 0.69, 0.64, 0.62, 0.59, 0.57],
        }
        
        week = date.today().isocalendar()[1]

        bench_progress, _ = AthleteProgress.objects.get_or_create(
            athlete=athlete,
            exercise=AthleteProgress.ExerciseChoices.BENCH,
            date__week=week,
            defaults={"best_weight": 0, "estimated_1rm": 0},
        )

        last_bench_press = Exercise.objects.filter(
            name=AthleteProgress.ExerciseChoices.BENCH,
            session__block__athlete=athlete,
            session__date__week=week,
        ).first()

        if last_bench_press:
            percentage = rpe_table[last_bench_press.rpe_actual][last_bench_press.reps - 1]
            bench_progress.best_weight = last_bench_press.weight_actual
            bench_progress.estimated_1rm = bench_progress.best_weight / percentage
            bench_progress.save()

        squat_progress, _ = AthleteProgress.objects.get_or_create(
            athlete=athlete,
            exercise=AthleteProgress.ExerciseChoices.SQUAT,
            date__week=week,
            defaults={"best_weight": 0, "estimated_1rm": 0},
        )

        last_squat = Exercise.objects.filter(
            name=AthleteProgress.ExerciseChoices.SQUAT,
            session__block__athlete=athlete,
            session__date__week=week,
        ).first()

        if last_squat:
            percentage = rpe_table[last_squat.rpe_actual][last_squat.reps - 1]
            squat_progress.best_weight = last_squat.weight
            squat_progress.estimated_1rm = squat_progress.best_weight / percentage
            squat_progress.save()

        deadlift_progress, _ = AthleteProgress.objects.get_or_create(
            athlete=athlete,
            exercise=AthleteProgress.ExerciseChoices.DEADLIFT,
            date__week=week,
            defaults={"best_weight": 0, "estimated_1rm": 0},
        )

        last_deadlift = Exercise.objects.filter(
            name=AthleteProgress.ExerciseChoices.DEADLIFT,
            session__block__athlete=athlete,
            session__date__week=week,
        ).first()

        if last_deadlift:
            percentage = rpe_table[last_deadlift.rpe_actual][last_deadlift.reps - 1]
            deadlift_progress.best_weight = last_deadlift.weight
            deadlift_progress.estimated_1rm = deadlift_progress.best_weight / percentage
            deadlift_progress.save()

        progress_data = (
            AthleteProgress.objects.filter(athlete=athlete)
            .annotate(week=TruncWeek("date"))
            .values("exercise", "week")
            .annotate(
                avg_best_weight=Avg("best_weight"),
                avg_est_1rm=Avg("estimated_1rm"),
            )
            .order_by("week")
        )

        # Reorganiza los datos por semana → {week: {Sentadilla: x, Press Banca: y, Peso Muerto: z}}
        structured = {}
        for entry in progress_data:
            week = entry["week"].strftime("%Y-%m-%d")
            exercise = entry["exercise"]
            if week not in structured:
                structured[week] = {}
            structured[week][exercise] = {
                "avg_best_weight": entry["avg_best_weight"],
                "avg_est_1rm": entry["avg_est_1rm"],
            }

        # Rellena con ejercicios faltantes (para que siempre haya los 3)
        all_exercises = [choice[0] for choice in AthleteProgress.ExerciseChoices.choices]
        for week, data in structured.items():
            for ex in all_exercises:
                data.setdefault(ex, {"avg_best_weight": None, "avg_est_1rm": None})

        return Response(structured)
    
    @action(detail=False, methods=["get"])
    def strength_chart(self, request):
        athlete = request.user
        data = self.strength_progress(request).data  # reutiliza la lógica anterior

        # Convertimos el JSON a formato de gráfico
        weeks = list(data.keys())
        exercises = ["Sentadilla", "Press Banca", "Peso Muerto"]

        plt.figure(figsize=(8,5))
        for exercise in exercises:
            y = [
                data[week][exercise]["avg_est_1rm"]
                if data[week][exercise]["avg_est_1rm"] is not None else None
                for week in weeks
            ]
            plt.plot(weeks, y, marker="o", label=exercise)

        plt.title("Evolución del 1RM estimado por semana")
        plt.xlabel("Semana")
        plt.ylabel("1RM estimado (kg)")
        plt.legend()
        plt.grid(True)

        # Convertir a imagen base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()

        graphic = base64.b64encode(image_png).decode("utf-8")
        return JsonResponse({"chart": graphic})