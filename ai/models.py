from django.db import models

from django.db import models
from django.core.exceptions import ValidationError

class AISuggestion(models.Model):
    class Scope(models.TextChoices):
        EXERCISE = "EXERCISE", "Exercise"
        SESSION = "SESSION", "Session"
        BLOCK = "BLOCK", "Block"

    target_scope = models.CharField(max_length=20, choices=Scope.choices, default=Scope.EXERCISE)
    exercise = models.ForeignKey('training.Exercise', on_delete=models.CASCADE, null=True, blank=True, related_name="ai_suggestions")
    session = models.ForeignKey('training.TrainingSession', on_delete=models.CASCADE, null=True, blank=True, related_name="ai_suggestions")
    block = models.ForeignKey('training.TrainingBlock', on_delete=models.CASCADE, null=True, blank=True, related_name="ai_suggestions")

    suggested_weight = models.FloatField(null=True, blank=True)
    suggested_sets = models.IntegerField(null=True, blank=True)
    suggested_reps = models.IntegerField(null=True, blank=True)
    suggested_rpe = models.FloatField(null=True, blank=True)

    rationale = models.TextField(blank=True)
    model_version = models.CharField(max_length=50, default="v1")
    created_at = models.DateTimeField(auto_now_add=True)

    accepted = models.BooleanField(default=False)
    accepted_by = models.ForeignKey('authentication.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name="accepted_ai_suggestions")
    accepted_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.target_scope == self.Scope.EXERCISE and not self.exercise:
            raise ValidationError("Debe asignar un ejercicio para target_scope EXERCISE.")
        if self.target_scope == self.Scope.SESSION and not self.session:
            raise ValidationError("Debe asignar una sesión para target_scope SESSION.")
        if self.target_scope == self.Scope.BLOCK and not self.block:
            raise ValidationError("Debe asignar un bloque para target_scope BLOCK.")

    def __str__(self):
        target = self.exercise or self.session or self.block
        return f"AI Sug ({self.target_scope}) → {target}"


class AIAdjustmentLog(models.Model):
    exercise = models.ForeignKey('training.Exercise', on_delete=models.SET_NULL, null=True, related_name="ai_adjustments")
    prev_weight = models.FloatField(null=True, blank=True)
    new_weight = models.FloatField(null=True, blank=True)
    prev_sets = models.IntegerField(null=True, blank=True)
    new_sets = models.IntegerField(null=True, blank=True)
    prev_reps = models.IntegerField(null=True, blank=True)
    new_reps = models.IntegerField(null=True, blank=True)
    prev_rpe = models.FloatField(null=True, blank=True)
    new_rpe = models.FloatField(null=True, blank=True)

    applied_by_ai = models.BooleanField(default=True)
    applied_by = models.ForeignKey('authentication.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name="manual_adjustments")
    suggestion = models.ForeignKey(AISuggestion, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
