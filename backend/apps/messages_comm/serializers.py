from rest_framework import serializers
from apps.messages_comm.models import Message, MessageRecipient
from apps.candidates.models import Candidate
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


class MessageRecipientSerializer(serializers.ModelSerializer):
    candidate_id = serializers.SerializerMethodField()
    candidate_name = serializers.SerializerMethodField()
    message_body = serializers.SerializerMethodField()
    status_raw = serializers.SerializerMethodField()
    recipient_id = serializers.SerializerMethodField()

    class Meta:
        model = MessageRecipient
        fields = [
            "recipient_id",
            "candidate_id",
            "candidate_name",
            "message_body",
            "status",
            "status_raw",
            "provider_message_id",
            "error_code",
            "friendly_message",
            "retryable",
            "attempt_count",
            "sent_at",
            "delivered_at",
            "read_at",
            "failed_at",
            "created_at",
            "updated_at",
        ]

    def get_recipient_id(self, obj) -> str:
        return str(obj.pk)

    def get_candidate_id(self, obj) -> str:
        return obj.candidate.candidate_id

    def get_candidate_name(self, obj) -> str:
        return obj.candidate.name

    def get_message_body(self, obj) -> str:
        return obj.message.body if obj.message else ""

    def get_status_raw(self, obj) -> str:
        return obj.status


class CandidateHistorySerializer(serializers.ModelSerializer):
    """Flat history item for the history drawer."""
    recipient_id = serializers.SerializerMethodField()
    message_id = serializers.SerializerMethodField()
    message_body = serializers.SerializerMethodField()
    status_raw = serializers.SerializerMethodField()

    class Meta:
        model = MessageRecipient
        fields = [
            "recipient_id",
            "message_id",
            "message_body",
            "status",
            "status_raw",
            "error_code",
            "friendly_message",
            "retryable",
            "attempt_count",
            "created_at",
            "updated_at",
        ]

    def get_recipient_id(self, obj) -> str:
        return str(obj.pk)

    def get_message_id(self, obj) -> str:
        return obj.message.message_id if obj.message else ""

    def get_message_body(self, obj) -> str:
        return obj.message.body if obj.message else ""

    def get_status_raw(self, obj) -> str:
        return obj.status
