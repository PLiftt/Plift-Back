from django.db import models

from django.db import models
from authentication.models import  CustomUser

# Usar tabla intermedia para la relación muchos a muchos entre coaches y atletas
class CoachAthlete(models.Model):
    coach = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="athletes")
    athlete = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="coaches")
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("coach", "athlete")


class TrainingBlock(models.Model):
    class Periodization(models.TextChoices):
        LINEAL = "LINEAL", "Lineal"
        DUP = "DUP", "DUP"
        BLOQUES = "BLOQUES", "Bloques"

    athlete = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="blocks")
    coach = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    periodization = models.CharField(max_length=20, choices=Periodization.choices, default=Periodization.LINEAL)
    start_date = models.DateField()
    end_date = models.DateField()
    goal_competition_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)



class TrainingSession(models.Model):
    block = models.ForeignKey(TrainingBlock, on_delete=models.CASCADE, related_name="sessions")
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"Sesión {self.date} - {self.block.name}"


class Exercise(models.Model):
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name="exercises")
    name = models.CharField(max_length=100)
    sets = models.IntegerField(default=3)
    reps = models.IntegerField(default=5)
    weight = models.FloatField(null=True, blank=True)
    rpe = models.FloatField(null=True, blank=True)
    weight_actual = models.FloatField(null=True, blank=True)
    rpe_actual = models.FloatField(null=True, blank=True)
    completed = models.BooleanField(default=False)



class AthleteProgress(models.Model):
    athlete = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="progress")
    exercise = models.CharField(max_length=100) 
    best_weight = models.FloatField()  
    estimated_1rm = models.FloatField(null=True, blank=True) 
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.athlete.email} - {self.exercise}: {self.best_weight}kg"

