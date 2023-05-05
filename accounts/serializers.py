from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from accounts.models import UserBalance,Country,Task,User
from rest_framework.fields import SerializerMethodField



class SignUpSerializer(serializers.ModelSerializer):
    """Create a User."""

    email = serializers.CharField(style={'input_type': 'email'}, write_only=True,
                                     required=True),
    username = serializers.CharField(write_only=True,required=True)                                                               
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True,
                                     required=True, validators=[validate_password])
    confirm_password = serializers.CharField(style={'input_type': 'password'}, write_only=True)    
  

    def validate_email(self, email):
        data = User.objects.filter(email=email)
        if data:
            raise serializers.ValidationError( 'Email already exists')
        return email


    def validate_username(self, username):
        data = User.objects.filter(username=username)
        if data:
            raise serializers.ValidationError( 'Username already exists')
        return username


    def validate(self, attrs):
        """Check if passwords match."""
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs


    def create(self, validated_data):
        """Create user with all validated data."""
        validated_data.pop('confirm_password')
        user = get_user_model().objects.create_user(**validated_data)
        return str(user)
        
        

    class Meta:
        model = get_user_model()
        fields = ['email','password', 'confirm_password','username']

        

class SignInSerializer(serializers.Serializer):
    """Log In User."""

    email = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=True)


    def validate(self, attrs):
        """Validate user's inputs."""
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )

        if not user:
            raise serializers.ValidationError('Please enter valid login details ')

        attrs['user'] = user
        return attrs



class ProfileDisplaySerializer(serializers.ModelSerializer):
    """Display User information."""



    # def validate_email(self, email):
    #     data = User.objects.filter(email=email)
    #     if data:
    #         raise serializers.ValidationError( 'Email already exists')
    #     return email


    # def validate_username(self, username):
    #     data = User.objects.filter(username=username)
    #     if data:
    #         raise serializers.ValidationError( 'Username already exists')
    #     return username
    

    class Meta:
        model = get_user_model()
        fields = ['email', 'username']





class UserBalanceAddSerializer(serializers.ModelSerializer):
    """Add User balance."""

    class Meta:
        model = UserBalance
        fields = ['amount', ]



class Countryserializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = ['id','country','price']



class ListTaskSerializer(serializers.ModelSerializer):
    # country_name = SerializerMethodField("get_country_name")
    class Meta:
        model = Task
        fields = ['id','phone','message','status']


    # def get_country_name(self, obj):
    #     if obj.country:
    #         return str(obj.country.country)
    #     return None        

class ListLogsSerializer(serializers.ModelSerializer):
    # country_name = SerializerMethodField("get_country_name")
    class Meta:
        model = Task
        fields = '__all__'

class SendForgotEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)



class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True,
                                     required=True, validators=[validate_password])
    confirm_password = serializers.CharField(style={'input_type': 'password'}, write_only=True,
                                             required=True, validators=[validate_password])



class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=200, required=True)
    confirm_password = serializers.CharField(max_length=200, required=True)
    current_password = serializers.CharField(max_length=200, required=True)                                             