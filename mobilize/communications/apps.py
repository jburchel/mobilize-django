from django.apps import AppConfig


class CommunicationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mobilize.communications"
    verbose_name = "Communications"

    def ready(self):
        # Import signal handlers
        import mobilize.communications.signals
