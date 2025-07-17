from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mobilize.authentication"
    verbose_name = "Authentication"

    def ready(self):
        """Import signals when the app is ready."""
        import mobilize.authentication.signals
