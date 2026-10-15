from django.urls import path, include
from apps.common.views import health_check, provider_health

urlpatterns = [
    # Health
    path("api/v1/health", health_check, name="backend_health"),
    path("api/v1/health/provider", provider_health, name="provider_health"),

    # Candidates (includes candidate history at /candidates/<id>/messages)
    path("api/v1/candidates/", include("apps.candidates.urls")),
    path("api/v1/candidates", include("apps.candidates.urls")),

    # Messages (bulk send, retry)
    path("api/v1/messages/", include("apps.messages_comm.urls")),
    path("api/v1/messages", include("apps.messages_comm.urls")),

    # Webhooks
    path("api/v1/webhooks/", include("apps.webhooks.urls")),
]
