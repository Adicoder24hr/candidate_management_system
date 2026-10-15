from django.urls import path
from apps.messages_comm.views import BulkSendView, CandidateMessagesView, MessageRetryView, SingleSendView

urlpatterns = [
    path("", SingleSendView.as_view(), name="message_send"),
    path("bulk", BulkSendView.as_view(), name="bulk_send"),
    path("<str:recipient_id>/retry", MessageRetryView.as_view(), name="message_retry"),
]
