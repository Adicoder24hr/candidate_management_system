from django.urls import path
from apps.candidates.views import (
    CandidateListCreateView,
    CandidateDetailView,
    CandidateBulkDeleteView,
)
from apps.messages_comm.views import CandidateMessagesView

urlpatterns = [
    path("", CandidateListCreateView.as_view(), name="candidate_list_create"),
    path("bulk-delete", CandidateBulkDeleteView.as_view(), name="candidate_bulk_delete"),
    path("<str:candidate_id>/messages", CandidateMessagesView.as_view(), name="candidate_messages"),
    path("<str:candidate_id>", CandidateDetailView.as_view(), name="candidate_detail"),
]
