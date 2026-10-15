import asyncio
import hashlib
import hmac
import json
import os
import random
import time
import uuid
from typing import Optional, Dict, Any
from fastapi import FastAPI, Header, HTTPException, Response, status, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Dummy Candidate Messaging Provider Service", version="1.0.0")

WEBHOOK_SECRET = os.getenv("PROVIDER_WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    raise RuntimeError("PROVIDER_WEBHOOK_SECRET must be configured in the environment.")
DEFAULT_CALLBACK_URL = os.getenv("BACKEND_WEBHOOK_URL", "http://localhost:8000/api/v1/webhooks/provider/")

# In-memory state
outage_mode: bool = False
attempts_counter: Dict[str, int] = {}
messages_db: Dict[str, Dict[str, Any]] = {}
idempotency_db: Dict[str, str] = {}


class MessagePayload(BaseModel):
    to_phone: str
    message: str
    callback_url: Optional[str] = None
    idempotency_key: Optional[str] = None
    channel: Optional[str] = "whatsapp"


class OutagePayload(BaseModel):
    on: bool


def generate_hmac_signature(secret: str, payload_str: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        payload_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


async def send_webhook(callback_url: str, event_data: dict):
    payload_str = json.dumps(event_data, separators=(",", ":"))
    signature = generate_hmac_signature(WEBHOOK_SECRET, payload_str)
    headers = {
        "Content-Type": "application/json",
        "X-Provider-Signature": signature
    }
    
    # Non-blocking async HTTP request
    import urllib.request
    import urllib.error

    def do_post():
        req = urllib.request.Request(
            callback_url,
            data=payload_str.encode("utf-8"),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status
        except Exception as e:
            return str(e)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, do_post)


async def simulate_message_lifecycle(provider_msg_id: str, phone: str, callback_url: str):
    clean_phone = phone.replace(" ", "").replace("-", "")
    
    # Deterministic branch for phone ending 0500: accepted, then fails with delivery_failed
    if clean_phone.endswith("0500"):
        await asyncio.sleep(1.2 + random.uniform(0.1, 0.4))
        # Sent event first
        sent_event = {
            "event_id": str(uuid.uuid4()),
            "provider_message_id": provider_msg_id,
            "status": "sent",
            "timestamp": int(time.time() * 1000)
        }
        await send_webhook(callback_url, sent_event)
        
        await asyncio.sleep(1.5 + random.uniform(0.1, 0.5))
        fail_event = {
            "event_id": str(uuid.uuid4()),
            "provider_message_id": provider_msg_id,
            "status": "failed",
            "error_code": "delivery_failed",
            "error_message": "The message couldn't be delivered to the recipient.",
            "timestamp": int(time.time() * 1000)
        }
        messages_db[provider_msg_id]["status"] = "failed"
        await send_webhook(callback_url, fail_event)
        return

    # Standard progression: sent -> delivered -> read
    # Add random chance to swap delivered and read or duplicate an event
    will_duplicate = (random.random() < 0.20)
    will_out_of_order = (random.random() < 0.15)
    
    # 1. Sent (~1.0s)
    await asyncio.sleep(1.0 + random.uniform(0.1, 0.5))
    sent_event = {
        "event_id": str(uuid.uuid4()),
        "provider_message_id": provider_msg_id,
        "status": "sent",
        "timestamp": int(time.time() * 1000)
    }
    messages_db[provider_msg_id]["status"] = "sent"
    await send_webhook(callback_url, sent_event)
    
    if will_duplicate:
        # Send exact duplicate event to test idempotency
        await asyncio.sleep(0.2)
        await send_webhook(callback_url, sent_event)

    # 2. Delivered (~3.0s) & Read (~6.0s)
    if will_out_of_order:
        # Send read before delivered
        await asyncio.sleep(2.0 + random.uniform(0.2, 0.5))
        read_event = {
            "event_id": str(uuid.uuid4()),
            "provider_message_id": provider_msg_id,
            "status": "read",
            "timestamp": int(time.time() * 1000)
        }
        messages_db[provider_msg_id]["status"] = "read"
        await send_webhook(callback_url, read_event)
        
        await asyncio.sleep(1.0)
        deliv_event = {
            "event_id": str(uuid.uuid4()),
            "provider_message_id": provider_msg_id,
            "status": "delivered",
            "timestamp": int(time.time() * 1000)
        }
        await send_webhook(callback_url, deliv_event)
    else:
        # Standard in-order delivery
        await asyncio.sleep(2.0 + random.uniform(0.1, 0.5))
        deliv_event = {
            "event_id": str(uuid.uuid4()),
            "provider_message_id": provider_msg_id,
            "status": "delivered",
            "timestamp": int(time.time() * 1000)
        }
        messages_db[provider_msg_id]["status"] = "delivered"
        await send_webhook(callback_url, deliv_event)

        await asyncio.sleep(3.0 + random.uniform(0.2, 0.8))
        read_event = {
            "event_id": str(uuid.uuid4()),
            "provider_message_id": provider_msg_id,
            "status": "read",
            "timestamp": int(time.time() * 1000)
        }
        messages_db[provider_msg_id]["status"] = "read"
        await send_webhook(callback_url, read_event)


@app.get("/health")
def health_check():
    if outage_mode:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "down", "outage": True, "error": "provider_down"}
        )
    return {"status": "ok", "outage": False, "service": "dummy-provider"}


