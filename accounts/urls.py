from accounts import views
from django.urls import path, include
from rest_framework import routers
from .views import *
from accounts.views import (
    SignupView,
    SignInView,
    ProfileUpdateView,
    SignOutView,
    GetAPIKeyView,
    BalanceAddView,
    ForgetPassword,
    ResetPassword,
    ListTaskView,
    GetBalanceView,
    ListLogsView
   
)
router = routers.SimpleRouter()
router.register(r'country', CountryViewSet)



urlpatterns = [
    path('user/signup', SignupView.as_view(), name='sign-up'),
    path('user/signin', SignInView.as_view(), name='sign-in'),
    path('user/signout', SignOutView.as_view(), name='sign-out'),
    path('user/update_profile', ProfileUpdateView.as_view(), name='update_profile'),
    path('user/key/', GetAPIKeyView.as_view(), name='profile'),
    path('user/add_balance', BalanceAddView.as_view(), name='add-balance'),
    path('user/create_task/', SendMessageView.as_view(), name='create_task'),
    path('user/forgot_password/', ForgetPassword.as_view(), name='forgot_password'),
    path('reset_password/<token>/<uid>/',ResetPassword.as_view(), name='reset_password'),
    path('user/all_task/', ListTaskView.as_view(), name='all_task'),
    path('user/get_balance/', GetBalanceView.as_view(), name='get_balance'),
    path('user/password-change', PasswordChange.as_view(), name='password_change'),
    path('user/get_logs', ListLogsView.as_view(), name='get_logs'),
]

urlpatterns += router.urls 






