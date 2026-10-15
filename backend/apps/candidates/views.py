from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from apps.candidates.models import Candidate
from apps.candidates.serializers import CandidateListSerializer, CandidateCreateSerializer
from apps.candidates.services import (
    create_candidate,
    soft_delete_candidate,
    soft_delete_multiple_candidates,
    ConflictError,
)


class CandidateListCreateView(APIView):
    """
    List candidates (with search, pagination, sorting) and add new candidates.
    """

    def get(self, request):
        queryset = Candidate.objects.filter(is_deleted=False)

        # 1. Search (debounced, server-side)
        search_query = request.query_params.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(candidate_id__icontains=search_query)
            )

        # 2. Sorting
        ordering = request.query_params.get("ordering", "-created_at")
        allowed_ordering = {
            "name": "name",
            "-name": "-name",
            "phone": "phone",
            "-phone": "-phone",
            "candidate_id": "candidate_id",
            "-candidate_id": "-candidate_id",
            "created_at": "created_at",
            "-created_at": "-created_at",
        }
        order_field = allowed_ordering.get(ordering, "-created_at")
        queryset = queryset.order_by(order_field)

        # 3. Pagination
        total_count = queryset.count()
        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except (ValueError, TypeError):
            page = 1

        try:
            page_size = min(100, max(1, int(request.query_params.get("page_size", 10))))
        except (ValueError, TypeError):
            page_size = 10

        start = (page - 1) * page_size
        end = start + page_size
        page_candidates = list(queryset[start:end])

        serializer = CandidateListSerializer(page_candidates, many=True)
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

        return Response({
            "count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "results": serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CandidateCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error": {
                    "code": "validation_error",
                    "message": "Invalid candidate data.",
                    "fields": serializer.errors,
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            candidate = create_candidate(
                name=serializer.validated_data["name"],
                raw_phone=serializer.validated_data["phone"],
                email=serializer.validated_data["email"],
            )
            response_serializer = CandidateListSerializer(candidate)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ConflictError as e:
            return Response({
                "error": {
                    "code": "conflict",
                    "message": e.message,
                    "fields": e.fields,
                }
            }, status=status.HTTP_409_CONFLICT)


class CandidateDetailView(APIView):
    """
    Candidate detail retrieval and soft delete.
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

        serializer = CandidateListSerializer(candidate)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, candidate_id):
        success = soft_delete_candidate(candidate_id)
        if not success:
            return Response({
                "error": {
                    "code": "not_found",
                    "message": f"Candidate '{candidate_id}' not found.",
                    "fields": {}
                }
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "message": "Candidate deleted successfully.",
            "candidate_id": candidate_id
        }, status=status.HTTP_200_OK)


class CandidateBulkDeleteView(APIView):
    """
    Bulk soft delete candidates.
    """

    def post(self, request):
        candidate_ids = request.data.get("candidate_ids", [])
        if not isinstance(candidate_ids, list) or not candidate_ids:
            return Response({
                "error": {
                    "code": "validation_error",
                    "message": "A non-empty list of 'candidate_ids' is required.",
                    "fields": {"candidate_ids": "This field is required."}
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        deleted_count = soft_delete_multiple_candidates(candidate_ids)
        return Response({
            "message": f"{deleted_count} candidate(s) deleted successfully.",
            "deleted_count": deleted_count
        }, status=status.HTTP_200_OK)
