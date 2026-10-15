from django.db import models
from django.utils import timezone


class WebhookEvent(models.Model):
    event_id = models.CharField(max_length=64, db_index=True)
    provider_message_id = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=30)
    signature = models.CharField(max_length=128)
    payload = models.JSONField(default=dict)
    signature_verified = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    received_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "webhook_events"
        ordering = ["-received_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider_message_id", "event_id"],
                name="uniq_provider_message_event",
            ),
        ]

    def __str__(self):
        return f"Event {self.event_id} ({self.status})"
