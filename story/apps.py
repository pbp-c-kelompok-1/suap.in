from django.apps import AppConfig


class StoryConfig(AppConfig):
    name = 'story'

    def ready(self):
        # import di sini supaya signal terdaftar setelah model siap
        from . import signals