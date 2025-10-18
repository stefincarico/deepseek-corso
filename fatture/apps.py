from django.apps import AppConfig


class FattureConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fatture'

    def ready(self):
        import fatture.signals
