from django.contrib.auth.hashers import (
    check_password,
    make_password,
)

from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.status import HTTP_200_OK, HTTP_406_NOT_ACCEPTABLE, HTTP_400_BAD_REQUEST
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from accounts.serializers import SignUpSerializer, SignInSerializer, ProfileDisplaySerializer,ChangePasswordSerializer,UserBalanceAddSerializer,Countryserializer,SendForgotEmailSerializer,ResetPasswordSerializer,ListTaskSerializer,ListLogsSerializer
from accounts.permissions import IsLoggedIn
from accounts.models import UserAPIKey , User,UserBalance,UserBalanceHistory,Country,Task
from rest_framework.generics import UpdateAPIView
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
import uuid
from django.conf import settings 
from rest_framework import status
from django.core.mail import send_mail
import datetime
from datetime import timedelta
import requests
import json
from django.views.decorators.csrf import csrf_exempt
import threading,queue
from rest_framework.decorators import api_view
from rest_framework.decorators import action
from threading import Thread
from token_auth.settings import FRONTEND_SITE_URL




class SignupView(CreateAPIView):
    serializer_class = SignUpSerializer


    def post(self, request, *args, **kwargs):
        try:
            print(request.data)
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                email = serializer.validated_data['email']
                serializer.save()
                user_inital = User.objects.filter(email=email).first()
                token, created = Token.objects.get_or_create(user= user_inital)
                return Response({'message': 'User Registered Successfully','token': token.key,}, status=status.HTTP_200_OK)
                # return Response({'token': token.key, 'email' : email})
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
        except Exception as e:
            return Response (data='please enter a valide information: '+ str(e),status=status.HTTP_400_BAD_REQUEST)



class SignInView(ObtainAuthToken):
    serializer_class = SignInSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
        # serializer.is_valid()
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            Response_data = {
                'message': "Login Success",
                'first_name': user.first_name,
                'username': user.username,
                'last_name': user.last_name,
                'email': user.email,
                'id': user.id,
                'token': token.key,
                'balance': user.balance.amount

                # 'profile_image_update': user.profile_image_update,
            }
            return Response(Response_data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ProfileUpdateView(IsLoggedIn, RetrieveUpdateAPIView):
    """Display and update User's profile."""
    serializer_class = ProfileDisplaySerializer


    def get_object(self):
        """Return object instance."""
        return self.request.user
        # return self.request.user,{'message': 'Amount add successfully'}


    # def update(self, request, *args, **kwargs):
    #     partial = kwargs.pop('partial', False)
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data, partial=partial)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_update(serializer)
    #     return Response(serializer.data,{'message': 'Profile update successfully'})
    

class GetAPIKeyView(IsLoggedIn, APIView):
    """Get API key for user."""


    def get(self, request):
        """Get API key for user."""
        user = request.user
        UserAPIKey.objects.filter(user=user).delete()
        _, key = UserAPIKey.objects.create_key(user=user, prefix=user.email, name=f'Key for {user.email}')
        return Response(status=HTTP_200_OK, data={'key': key})







