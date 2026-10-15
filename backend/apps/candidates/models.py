import random
import string
from django.db import models
from django.utils import timezone


def generate_candidate_id() -> str:
    """Generate 6-character alphanumeric ID e.g., 'A1B2C3'."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=6))


class Candidate(models.Model):
    candidate_id = models.CharField(max_length=12, unique=True, default=generate_candidate_id, db_index=True)
    name = models.CharField(max_length=80)
    phone = models.CharField(max_length=30)
    email = models.EmailField(max_length=120)
    is_deleted = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidates"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.candidate_id})"
