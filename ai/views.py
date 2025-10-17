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
                            data = adjustments[ai_name]

                            ExerciseAdjustment.objects.create(
                                exercise=ex,
                                sets=adjustments[ai_name]["sets"],
                                reps=adjustments[ai_name]["reps"],
                                weight=adjustments[ai_name]["weight"],
                                reason=adjustments[ai_name].get("reason", ""),
                                pending=True,
                            )

                            modified.append({
                                "name": db_name,
                                "reason": adjustments[ai_name].get("reason", ""),
                                "proposed_sets": data["sets"],
                                "proposed_reps": data["reps"],
                                "proposed_weight": data["weight"],
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirm_feedback(request):
    """
    El atleta confirma qué ajustes aplicar según la IA.
    Solo los confirmados se aplican al ejercicio real.
    """
    data = request.data
    session_id = data.get("session_id")
    accepted = data.get("accepted", {})

    # Verificar sesión activa del atleta
    session = TrainingSession.objects.filter(
        id=session_id, block__athlete=request.user
    ).first()
    if not session:
        return Response(
            {"error": "Sesión no encontrada"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Mapeo flexible (por si llegan en inglés o español)
    name_map = {
        "Squat": "Sentadilla",
        "Sentadilla": "Sentadilla",
        "Bench": "Bench Press",
        "Bench Press": "Bench Press",
        "Deadlift": "Peso muerto",
        "Peso muerto": "Peso muerto",
    }

    applied = []

    # 🔍 Recorremos los ajustes confirmados por el usuario
    for ai_name, accept in accepted.items():
        if not accept:
            continue

        db_name = name_map.get(ai_name)
        if not db_name:
            continue  # nombre no reconocido

        ex = session.exercises.filter(name=db_name).first()
        if not ex:
            continue  # ejercicio no existe en esa sesión

        # Buscar el último ajuste pendiente para ese ejercicio
        adj = (
            ExerciseAdjustment.objects.filter(exercise=ex, pending=True)
            .order_by("-id")
            .first()
        )
        if not adj:
            continue  # no hay ajuste pendiente

        # 🔧 Aplicar los cambios
        ex.sets = adj.sets
        ex.reps = adj.reps
        ex.weight = adj.weight
        ex.save()

        # Marcar ajuste como aplicado
        adj.pending = False
        adj.save()

        applied.append({
            "exercise": db_name,
            "new_sets": ex.sets,
            "new_reps": ex.reps,
            "new_weight": ex.weight,
        })

    # 🧩 Respuesta final
    if applied:
        return Response(
            {
                "message": "Hola.",
                "applied_exercises": applied,
            },
            status=status.HTTP_200_OK,
        )
    else:
        return Response(
            {"message": "No se aplicó ningún cambio. Verifica los nombres o estados."},
            status=status.HTTP_200_OK,
        )
