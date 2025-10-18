from django.apps import AppConfig

class AcquistiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'acquisti'

    def ready(self):
        import acquisti.signals

    def ready(self):
        import acquisti.signals
