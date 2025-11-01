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
    def block_progress(self, request):
        """
        Devuelve el progreso del atleta dentro de un bloque específico.
        Usa el parámetro ?block=<id>
        """
        athlete = request.user
        block_id = request.query_params.get("block")

        if athlete.role != "athlete":
            return Response({"detail": "Solo los atletas pueden ver su progreso."}, status=403)

        if not block_id:
            return Response({"detail": "Debes indicar el parámetro ?block=<id>."}, status=400)

        # Obtenemos las fechas del bloque para filtrar los progresos dentro de ese rango
        try:
            block = TrainingBlock.objects.get(id=block_id, athlete=athlete)
        except TrainingBlock.DoesNotExist:
            return Response({"detail": "Bloque no encontrado."}, status=404)

        # Filtramos registros de progreso del atleta dentro del rango del bloque
        progress_qs = AthleteProgress.objects.filter(
            athlete=athlete,
            date__range=[block.start_date, block.end_date]
        )

        if not progress_qs.exists():
            return Response({"detail": "No hay registros de progreso en este bloque."}, status=404)

        # Promedio por tipo de ejercicio (Sentadilla, Press Banca, Peso Muerto)
        progress_data = (
            progress_qs.values("exercise")
            .annotate(
                avg_best_weight=Avg("best_weight"),
                avg_est_1rm=Avg("estimated_1rm"),
            )
            .order_by("exercise")
        )

        # Asegurar que todos los ejercicios aparezcan, aunque no tengan datos
        structured = {}
        all_exercises = [choice[0] for choice in AthleteProgress.ExerciseChoices.choices]

        for ex in all_exercises:
            match = next((p for p in progress_data if p["exercise"] == ex), None)
            structured[ex] = {
                "avg_best_weight": match["avg_best_weight"] if match else None,
                "avg_est_1rm": match["avg_est_1rm"] if match else None,
            }

        return Response({
            "block_id": block_id,
            "athlete": athlete.email,
            "progress": structured
        })

    
    @action(detail=False, methods=["get"])
    def strength_chart(self, request):
        """
        Devuelve un gráfico del progreso (estimación de 1RM) por bloque.
        Usa el parámetro ?block=<id>
        """
        athlete = request.user
        block_id = request.query_params.get("block")

        if athlete.role != "athlete":
            return Response({"detail": "Solo los atletas pueden ver su progreso."}, status=403)

        if not block_id:
            return Response({"detail": "Debes indicar el parámetro ?block=<id>."}, status=400)

        # Buscar el bloque y validar que pertenezca al atleta
        try:
            block = TrainingBlock.objects.get(id=block_id, athlete=athlete)
        except TrainingBlock.DoesNotExist:
            return Response({"detail": "Bloque no encontrado."}, status=404)

        # Filtrar los progresos del atleta dentro del rango del bloque
        progress_qs = AthleteProgress.objects.filter(
            athlete=athlete,
            date__range=[block.start_date, block.end_date]
        )

        if not progress_qs.exists():
            return Response({"detail": "No hay registros de progreso en este bloque."}, status=404)

        # Agrupar por fecha y ejercicio para mostrar evolución dentro del bloque
        progress_data = (
            progress_qs.values("date", "exercise")
            .annotate(avg_est_1rm=Avg("estimated_1rm"))
            .order_by("date")
        )

        # Estructurar datos por ejercicio
        exercises = [choice[0] for choice in AthleteProgress.ExerciseChoices.choices]
        dates = sorted(set([str(p["date"]) for p in progress_data]))

        plt.figure(figsize=(8, 5))
        for ex in exercises:
            y = [
                next((p["avg_est_1rm"] for p in progress_data if str(p["date"]) == d and p["exercise"] == ex), None)
                for d in dates
            ]
            plt.plot(dates, y, marker="o", label=ex)

        plt.title(f"Evolución del 1RM estimado - Bloque {block.name}")
        plt.xlabel("Fecha")
        plt.ylabel("1RM estimado (kg)")
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True)

        # Convertir el gráfico a base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()

        graphic = base64.b64encode(image_png).decode("utf-8")
        return JsonResponse({
            "block": block.name,
            "start_date": str(block.start_date),
            "end_date": str(block.end_date),
            "chart": graphic
        })