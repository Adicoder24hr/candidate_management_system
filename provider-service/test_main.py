import pytest
from fastapi import BackgroundTasks, HTTPException, Response

import main


def send(phone: str) -> Response:
    response = Response()
    main.send_message(
        main.MessagePayload(to_phone=phone, message="Test", callback_url="http://example.invalid"),
        BackgroundTasks(),
        response,
    )
    return response


def test_invalid_recipient_is_permanent_422() -> None:
    with pytest.raises(HTTPException) as error:
        send("+919876500000")
    assert error.value.status_code == 422
    assert error.value.detail["error"]["code"] == "invalid_recipient"


def test_rate_limited_includes_retry_after() -> None:
    response = Response()
    with pytest.raises(HTTPException) as error:
        main.send_message(
            main.MessagePayload(to_phone="+919876500429", message="Test"),
            BackgroundTasks(),
            response,
        )
    assert error.value.status_code == 429
    assert response.headers["Retry-After"] == "5"


def test_temporary_failure_succeeds_on_third_attempt() -> None:
    phone = "+919876500503"
    main.attempts_counter.pop(phone, None)
    for _ in range(2):
        with pytest.raises(HTTPException) as error:
            send(phone)
        assert error.value.status_code == 503
    assert send(phone).status_code == 202


def test_accepted_idempotency_key_returns_existing_provider_message() -> None:
    key = "retry-safety-test-key"
    first_tasks = BackgroundTasks()
    first = main.send_message(
        main.MessagePayload(to_phone="+919876543210", message="Test", callback_url="http://example.invalid", idempotency_key=key),
        first_tasks,
        Response(),
    )
    second_tasks = BackgroundTasks()
    second = main.send_message(
        main.MessagePayload(to_phone="+919876543210", message="Test", callback_url="http://example.invalid", idempotency_key=key),
        second_tasks,
        Response(),
    )
    assert first["provider_message_id"] == second["provider_message_id"]
    assert len(first_tasks.tasks) == 1
    assert len(second_tasks.tasks) == 0
