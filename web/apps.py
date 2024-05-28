from django.apps import AppConfig

from button.ws import mongo_updates

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web'

