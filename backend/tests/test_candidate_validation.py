import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apps.candidates.services import normalize_phone_number
from apps.candidates.views import CandidateListCreateView
from apps.messages_comm.views import SingleSendView


def test_normalize_indian_phone_without_country_code() -> None:
    assert normalize_phone_number("9876543210") == "+919876543210"


def test_normalize_e164_phone() -> None:
    assert normalize_phone_number("+1 415 555 2671") == "+14155552671"


def test_reject_invalid_phone() -> None:
    with pytest.raises(ValidationError):
        normalize_phone_number("not-a-phone")


def test_candidate_create_endpoint_returns_field_errors() -> None:
    request = APIRequestFactory().post("/api/v1/candidates/", {}, format="json")
    response = CandidateListCreateView.as_view()(request)
    assert response.status_code == 400
    assert "name" in response.data["error"]["fields"]


def test_single_send_requires_candidate_and_message() -> None:
    request = APIRequestFactory().post("/api/v1/messages", {}, format="json")
    response = SingleSendView.as_view()(request)
    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"