class BalanceAddView(IsLoggedIn, UpdateAPIView):
    """Add balance for a user."""

    serializer_class = UserBalanceAddSerializer
    http_method_names = ['patch','get' ]


    def get(self, request, format=None):
        snippets = UserBalance.objects.filter(user=request.user.id)
        serializer = UserBalanceAddSerializer(snippets, many=True)
        return Response(serializer.data) 
    

    def get_object(self):
        """Retrieve user object."""
        return get_object_or_404(UserBalance, pk=self.request.user)


    def patch(self, request, *args, **kwargs):
        """Add amount in user balance."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if not serializer.validated_data['amount'] > 0:
            return Response(status=HTTP_400_BAD_REQUEST, data={'message': 'Amount should be greater than 0'})

        amount = UserBalance.update_balance(request.user, serializer.validated_data['amount'])
        UserBalanceHistory.objects.create(user=request.user, amount=serializer.validated_data.get('amount'))
        return Response({'amount': amount,'message': 'Amount add successfully'})


     
class SendMessageView(IsLoggedIn, APIView):


    def get(self, request, format=None):
        snippets = Task.objects.filter(user=request.user.id)
        serializer = ListTaskSerializer(snippets, many=True)
        return Response(serializer.data) 


    @action(detail=False, methods=['post'], url_path='post')
    def post(self,request):
        try:
            phone_number = request.data.get('phone_number')
            compaign_name = request.data.get('compaign_name')
            content = request.data.get('Content')
            country_code = request.data.get('country')   
            user_data = UserBalance.objects.get(user=request.user)
            country_data = Country.objects.get(country=country_code)
            message_price = country_data.price
            total_phone_number = len(phone_number.split(','))
            total_price_for_send_message = total_phone_number*message_price
            if user_data.amount>=total_price_for_send_message:
                user_data = UserBalance.objects.get(user=request.user)
                user_data.amount = user_data.amount-total_price_for_send_message   
                user_data.save() 
                data_obj=Task.objects.create(user=request.user,campaign_name=request.data.get('compaign_name'),phone=phone_number,message=request.data.get('Content'),country=country_data,counter_faild_sms = 0, status="pending")  
                task_id=data_obj.id   
                threading.Thread(target=doCrawl,args=[request,task_id],daemon=True).start()
                return Response(status=HTTP_200_OK, data={'message': 'Message send successfully'}) 
            else:    
                Task.objects.create(user=request.user,campaign_name=compaign_name,phone=phone_number,message=content,country=country_data,counter_faild_sms = 0,status="CANCELED")                                
                return Response(status=HTTP_400_BAD_REQUEST, data={'message': 'You have not sufficient balance in your account'})
        except Exception as e:  
            return Response({'message': f'{e} is required'}, status=status.HTTP_400_BAD_REQUEST)

 



def doCrawl(request,task_id):
    phone_number = request.data.get('phone_number').split(',')
    country_code = request.data.get('country')   
    user_data = UserBalance.objects.get(user=request.user)
    country_data = Country.objects.get(country=country_code)
    message_price = country_data.price
    status_count = []
    for number in phone_number:
        data={
            'user':request.user,
            'campaign_name':request.data.get('compaign_name'),
            'phone':number,
            'message':request.data.get('Content'),
            'country':request.data.get('country'),
            'status':"success"
            
            }
        try:  
            r = requests.post('https://app-name20.herokuapp.com/sender/sms',data=data)     
            json_object = json.loads(r.text)  
            status = json_object["status"]
            status_count.append(status)
        except Exception as e:    
            status = None   
    
    if status_count:
        count_error = status_count.count('ERROR')
        if count_error > 0:
            refund_balance = count_error*message_price                        
            user_balance_after_refund = user_data.amount+refund_balance  
            user_data.amount = user_balance_after_refund
            user_data.save() 
            Task.objects.filter(id=task_id).update(counter_faild_sms = count_error, status="success") 
            return Response(status=HTTP_200_OK, data={'message': 'Message successfully sent'})  
        if count_error == 0:
            Task.objects.filter(id=task_id).update(counter_faild_sms = 0, status="success") 
            return Response(status=HTTP_200_OK, data={'message': 'Message successfully sent'})    
    return Response(status=HTTP_200_OK, data={'message': 'Message successfully sent'}) 
                          


class SignOutView(IsLoggedIn, APIView):
    """Sign Out User."""

    def get(self, request):
        """Sign Out User on Get Request."""
        request.user.auth_token.delete()
        return Response(status=HTTP_200_OK)
    


class CountryViewSet(viewsets.ModelViewSet):
    serializer_class = Countryserializer
    queryset = Country.objects.all()


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        all_country_data = Country.objects.values_list('country', flat=True)
        all_country = request.data.get('country')
        price = request.data.get('price')
        if all_country in all_country_data:
            return Response({'message': 'Country already exists '}, status=status.HTTP_400_BAD_REQUEST)
        Country.objects.create(country=all_country, price=price)
        return Response({'message': 'Country successfully add'},status=HTTP_200_OK,)      


   
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        if serializer.is_valid(raise_exception=True):
            self.perform_update(serializer)
            context = {
                'message': 'Country successfully updated',
                'status': status.HTTP_200_OK,
                'errors': serializer.errors,
                'data': serializer.data,
            }
            return Response(context)
        else:
            return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)    



    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        context = {
            'message': 'Country successfully deleted',
            'status': status.HTTP_204_NO_CONTENT,
            'errors': False,
        }
        return Response(context)     



class ForgetPassword(APIView):
    serializer_class = SendForgotEmailSerializer
    
    def post(self, request):
        protocol = request.scheme
        # domain = request.get_host()
        domain = FRONTEND_SITE_URL
        email = request.data
        serializer = SendForgotEmailSerializer(data=email)
        if serializer.is_valid(raise_exception=True):
            email = request.data['email']
            user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.filter(username=email).first()
                return Response({'message': 'Email does not exists'}, status=status.HTTP_400_BAD_REQUEST)
            token = str(uuid.uuid4())
            token_expire_time = datetime.datetime.utcnow() + timedelta(minutes=3)
            user.token_expire_time = token_expire_time
            user.forgot_password_token = token
            user.save()
            user_id = user.id
            email_from = settings.EMAIL_HOST_USER
            subject = 'Forgot Password Email'
            message = "\n\n\n\nHI " + str(user.username) + " \n\n link to reset password is : " + str(
                protocol) + "/" + str(domain) + "/reset-password/" + str(token) + "/" + str(user_id)
            restUrl =  str(domain)+"/reset-password/" + str(token) + "/" + str(user_id)+"/"

            htmlMessage = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\
                        <html xmlns="http://www.w3.org/1999/xhtml">\
                        <head>\
                            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\
                            <title>Mongo DB</title>\
                            <meta name="viewport" content="width=device-width, initial-scale=1.0" /> </head>\
                        <body style="margin: 0; padding: 0; background: #eee;">\
                            <div style="background: rgba(36, 114, 252, 0.06) !important;">\
                            <table style="font: Arial, sans-serif; border-collapse: collapse; width:600px; margin: 0 auto;" width="600" cellpadding="0" cellspacing="0">\
                                <tbody>\
                                <tr>\
                                    <td style="width: 100%; margin: 36px 0 0;">\
                                    <div style="padding: 34px 44px; border-radius: 8px !important; background: #fff; border: 1px solid #dddddd5e; margin-bottom: 50px; margin-top: 50px;">\
                                        <div class="email-logo">\
                                        <img style="width: 165px;" src="https://webimages.mongodb.com/_com_assets/cms/kuzt9r42or1fxvlq2-Meta_Generic.png" />\
                                        </div>\
                                        <a href="#"></a>\
                                        <div class="welcome-text">\
                                        <h1 style="font:24px;"> Welcome <span class="welcome-hand">👋</span>\
                                        </h1>\
                                        </div>\
                                        <div class="welcome-paragraph">\
                                        <div style="padding: 20px 0px; font-size:16px; color: #384860;">Welcome to Sevesms!</div>\
                                        <div style="padding:10px 0px; font-size: 16px; color: #384860;">Please click the below link to reset your password. <br />\
                                        </div>\
                                        <div style="padding: 20px 0px; font-size: 16px; color: #384860;"> Sincerely, <br />The Sevesms Team </div>\
                                        </div>\
                                        <div style="padding-top:40px; cursor: pointer !important;" class="confirm-email-button">\
                                        <a href="'+restUrl+'" style="cursor: pointer;">\
                                            <button style="height: 56px;padding: 15px 44px; background: #2472fc; border-radius: 8px;border-style: none; color: white; font-size: 16px; cursor: pointer !important;">Reset Password</button>\
                                        </a>\
                                        </div>\
                                        <div style="padding: 50px 0px;" class="email-bottom-para">\
                                        <div style="padding: 20px 0px; font-size:16px; color: #384860;">This email was sent by Sevesms. If you&#x27;d rather not receive this kind of email, Don’t want any more emails from Sevesms? <a href="#">\
                                            <span style="text-decoration:underline;"> Unsubscribe.</span>\
                                            </a>\
                                        </div>\
                                        <div style="font-size: 16px;color: #384860;"> © 2023 Sevesms</div>\
                                        </div>\
                                    </div>\
                                    </td>\
                                </tr>\
                                </tbody>\
                            </table>\
                            </div>\
                        </body>\
                        </html>'
            try:
                send_mail(subject,message, email_from,[email], html_message=htmlMessage, fail_silently=False,)
                return Response({'message': 'Email successfully sent, please check your email'},status=status.HTTP_200_OK)      
            except Exception as e:
                pass
        else:
            return Response({'message': 'There is an error to sending the data'},status=status.HTTP_400_BAD_REQUEST)


class ListTaskView(IsLoggedIn, APIView):
        
    def get(self, request, format=None):    
        snippets = Task.objects.filter(user=request.user.id).order_by('-id')
        serializer = ListTaskSerializer(snippets, many=True)
        return Response(serializer.data) 




class GetBalanceView(IsLoggedIn, APIView):
        
    def get(self, request, format=None):
            snippets = UserBalance.objects.filter(user=request.user.id)
            serializer = UserBalanceAddSerializer(snippets, many=True)
            return Response(serializer.data)         


class ResetPassword(APIView):
    serializer_class = ResetPasswordSerializer
    lookup_url_kwarg = "token"
    lookup_url_kwarg2 = "uid"

    def get(self, request, *args, **kwargs):
        serializer_class = ResetPasswordSerializer
        token = self.kwargs.get(self.lookup_url_kwarg)
        uid = self.kwargs.get(self.lookup_url_kwarg2)
        user_data = User.objects.filter(id=uid).first()
        if not user_data.forgot_password_token:
            return Response({'token_expire': 'Token Expired'}, status=status.HTTP_400_BAD_REQUEST)
        if token != user_data.forgot_password_token:
            return Response({'token_expire': 'Token Expired'}, status=status.HTTP_400_BAD_REQUEST)

        token_expire_time = user_data.token_expire_time.replace(tzinfo=None)
        current_expire_time = datetime.datetime.utcnow()
        if current_expire_time > token_expire_time:
            return Response({'token_expire': 'Token Expired'}, status=status.HTTP_400_BAD_REQUEST)

        context = {
            'token_expire_time': token_expire_time
            # 'current_expire_time': current_expire_time
        }
        response = Response(context, status=status.HTTP_200_OK)
        return response
    
    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = request.data['password']
        confirm_password = request.data['confirm_password']

        if password != confirm_password:
            return Response({'message': 'Password and Confirm Password do not match'},status=status.HTTP_400_BAD_REQUEST)
        user_id = self.kwargs.get(self.lookup_url_kwarg2)
        user_data = User.objects.get(id=user_id)
        user_data.set_password(password)
        user_data.forget_password_token = None
        user_data.save()
        if user_data != 0: 
            return Response({'message': 'Password successfully changed'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'There is an error to updating the data'}, status=status.HTTP_400_BAD_REQUEST)




class PasswordChange(IsLoggedIn,APIView):
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        data = self.serializer_class(data=request.data)
        if data.is_valid():
            new_password = data.validated_data.get('new_password', None)
            confirm_password = data.validated_data.get('confirm_password', None)
            current_password = data.validated_data.get('current_password', None)
            user = User.objects.filter(id=request.user.id).first()
            if new_password != confirm_password:
                return Response({'message': 'New Password and Confirm Password do not match'},
                                status=status.HTTP_400_BAD_REQUEST)
            if not user.check_password(current_password):
                context = {
                    'message': 'Current password does not match.'
                }
                return Response(context, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
            user.save()
            if user:
                return Response({'message': 'Your Password Changed Successfully.'}, status=status.HTTP_200_OK) 
            else:
                return Response({'message': 'There is an error to changing the password'},status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response({'message': data.errors}, status=status.HTTP_400_BAD_REQUEST)



class ListLogsView(IsLoggedIn, APIView):
        
    def get(self, request, format=None):    
        snippets = Task.objects.filter(user=request.user.id).order_by('-id')
        serializer = ListLogsSerializer(snippets, many=True)
        return Response(serializer.data) 
