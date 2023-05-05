from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import EmailValidator
from rest_framework_api_key.models import AbstractAPIKey
from accounts.managers import UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.db import transaction
from django_countries.fields import CountryField
from phone_field import PhoneField



class BaseClass(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    


class Country(models.Model):
    country = CountryField()
    price=models.FloatField()
    created_at=models.DateTimeField(auto_now_add=True)
    update_at=models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)



class User(AbstractBaseUser):
    """Custom User model that uses email instead of username."""

    email = models.EmailField(
        verbose_name='email address', max_length=175,
        unique=True, validators=[EmailValidator, ]
    )
    username = models.CharField(max_length=100,null=True,unique=True,)
    first_name = models.CharField(max_length=30, null=True)
    last_name = models.CharField(max_length=30, null=True)
    forgot_password_token = models.CharField(max_length=100,blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    token_expire_time = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()


    def __str__(self):
        """Represent instance of this class."""
        return self.email


    def has_perm(self, perm: str, obj: object = None):
        """Check for specific permission."""
        return True


    def has_module_perms(self, app_label: str):
        """Check user permission to view app_label."""
        return True

   

class UserAPIKey(AbstractAPIKey):
    """API keys for users to get numbers."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='api_key')
    prefix = models.CharField(max_length=175, unique=True, editable=False)



class UserBalance(models.Model):
    """Balance for every user."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='balance', primary_key=True)
    amount = models.FloatField(default=0, validators=[MinValueValidator(0.0), ])

    @staticmethod
    def update_balance(user, amount):
        """Update balance for user."""
        with transaction.atomic():
            user.balance.amount += amount
            user.balance.save()
        return user.balance.amount

    @staticmethod
    def has_balance(user, amount):
        """Check if a user has sufficient balance."""
        with transaction.atomic():
            return True if user.balance.amount >= amount else False



class UserBalanceHistory(models.Model):
    """Balance history for every user."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='balance_history')
    amount = models.FloatField(validators=[MinValueValidator(0.0), ])



class Task(BaseClass):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    campaign_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255,blank=True,null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    # country = CountryField()
    message = models.TextField(blank=True,null=True)
    status = models.CharField(max_length=255, blank=True,null=True)
    counter_faild_sms = models.PositiveIntegerField()
    modified = models.DateTimeField(auto_now=True, editable=False)
   
