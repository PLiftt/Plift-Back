from rest_framework import serializers
from .models import TrainingBlock, TrainingSession, Exercise, AthleteProgress

# Lista de ejercicios predeterminados
EXERCISE_CHOICES = [
    ("Sentadilla", "Sentadilla"),
    ("Bench Press", "Bench Press"),
    ("Peso muerto", "Peso muerto"),
    ("Overhead Press", "Overhead Press"),
    ("Remo con barra", "Remo con barra"),
    ("Pull Up", "Pull Up"),
    ("Dips", "Dips"),
    ("Otro", "Otro"),  # Permite nombre personalizado
]

class ExerciseSerializer(serializers.ModelSerializer):
    predefined_name = serializers.ChoiceField(
        choices=EXERCISE_CHOICES,
        write_only=True,
        required=False
    )
    custom_name = serializers.CharField(
        max_length=30,
        required=False,
        write_only=True
    )
    name = serializers.CharField(read_only=True)

    class Meta:
        model = Exercise
        fields = "__all__"

    def validate(self, data):
        predefined = data.get("predefined_name")
        custom = data.get("custom_name")

        if self.instance:
            return data
        if predefined == "Otro" and not custom:
            raise serializers.ValidationError("Debe especificar el nombre si selecciona 'Otro'.")
        if predefined and predefined != "Otro":
            data["name"] = predefined
        elif custom:
            data["name"] = custom
        else:
            raise serializers.ValidationError("Debe seleccionar un ejercicio o escribir uno.")

        return data

    def create(self, validated_data):
        validated_data.pop("predefined_name", None)
        validated_data.pop("custom_name", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Actualiza los campos del ejercicio
        instance = super().update(instance, validated_data)

        # --- Lógica automática de completado ---
        session = instance.session
        block = session.block

        # ✅ Actualizar estado de la sesión
        exercises = session.exercises.all()
        all_exercises_completed = all(e.completed for e in exercises)

        if all_exercises_completed and session.status != "completed":
            session.status = "completed"
            session.save()
        elif not all_exercises_completed and session.status == "completed":
            session.status = "in_progress"
            session.save()

        # ✅ Actualizar estado del bloque
        sessions = block.sessions.all()
        all_sessions_completed = all(s.status == "completed" for s in sessions)

        if block.completed != all_sessions_completed:
            block.completed = all_sessions_completed
            block.save()

        return instance


    
class TrainingSessionSerializer(serializers.ModelSerializer):
    exercises = ExerciseSerializer(many=True, read_only=True)
    
    class Meta:
        model = TrainingSession
        fields = "__all__"

class TrainingBlockSerializer(serializers.ModelSerializer):
    sessions = TrainingSessionSerializer(many=True, read_only=True)
    athlete_name = serializers.SerializerMethodField()

    class Meta:
        model = TrainingBlock
        fields = "__all__"

    def get_athlete_name(self, obj):
        if obj.athlete:
            first = obj.athlete.first_name or ""
            last = obj.athlete.last_name or ""
            return f"{first} {last}".strip()
        return ""


class AthleteProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = AthleteProgress
        fields = "__all__"
