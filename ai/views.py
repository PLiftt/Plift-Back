import os
import json
import openai
from openai import OpenAI
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from training.models import AthleteProgress, TrainingSession, Exercise
from .models import ExerciseAdjustment
from .serializer import AthleteFeedbackSerializer
from django.conf import settings


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def athlete_feedback(request):
    """
    El atleta responde feedback diario y se ajusta la última sesión activa automáticamente,
    sin modificar sesiones que ya estén finalizadas.
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    serializer = AthleteFeedbackSerializer(data=request.data)
    if serializer.is_valid():

        # Buscar sesión en progreso
        session = TrainingSession.objects.filter(
            block__athlete=request.user, 
            status="in_progress"
        ).first()

        if not session:
            return Response(
                {"error": "No hay una sesión activa para ajustar."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Guardar feedback
        feedback = serializer.save(athlete=request.user, session=session)
        progress = AthleteProgress.objects.filter(athlete=request.user).order_by("-date")[:3]
        
        # Contexto para el modelo
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
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """
Eres un coach de powerlifting experto. 
Tu tarea es analizar el feedback diario del atleta y ajustar los ejercicios principales (Squat, Bench y Deadlift).
Debes devolver únicamente un JSON con los ajustes propuestos. 

En cada ajuste incluye:
- sets, reps, y weight con valores numéricos adecuados.
- un campo "reason" con una explicación detallada (mínimo 2 oraciones) del por qué se realizó el ajuste, 
  considerando el estado del atleta (fatiga, estrés, sueño, dolores, rendimiento reciente, etc.).
  Usa un lenguaje natural, empático y técnico como un coach humano.

Ejemplo:
{
  "Squat": {"sets": 4, "reps": 6, "weight": 80, 
  "reason": "El atleta mostró buena recuperación y bajo nivel de fatiga, por lo que se mantiene la intensidad habitual para sostener la progresión."}
}
"""
                    },
                    {"role": "user", "content": context}
                ],
                max_tokens=600,
                temperature=0.7
            )

            ai_reply = completion.choices[0].message.content.strip()

            start_idx = ai_reply.find("{")
            end_idx = ai_reply.rfind("}") + 1
            if start_idx != -1 and end_idx != -1:
                ai_reply = ai_reply[start_idx:end_idx]

            try:
                adjustments = json.loads(ai_reply)
            except json.JSONDecodeError:
                adjustments = {}

            modified = []

            # Verificación adicional para no modificar sesiones terminadas
            if session.status != "completed":
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
            else:
                return Response(
                    {"error": "No se pueden modificar sesiones ya completadas."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response({
                "feedback": serializer.data,
                "adjustments": adjustments,
                "modified_exercises": modified,
                "session_id": session.id if session else None
            }, status=status.HTTP_201_CREATED)

        except openai.OpenAIError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