@app.post("/admin/outage")
def set_outage(payload: OutagePayload):
    global outage_mode
    outage_mode = payload.on
    return {"status": "ok", "outage": outage_mode}


@app.post("/v1/messages")
def send_message(payload: MessagePayload, background_tasks: BackgroundTasks, response: Response):
    global outage_mode
    
    if outage_mode:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "provider_down",
                    "message": "The messaging service is currently unavailable.",
                    "retryable": True
                }
            }
        )

    clean_phone = payload.to_phone.replace(" ", "").replace("-", "")

    # Deterministic suffix matching
    if clean_phone.endswith("0000"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": {
                    "code": "invalid_recipient",
                    "message": "This phone number isn't valid or can't receive messages.",
                    "retryable": False
                }
            }
        )
    
    if clean_phone.endswith("0429"):
        response.headers["Retry-After"] = "5"
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "code": "rate_limited",
                    "message": "Too many messages sent. We'll retry shortly.",
                    "retryable": True
                }
            }
        )

    if clean_phone.endswith("0503"):
        current_attempts = attempts_counter.get(clean_phone, 0) + 1
        attempts_counter[clean_phone] = current_attempts
        if current_attempts < 3:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "temporary_failure",
                        "message": "The messaging service had a temporary problem.",
                        "retryable": True,
                        "attempt": current_attempts
                    }
                }
            )

    if payload.idempotency_key and payload.idempotency_key in idempotency_db:
        existing_id = idempotency_db[payload.idempotency_key]
        response.status_code = status.HTTP_202_ACCEPTED
        return {
            "provider_message_id": existing_id,
            "status": messages_db[existing_id]["status"],
            "message": "Message was already accepted",
        }

    provider_msg_id = f"prov_{uuid.uuid4().hex[:12]}"
    messages_db[provider_msg_id] = {
        "id": provider_msg_id,
        "to_phone": payload.to_phone,
        "message": payload.message,
        "status": "queued",
        "created_at": time.time()
    }
    if payload.idempotency_key:
        idempotency_db[payload.idempotency_key] = provider_msg_id

    callback = payload.callback_url or DEFAULT_CALLBACK_URL
    background_tasks.add_task(simulate_message_lifecycle, provider_msg_id, payload.to_phone, callback)

    response.status_code = status.HTTP_202_ACCEPTED
    return {
        "provider_message_id": provider_msg_id,
        "status": "queued",
        "message": "Message accepted for delivery"
    }


@app.get("/v1/messages/{msg_id}")
def get_message_status(msg_id: str):
    if msg_id not in messages_db:
        raise HTTPException(status_code=404, detail="Message not found")
    return messages_db[msg_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
