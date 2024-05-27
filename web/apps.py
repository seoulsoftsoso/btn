from django.apps import AppConfig

from button.ws import mongo_updates

class YourAppConfig(AppConfig):
    name = 'web'

    def ready(self):
        mongo_updates.listen_to_changes()
class WebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web'
