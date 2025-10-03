import os
import json
import openai
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from training.models import AthleteProgress, TrainingSession, Exercise
from .models import ExerciseAdjustment
from .serializer import AthleteFeedbackSerializer
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def athlete_feedback(request):
    """
    El atleta responde feedback diario y se ajusta la última sesión automáticamente,
    solo modificando los ejercicios existentes y registrando la razón del cambio.
    """
    serializer = AthleteFeedbackSerializer(data=request.data)
    if serializer.is_valid():

        session = TrainingSession.objects.filter(block__athlete=request.user).order_by("-date").first()
        feedback = serializer.save(athlete=request.user, session=session)
        progress = AthleteProgress.objects.filter(athlete=request.user).order_by("-date")[:3]
        
        context = f"""
Atleta: {request.user.first_name} {request.user.last_name}
Peso corporal: {request.user.bodyweight_kg} kg
Feedback diario:
- Sueño: {feedback.sleep_quality}/10
- Fatiga: {feedback.fatigue}/10
- Estrés: {feedback.stress}/10
- Dolores: {feedback.soreness or 'Ninguno'}

Últimos progresos:
{", ".join([f"{p.exercise}: {p.best_weight}kg (1RM est: {p.estimated_1rm})" for p in progress])}

Devuelve un JSON con este formato para los ejercicios de powerlifting:
{{
    "Squat": {{"sets": int, "reps": int, "weight": float, "reason": "motivo del ajuste"}},
    "Bench": {{"sets": int, "reps": int, "weight": float, "reason": "motivo del ajuste"}},
    "Deadlift": {{"sets": int, "reps": int, "weight": float, "reason": "motivo del ajuste"}}
}}
"""

        try:
            completion = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un coach de powerlifting que solo responde con JSON con ajustes de los ejercicios y un motivo."},
                    {"role": "user", "content": context}
                ],
                max_tokens=400,
                temperature=0.5
            )
            ai_reply = completion.choices[0].message.content

            try:
                adjustments = json.loads(ai_reply)
            except json.JSONDecodeError:
                adjustments = {}

            modified = []

            if session:
                # Mapear nombres del JSON a nombres existentes en la DB
                name_map = {
                    "Squat": "Sentadilla",
                    "Bench": "Bench Press",
                    "Deadlift": "Peso muerto"
                }

                for ai_name, db_name in name_map.items():
                    if ai_name in adjustments:
                        ex = session.exercises.filter(name=db_name).first()
                        if ex:
                            ex.sets = adjustments[ai_name]["sets"]
                            ex.reps = adjustments[ai_name]["reps"]
                            ex.weight = adjustments[ai_name]["weight"]
                            ex.save()

                            # Guardar el ajuste con motivo
                            ExerciseAdjustment.objects.create(
                                exercise=ex,
                                sets=ex.sets,
                                reps=ex.reps,
                                weight=ex.weight,
                                reason=adjustments[ai_name].get("reason", "")
                            )

                            modified.append({
                                "name": db_name,
                                "reason": adjustments[ai_name].get("reason", "")
                            })

            return Response({
                "feedback": serializer.data,
                "adjustments": adjustments,
                "modified_exercises": modified,
                "session_id": session.id if session else None
            }, status=status.HTTP_201_CREATED)

        except openai.OpenAIError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
