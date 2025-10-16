from django.db import models

from django.db import models
from authentication.models import CustomUser
from training.models import TrainingSession, Exercise
from django.core.exceptions import ValidationError

class AthleteFeedback(models.Model):
    athlete = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="feedbacks")
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name="feedbacks", null=True, blank=True)
    sleep_quality = models.IntegerField(help_text="Calidad del sueño 1-10")
    fatigue = models.IntegerField(help_text="Fatiga 1-10")
    stress = models.IntegerField(help_text="Estrés 1-10")
    soreness = models.TextField(blank=True, null=True, help_text="Molestias o dolores")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback {self.athlete.email} {self.created_at.date()}"

class ExerciseAdjustment(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="adjustments")
    sets = models.IntegerField()
    reps = models.IntegerField()
    weight = models.FloatField()
    reason = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    pending = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.exercise.name} - {self.date.date()} - {self.reason or 'Sin motivo'}"
