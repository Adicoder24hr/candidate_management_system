import re
from typing import Optional, Dict, Any, Tuple
import phonenumbers
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from apps.candidates.models import Candidate
from apps.messages_comm.models import MessageRecipient


class ConflictError(Exception):
    def __init__(self, message: str, fields: Dict[str, str]):
        super().__init__(message)
        self.message = message
        self.fields = fields


def normalize_phone_number(raw_phone: str) -> str:
    """
    Validate and normalize phone number into standard E.164 format.
    Accepts valid numbers with or without leading '+'. Defaults region to 'IN' if omitted.
    """
    cleaned = raw_phone.strip()
    if not cleaned:
        raise ValidationError({"phone": "Mobile number is required."})

    try:
        if not cleaned.startswith("+"):
            # Assume India (+91) if country code is omitted
            parsed = phonenumbers.parse(cleaned, "IN")
        else:
            parsed = phonenumbers.parse(cleaned, None)

        if not phonenumbers.is_valid_number(parsed):
            raise ValidationError({"phone": "Please enter a valid mobile number in E.164 format (e.g. +919876543210)."})

        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        raise ValidationError({"phone": "Invalid phone number format."})


def validate_candidate_uniqueness(phone: str, email: str, exclude_id: Optional[str] = None):
    """
    Verify uniqueness among active (non-deleted) candidates.
    Raises ConflictError (409) if duplicate phone or email exists.
    """
    base_query = Candidate.objects.filter(is_deleted=False)
    if exclude_id:
        base_query = base_query.exclude(candidate_id=exclude_id)

    conflicts = {}
    if base_query.filter(phone=phone).exists():
        conflicts["phone"] = "A candidate with this phone number already exists."
    if base_query.filter(email__iexact=email).exists():
        conflicts["email"] = "A candidate with this email address already exists."

    if conflicts:
        raise ConflictError(
            message="A candidate with this phone number or email already exists.",
            fields=conflicts
        )


def create_candidate(name: str, raw_phone: str, email: str) -> Candidate:
    """
    Create a new candidate with full validation.
    """
    clean_name = name.strip()
    if len(clean_name) < 2 or len(clean_name) > 80:
        raise ValidationError({"name": "Full name must be between 2 and 80 characters."})

    clean_email = email.strip().lower()
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, clean_email):
        raise ValidationError({"email": "Please enter a valid email address."})

    normalized_phone = normalize_phone_number(raw_phone)
    validate_candidate_uniqueness(phone=normalized_phone, email=clean_email)

    candidate = Candidate.objects.create(
        name=clean_name,
        phone=normalized_phone,
        email=clean_email,
        is_deleted=False
    )
    return candidate


def soft_delete_candidate(candidate_id: str) -> bool:
    """
    Soft delete candidate by candidate_id.
    """
    try:
        candidate = Candidate.objects.get(candidate_id=candidate_id, is_deleted=False)
        candidate.is_deleted = True
        candidate.save()
        return True
    except Candidate.DoesNotExist:
        return False


def soft_delete_multiple_candidates(candidate_ids: list) -> int:
    """
    Soft delete candidates in bulk.
    """
    updated_count = Candidate.objects.filter(
        candidate_id__in=candidate_ids,
        is_deleted=False
    ).update(is_deleted=True)
    return updated_count
