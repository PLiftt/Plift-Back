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
        # Quitar los campos que no existen en el modelo
        validated_data.pop("predefined_name", None)
        validated_data.pop("custom_name", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Actualiza normalmente los campos del ejercicio
        instance = super().update(instance, validated_data)

        # --- Lógica automática de completado ---
        session = instance.session
        block = session.block

        # ✅ Actualizar estado de la sesión
        exercises = session.exercises.all()
        session_completed = all(e.completed for e in exercises)
        if session.completed != session_completed:
            session.completed = session_completed
            session.save()

        # ✅ Actualizar estado del bloque
        sessions = block.sessions.all()
        block_completed = all(s.completed for s in sessions)
        if block.completed != block_completed:
            block.completed = block_completed
            block.save()

        return instance

    
class TrainingSessionSerializer(serializers.ModelSerializer):
    exercises = ExerciseSerializer(many=True, read_only=True)
    
    class Meta:
        model = TrainingSession
        fields = "__all__"

class TrainingBlockSerializer(serializers.ModelSerializer):
    sessions = TrainingSessionSerializer(many=True, read_only=True)
    
    class Meta:
        model = TrainingBlock
        fields = "__all__"

class AthleteProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = AthleteProgress
        fields = "__all__"
