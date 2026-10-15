from django.apps import AppConfig

class MessagesCommConfig(AppConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'
    name = 'apps.messages_comm'
