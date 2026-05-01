from django.apps import AppConfig

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    
    def ready(self):
        """Register signal handlers when app is ready."""
        import app.admin_signals  # noqa
        from app.admin_utils import setup_cache_invalidation_signals
        setup_cache_invalidation_signals()  # noqa