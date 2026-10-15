from typing import Any

from apps.messages_comm.models import MessageRecipient
from apps.webhooks.models import WebhookEvent
from apps.messages_comm.services import process_webhook_event


class FakeQuery:
    def __init__(self, exists: bool = False) -> None:
        self._exists = exists

    def exists(self) -> bool:
        return self._exists

    def first(self) -> Any:
        return None


class FakeRecipient:
    def __init__(self, status: str) -> None:
        self.status = status
        self.saved = False

    def save(self) -> None:
        self.saved = True


class FakeEventManager:
    def __init__(self, duplicate: bool = False) -> None:
        self.duplicate = duplicate
        self.filters: list[dict[str, str]] = []
        self.created: list[dict[str, Any]] = []

    def filter(self, **kwargs: str) -> FakeQuery:
        self.filters.append(kwargs)
        return FakeQuery(self.duplicate)

    def create(self, **kwargs: Any) -> None:
        self.created.append(kwargs)


class FakeRecipientManager:
    def __init__(self, recipient: FakeRecipient) -> None:
        self.recipient = recipient

    def get(self, **kwargs: str) -> FakeRecipient:
        return self.recipient


def test_duplicate_event_is_idempotent_by_provider_and_event_id(monkeypatch) -> None:
    manager = FakeEventManager(duplicate=True)
    monkeypatch.setattr(WebhookEvent, "objects", manager)
    event = {"provider_message_id": "provider-1", "event_id": "event-1", "status": "sent"}

    assert process_webhook_event(event) == "duplicate"
    assert manager.filters[0] == {"provider_message_id": "provider-1", "event_id": "event-1"}
    assert not manager.created


def test_late_queued_event_cannot_reopen_failed_recipient(monkeypatch) -> None:
    events = FakeEventManager()
    recipient = FakeRecipient("failed")
    monkeypatch.setattr(WebhookEvent, "objects", events)
    monkeypatch.setattr(MessageRecipient, "objects", FakeRecipientManager(recipient))
    event = {"provider_message_id": "provider-2", "event_id": "event-2", "status": "queued"}

    assert process_webhook_event(event) == "ignored"
    assert len(events.created) == 1
    assert recipient.status == "failed"
    assert not recipient.saved
