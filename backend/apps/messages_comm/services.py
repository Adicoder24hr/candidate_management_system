import uuid
import hmac
import hashlib
import json
import time
import random
import logging
from typing import Optional
from zoneinfo import ZoneInfo

import requests
from django.conf import settings
from django.utils import timezone
from apps.messages_comm.models import Message, MessageRecipient
from apps.candidates.models import Candidate

logger = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")

# ─── Friendly error messages ───────────────────────────────────────────────────

FRIENDLY_MESSAGES = {
    "invalid_recipient": "This phone number isn't valid or can't receive messages.",
    "rate_limited": "Too many messages sent. We'll retry shortly.",
    "temporary_failure": "The messaging service had a temporary problem.",
    "provider_down": "The messaging service is currently unavailable.",
    "delivery_failed": "The message couldn't be delivered to the recipient.",
    "timeout": "The request to the messaging service timed out.",
    "unknown": "Something went wrong. Please try again.",
}

RETRYABLE_CODES = {"rate_limited", "temporary_failure", "provider_down", "timeout"}

# Status rank for out-of-order protection
STATUS_RANK = {
    "queued": 1,
    "sent": 2,
    "delivered": 3,
    "read": 4,
    "failed": 0,   # special handling
}


def get_friendly_message(error_code: str) -> str:
    return FRIENDLY_MESSAGES.get(error_code, FRIENDLY_MESSAGES["unknown"])


def is_retryable(error_code: str) -> bool:
    return error_code in RETRYABLE_CODES


# ─── Provider adapter ─────────────────────────────────────────────────────────

def call_provider(candidate: Candidate, message_body: str, idempotency_key: str) -> dict:
    """
    Call the dummy provider to send a message.
    Returns: {"provider_message_id": ..., "status": "queued"} on success
    Raises: ValueError with error_code on failure
    """
    provider_url = f"{settings.PROVIDER_BASE_URL.rstrip('/')}/v1/messages"
    webhook_url = f"{settings.BACKEND_URL.rstrip('/')}/api/v1/webhooks/provider/"

    payload = {
        "to_phone": candidate.phone,
        "message": message_body,
        "callback_url": webhook_url,
        "idempotency_key": idempotency_key,
        "channel": "whatsapp",
    }

    try:
        resp = requests.post(provider_url, json=payload, timeout=5)
    except requests.Timeout:
        raise _ProviderError("timeout")
    except requests.ConnectionError:
        raise _ProviderError("provider_down")

    if resp.status_code == 202:
        data = resp.json()
        return {"provider_message_id": data["provider_message_id"], "status": "queued"}

    # Map HTTP error codes to error_codes
    try:
        body = resp.json()
        err_detail = body.get("detail", {})
        if isinstance(err_detail, dict):
            err_inner = err_detail.get("error", {})
            error_code = err_inner.get("code", "unknown")
        else:
            error_code = "unknown"
    except Exception:
        error_code = "unknown"

    raise _ProviderError(error_code)


class _ProviderError(Exception):
    def __init__(self, error_code: str):
        super().__init__(error_code)
        self.error_code = error_code


# ─── Send a single message to one candidate ───────────────────────────────────

def send_to_candidate(
    candidate: Candidate,
    message: Message,
    max_attempts: int = 3,
) -> MessageRecipient:
    """
    Create a MessageRecipient and try to send via provider.
    On failure: classify, store, and (for retryable) retry with exponential backoff.
    """
    idempotency_key = str(uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"{message.message_id}:{candidate.candidate_id}"
    ))

    recipient, created = MessageRecipient.objects.get_or_create(
        message=message,
        candidate=candidate,
        defaults={
            "status": "queued",
            "channel": message.channel,
            "idempotency_key": idempotency_key,
            "attempt_count": 0,
        }
    )

    if not created and recipient.status in ("sent", "delivered", "read"):
        # Already succeeded — idempotent
        return recipient

    attempt = recipient.attempt_count

    while attempt < max_attempts:
        attempt += 1
        recipient.attempt_count = attempt
        recipient.save(update_fields=["attempt_count"])

        try:
            result = call_provider(candidate, message.body, idempotency_key)
            recipient.status = "queued"
            recipient.provider_message_id = result["provider_message_id"]
            recipient.error_code = None
            recipient.friendly_message = None
            recipient.retryable = False
            recipient.save(update_fields=["status", "provider_message_id", "error_code", "friendly_message", "retryable"])
            return recipient

        except _ProviderError as e:
            error_code = e.error_code
            retryable = is_retryable(error_code)
            friendly = get_friendly_message(error_code)

            recipient.error_code = error_code
            recipient.friendly_message = friendly
            recipient.retryable = retryable

            if retryable and attempt < max_attempts:
                # Exponential backoff: min(2 * 2^(attempt-1), 30) + jitter 0-500ms
                delay = min(2 * (2 ** (attempt - 1)), 30) + random.uniform(0, 0.5)
                recipient.status = "queued"
                recipient.save(update_fields=["status", "error_code", "friendly_message", "retryable", "attempt_count"])
                time.sleep(delay)
                continue
            else:
                # Permanent failure or exhausted retries
                recipient.status = "failed"
                recipient.failed_at = timezone.now()
                recipient.save(update_fields=["status", "error_code", "friendly_message", "retryable", "failed_at"])
                return recipient

    return recipient


# ─── Bulk send ────────────────────────────────────────────────────────────────

