from django.urls import path
from apps.webhooks.views import provider_webhook

urlpatterns = [
    path("provider/", provider_webhook, name="provider_webhook"),
]
