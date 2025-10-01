from rest_framework import serializers
from .models import TrainingBlock, TrainingSession, Exercise, AthleteProgress

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = "__all__"

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
