from django.apps import AppConfig


class EndmonthappConfig(AppConfig):
    name = "core"

    def ready(self):
        import core.signals  # noqa: F401
