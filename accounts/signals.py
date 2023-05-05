from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from accounts.models import User,UserBalance
from django_rest_passwordreset.signals import reset_password_token_created



@receiver(post_save, sender=get_user_model())
def create_balance(sender, instance, created, **kwargs):
    if created:
        data = UserBalance.objects.create(user=instance)
        print(data)
        data.save()
