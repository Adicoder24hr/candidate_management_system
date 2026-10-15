import time
import requests
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from pymongo import MongoClient
from apps.messages_comm.models import MessageRecipient

START_TIME = time.time()

@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Backend and MongoDB Atlas health check.
    """
    db_status = "ok"
    try:
        client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
    except Exception as e:
        db_status = f"unhealthy: {type(e).__name__}"

    return Response({
        "status": "ok" if db_status == "ok" else "degraded",
        "service": "candidate-backend",
        "database": db_status,
        "uptime_seconds": round(time.time() - START_TIME, 2),
    }, status=status.HTTP_200_OK if db_status == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(["GET"])
@permission_classes([AllowAny])
def provider_health(request):
    """
    Proxy provider health check from provider-service.
    """
    provider_url = f"{settings.PROVIDER_BASE_URL.rstrip('/')}/health"
    try:
        resp = requests.get(provider_url, timeout=3)
        provider_ok = resp.status_code == 200
    except Exception as e:
        provider_ok = False

    recipients = MessageRecipient.objects.all()
    sent = recipients.filter(status__in=["sent", "delivered", "read"]).count()
    delivered = recipients.filter(status__in=["delivered", "read"]).count()
    failed = recipients.filter(status="failed").count()
    recent = list(recipients.order_by("-created_at")[:20])
    recent_failed = sum(1 for item in recent if item.status == "failed")
    failure_rate = (recent_failed / len(recent)) if recent else 0
    if not provider_ok or failure_rate > 0.5:
        health_status = "down"
    elif failure_rate >= 0.2:
        health_status = "degraded"
    else:
        health_status = "operational"
    return Response({
        "status": health_status,
        "provider_reachable": provider_ok,
        "sent": sent,
        "delivered": delivered,
        "failed": failed,
        "success_rate": round(delivered / sent * 100, 1) if sent else None,
        "recent_failure_rate": round(failure_rate * 100, 1),
    }, status=status.HTTP_200_OK)