def bulk_send(candidate_ids: list[str], body: str) -> dict:
    """
    Send a message to multiple candidates. Each is independent — one failure
    never blocks others. Returns per-candidate results.
    """
    candidates = list(
        Candidate.objects.filter(candidate_id__in=candidate_ids, is_deleted=False)
    )

    message = Message.objects.create(
        body=body,
        channel="whatsapp",
    )

    results = []
    succeeded = 0
    failed = 0

    for candidate in candidates:
        try:
            recipient = send_to_candidate(candidate, message)
            if recipient.status == "failed":
                failed += 1
                results.append({
                    "candidate_id": candidate.candidate_id,
                    "candidate_name": candidate.name,
                    "status": "failed",
                    "error": recipient.friendly_message or "Unknown error",
                    "recipient_id": str(recipient.pk),
                })
            else:
                succeeded += 1
                results.append({
                    "candidate_id": candidate.candidate_id,
                    "candidate_name": candidate.name,
                    "status": "sent",
                    "recipient_id": str(recipient.pk),
                })
        except Exception as ex:
            logger.exception(f"Unexpected error sending to candidate {candidate.candidate_id}: {ex}")
            failed += 1
            results.append({
                "candidate_id": candidate.candidate_id,
                "candidate_name": candidate.name,
                "status": "failed",
                "error": "Something went wrong. Please try again.",
                "recipient_id": None,
            })

    return {
        "total": len(candidates),
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
        "message_id": message.message_id,
    }


# ─── Retry a single recipient ─────────────────────────────────────────────────

def retry_recipient(recipient_id: str) -> Optional[MessageRecipient]:
    try:
        recipient = MessageRecipient.objects.select_related("message", "candidate").get(pk=recipient_id)
    except MessageRecipient.DoesNotExist:
        return None

    if not recipient.retryable:
        return recipient

    # Reset to queued so send_to_candidate can re-try
    recipient.status = "queued"
    recipient.attempt_count = 0
    recipient.error_code = None
    recipient.friendly_message = None
    recipient.retryable = False
    recipient.save(update_fields=["status", "attempt_count", "error_code", "friendly_message", "retryable"])

    # Retry with remaining attempts
    send_to_candidate(recipient.candidate, recipient.message, max_attempts=3)
    recipient.refresh_from_db()
    return recipient


# ─── Webhook processing ───────────────────────────────────────────────────────

def verify_webhook_signature(body_bytes: bytes, signature_header: str) -> bool:
    secret = settings.PROVIDER_WEBHOOK_SECRET.encode("utf-8")
    expected = hmac.new(secret, body_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header or "")


def process_webhook_event(event: dict) -> str:
    """
    Process a provider webhook event. Returns 'processed', 'duplicate', or 'ignored'.
    """
    provider_message_id = event.get("provider_message_id")
    event_id = event.get("event_id")
    new_status = event.get("status")
    error_code = event.get("error_code")

    if not provider_message_id or not event_id or not new_status:
        return "invalid"

    # Idempotency: check if we've already processed this event
    from apps.webhooks.models import WebhookEvent
    if WebhookEvent.objects.filter(
        provider_message_id=provider_message_id,
        event_id=event_id,
    ).exists():
        logger.info(f"Duplicate webhook event {event_id} — ignored")
        return "duplicate"

    # Store event first (always, for audit trail)
    try:
        WebhookEvent.objects.create(
            event_id=event_id,
            provider_message_id=provider_message_id,
            status=new_status,
            signature="",
            signature_verified=True,
            payload=event,
        )
    except Exception as exc:
        # A concurrent duplicate can win the unique compound index race.
        from django.db import IntegrityError
        if isinstance(exc, IntegrityError) and WebhookEvent.objects.filter(
            provider_message_id=provider_message_id,
            event_id=event_id,
        ).exists():
            return "duplicate"
        raise

    # Find the recipient
    try:
        recipient = MessageRecipient.objects.get(provider_message_id=provider_message_id)
    except MessageRecipient.DoesNotExist:
        logger.warning(f"No recipient for provider_message_id={provider_message_id}")
        return "ignored"
    except MessageRecipient.MultipleObjectsReturned:
        recipient = MessageRecipient.objects.filter(provider_message_id=provider_message_id).first()

    current_rank = STATUS_RANK.get(recipient.status, 0)
    new_rank = STATUS_RANK.get(new_status, 0)

    if recipient.status == "failed":
        logger.info("Ignoring status event %s for terminal failed recipient", new_status)
        return "ignored"

    if new_status == "failed":
        # Only accept failure if current status is queued or sent
        if recipient.status not in ("queued", "sent"):
            logger.info(f"Ignoring 'failed' event — current status is {recipient.status}")
            return "ignored"
        recipient.status = "failed"
        recipient.failed_at = timezone.now()
        err_code = error_code or "delivery_failed"
        recipient.error_code = err_code
        recipient.friendly_message = get_friendly_message(err_code)
        recipient.retryable = is_retryable(err_code)
    elif new_rank > current_rank:
        # Only advance forward
        recipient.status = new_status
        if new_status == "sent":
            recipient.sent_at = timezone.now()
        elif new_status == "delivered":
            recipient.delivered_at = timezone.now()
        elif new_status == "read":
            recipient.read_at = timezone.now()
    else:
        logger.info(f"Out-of-order event {new_status} (rank {new_rank}) vs current {recipient.status} (rank {current_rank}) — ignoring status update")
        return "ignored"

    recipient.save()
    return "processed"
