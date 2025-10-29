# notifications/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import PushToken

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_device_token(request):
    token = request.data.get("expo_token")
    if not token:
        return Response({"error": "Falta expo_token"}, status=400)
    obj, _ = PushToken.objects.update_or_create(
        user=request.user,
        expo_token=token
    )
    return Response({"ok": True})
