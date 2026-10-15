import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from apps.messages_comm.services import verify_webhook_signature, process_webhook_event

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def provider_webhook(request):
    """
    POST /api/v1/webhooks/provider/
    Receives status update webhooks from the dummy provider.
    """
    body_bytes = request.body

    # HMAC-SHA256 signature verification
    signature = request.headers.get("X-Provider-Signature", "")
    if not verify_webhook_signature(body_bytes, signature):
        logger.warning("Webhook signature verification failed")
        return JsonResponse(
            {"error": {"code": "invalid_signature", "message": "Signature verification failed."}},
            status=401
        )

    try:
        event = json.loads(body_bytes)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse(
            {"error": {"code": "invalid_payload", "message": "Invalid JSON body."}},
            status=400
        )

    outcome = process_webhook_event(event)
    return JsonResponse({"status": "ok", "outcome": outcome}, status=200)
