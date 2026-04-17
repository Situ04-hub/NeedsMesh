from django.apps import AppConfig


class NeedsmeshappConfig(AppConfig):
    name = 'NeedsMeshApp'

    def ready(self):
        import NeedsMeshApp.signals
