from django.apps import AppConfig

from button.ws import mongo_updates

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web'

    def ready(self):
        from button.ws.mongo_updates import start_listening_to_changes
        start_listening_to_changes()
