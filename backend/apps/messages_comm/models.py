import uuid
from django.db import models
from django.utils import timezone
from apps.candidates.models import Candidate


def generate_message_uuid():
    return str(uuid.uuid4())


class Message(models.Model):
    message_id = models.CharField(max_length=64, unique=True, default=generate_message_uuid, db_index=True)
    body = models.TextField()
    channel = models.CharField(max_length=30, default="whatsapp")
    scheduled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "messages"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Message {self.message_id[:8]}: {self.body[:30]}"


class MessageRecipient(models.Model):
    STATUS_CHOICES = (
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("read", "Read"),
        ("failed", "Failed"),
        ("scheduled", "Scheduled"),
    )

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="recipients")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="message_recipients")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued", db_index=True)
    channel = models.CharField(max_length=30, default="whatsapp")
    provider_message_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    error_code = models.CharField(max_length=40, null=True, blank=True)
    friendly_message = models.TextField(null=True, blank=True)
    retryable = models.BooleanField(default=False)
    attempt_count = models.IntegerField(default=1)
    idempotency_key = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "message_recipients"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.candidate.name} - {self.status}"
