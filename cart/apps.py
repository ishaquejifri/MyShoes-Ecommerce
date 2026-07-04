from django.apps import AppConfig


class CartConfig(AppConfig):
    name = 'cart'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import cart.signals
