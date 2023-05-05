from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        import accounts.signals


# from django.apps import AppConfig


# class OrdersConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'orders'

#     def ready(self):
#         import orders.signals
