import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from apps.candidates.models import Candidate
from apps.messages_comm.models import MessageRecipient
from apps.messages_comm.serializers import CandidateHistorySerializer, MessageRecipientSerializer
from apps.messages_comm.services import bulk_send, retry_recipient

logger = logging.getLogger(__name__)


class BulkSendView(APIView):
    """
    POST /api/v1/messages/bulk
    Body: { "candidate_ids": [...], "body": "..." }
    Each recipient is processed independently.
    """

    def post(self, request):
        candidate_ids = request.data.get("candidate_ids", [])
        body = request.data.get("body", "").strip()

        if not isinstance(candidate_ids, list) or not candidate_ids:
            return Response({
                "error": {
                    "code": "validation_error",
                    "message": "A non-empty list of 'candidate_ids' is required.",
                    "fields": {"candidate_ids": "This field is required."}
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        if not body:
            return Response({
                "error": {
                    "code": "validation_error",
                    "message": "Message body is required.",
                    "fields": {"body": "This field is required."}
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(body) > 4096:
            return Response({
                "error": {
                    "code": "validation_error",
                    "message": "Message body must be at most 4096 characters.",
                    "fields": {"body": "Too long."}
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        result = bulk_send(candidate_ids=candidate_ids, body=body)
        return Response(result, status=status.HTTP_200_OK)


class SingleSendView(APIView):
    """POST /api/v1/messages for one candidate."""

    def post(self, request):
        candidate_id = request.data.get("candidate_id")
        body = request.data.get("body", "").strip()
        if not candidate_id or not isinstance(candidate_id, str):
            return Response({"error": {"code": "validation_error", "message": "Candidate is required.", "fields": {"candidate_id": "This field is required."}}}, status=status.HTTP_400_BAD_REQUEST)
        if not body or len(body) > 4096:
            return Response({"error": {"code": "validation_error", "message": "Enter a message up to 4096 characters.", "fields": {"body": "This field is required and must be at most 4096 characters."}}}, status=status.HTTP_400_BAD_REQUEST)
        result = bulk_send(candidate_ids=[candidate_id], body=body)
        if result["total"] == 0:
            return Response({"error": {"code": "not_found", "message": "Candidate not found.", "fields": {"candidate_id": "Candidate not found."}}}, status=status.HTTP_404_NOT_FOUND)
        return Response(result["results"][0], status=status.HTTP_200_OK)


class CandidateMessagesView(APIView):
    """
    GET /api/v1/candidates/{candidate_id}/messages
    Returns message history newest-first.
    """

    def get(self, request, candidate_id):
        try:
            candidate = Candidate.objects.get(candidate_id=candidate_id, is_deleted=False)
        except Candidate.DoesNotExist:
            return Response({
                "error": {
                    "code": "not_found",
                    "message": f"Candidate '{candidate_id}' not found.",
                    "fields": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        recipients = (
            MessageRecipient.objects
            .filter(candidate=candidate)
            .select_related("message")
            .order_by("-created_at")
        )
        serializer = CandidateHistorySerializer(recipients, many=True)
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)


class MessageRetryView(APIView):
    """
    POST /api/v1/messages/{recipient_id}/retry
    """

    def post(self, request, recipient_id):
        recipient = retry_recipient(recipient_id)
        if recipient is None:
            return Response({
                "error": {
                    "code": "not_found",
                    "message": f"Message recipient '{recipient_id}' not found.",
                    "fields": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        if not recipient.retryable and recipient.status == "failed":
            return Response({
                "error": {
                    "code": "not_retryable",
                    "message": f"Can't be retried: {recipient.friendly_message}",
                    "fields": {}
                }
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        serializer = MessageRecipientSerializer(recipient)
        return Response(serializer.data, status=status.HTTP_200_OK)
