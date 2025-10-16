from rest_framework.permissions import AllowAny  # o IsAuthenticated si quieres
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .models import ContactMessage, ContactAttachment
from .serializers import ContactMessageOut


class ContactMessageCreateView(APIView):
    """
    POST multipart/form-data a /api/contact/
      Campos:
        - email (opcional si hay user)
        - subject (str)
        - message (str)
        - client_request_id (opcional)
        - locale (opcional)
        - attachments: múltiples archivos con clave 'attachments'
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        subject = (request.data.get("subject") or "").strip()
        message = (request.data.get("message") or "").strip()
        email = (request.data.get("email") or "").strip() or None
        client_request_id = (request.data.get("client_request_id") or "").strip()
        locale = (request.data.get("locale") or "").strip()

        if not subject or not message:
            return Response({"detail": "subject y message son obligatorios."},
                            status=status.HTTP_400_BAD_REQUEST)

        user = request.user if request.user.is_authenticated else None
        if not user and not email:
            return Response({"detail": "Si no estás autenticado, envía 'email'."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Crea el mensaje
        msg = ContactMessage.objects.create(
            user=user,
            email=email,
            subject=subject,
            message=message,
            client_request_id=client_request_id,
            locale=locale,
        )

        # Adjuntos
        files = request.FILES.getlist("attachments")
        for f in files:
            ContactAttachment.objects.create(
                message=msg,
                file=f,
                original_name=getattr(f, "name", ""),
                content_type=getattr(f, "content_type", ""),
                size=getattr(f, "size", 0),
            )

        # (Opcional) enviar email interno aquí si quieres
        # from django.core.mail import send_mail
        # send_mail(subject, message, "<from@yourdomain>", ["destino@plift..."])

        data = ContactMessageOut(msg).data
        return Response(data, status=status.HTTP_201_CREATED)
