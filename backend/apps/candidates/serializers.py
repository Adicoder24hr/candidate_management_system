from rest_framework import serializers
from apps.candidates.models import Candidate
from apps.messages_comm.models import MessageRecipient
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


class CandidateCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=80, min_length=2, required=True)
    phone = serializers.CharField(max_length=30, required=True)
    email = serializers.EmailField(max_length=120, required=True)


class CandidateListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    status_raw = serializers.SerializerMethodField()
    latest_message_text = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = [
            "candidate_id",
            "name",
            "phone",
            "email",
            "last_message",
            "status",
            "status_raw",
            "latest_message_text",
            "created_at",
        ]

    def _get_latest_recipient(self, obj):
        # Cache recipient lookup on candidate instance to avoid repeated queries
        if not hasattr(obj, "_latest_recipient_cached"):
            obj._latest_recipient_cached = (
                MessageRecipient.objects.filter(candidate=obj)
                .select_related("message")
                .order_by("-created_at")
                .first()
            )
        return obj._latest_recipient_cached

    def get_last_message(self, obj) -> str:
        recipient = self._get_latest_recipient(obj)
        if not recipient:
            return "NA"
        # Format as DD-MM-YYYY (IST) per Figma mockups
        dt = recipient.created_at.astimezone(IST)
        return dt.strftime("%d-%m-%Y")

    def get_status(self, obj) -> str:
        recipient = self._get_latest_recipient(obj)
        if not recipient:
            return "NA"
        status_map = {
            "read": "read",
            "delivered": "delivered",
            "sent": "Sent",
            "failed": "Failed",
            "queued": "Queued",
            "scheduled": "Scheduled",
        }
        return status_map.get(recipient.status, recipient.status)

    def get_status_raw(self, obj) -> str:
        recipient = self._get_latest_recipient(obj)
        return recipient.status if recipient else "NA"

    def get_latest_message_text(self, obj) -> str:
        recipient = self._get_latest_recipient(obj)
        return recipient.message.body if recipient and recipient.message else ""
