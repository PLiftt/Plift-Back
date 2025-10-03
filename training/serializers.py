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
    # Campo opcional para nombre personalizado
    custom_name = serializers.CharField(
        max_length=30,
        required=False,
        write_only=True
    )

    class Meta:
        model = Exercise
        fields = "__all__"

    def validate(self, data):
        predefined = data.get("predefined_name")
        custom = data.get("custom_name")

        # Validar que haya un nombre
        if predefined == "Otro" and not custom:
            raise serializers.ValidationError("Debe especificar el nombre si selecciona 'Otro'.")
        if predefined and predefined != "Otro":
            data["name"] = predefined
        elif custom:
            data["name"] = custom
        else:
            raise serializers.ValidationError("Debe seleccionar un ejercicio o escribir uno.")

        return data
    
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
