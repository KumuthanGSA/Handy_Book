from django.db import transaction
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# Third party imports
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from phonenumber_field.serializerfields import PhoneNumberField

#local imports
from core.models import CustomUser, MobileUsers


# Create your serializers here
# USER MANAGEMENT API'S *******
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True)

    class Meta:
        model = MobileUsers
        fields = ['first_name', 'last_name', 'email', 'phone_no','password', 'fcm_token']
        extra_kwargs = {
            'password': {'write_only': True},
            'phone_no': {'required': True, 'allow_blank': False, 'allow_null': False},
            'fcm_token': {'required': True, 'allow_blank': False, 'allow_null': False}
        }

    def create(self, validated_data):
        # Validate password strength
        password = validated_data.pop('password', None)
        try:
            validate_password(password)
        except ValidationError as e:
            return serializers.ValidationError({'password': e.messages})
        
        # if any operation fails, the entire transaction will be rolled back.
        with transaction.atomic():
            # Creating a custom user
            custom_user = CustomUser()
            custom_user.set_password(password)
            custom_user.save()

            # Add the user to USER group
            group, _ = Group.objects.get_or_create(name='USER')
            custom_user.groups.add(group)

            #  Creating a Mobile user 
            mobile_user = self.Meta.model(**validated_data)
            mobile_user.user = custom_user
            mobile_user.save()
        return mobile_user
    

class GetOTPSerializer(serializers.Serializer):
    phone_no = PhoneNumberField(region="IN")


class OTPVerficationSerializer(serializers.Serializer):
    phone_no = PhoneNumberField(region="IN")
    otp = serializers.IntegerField()

    def validate(self, data):
        phone_no = data["phone_no"]
        otp = data["otp"]

        if not(1000 <= otp <= 9999):
            raise serializers.ValidationError({"otp": "OTP must be exactly 4 digits"})
        
        try:
            user = MobileUsers.objects.get(phone_no=phone_no)
        except MobileUsers.DoesNotExist:
            raise serializers.ValidationError({"phone_no": "User not found"})
        
        # Change otp to string becouse it is mentioned as CharField in model
        if not user.otp or user.otp != str(otp):
            raise serializers.ValidationError({"otp": "Invalid otp"})
        
        data["user"] = user
        data["custom_user"] =user.user

        return data
    
    def save(self):
        user = self.validated_data["user"]
        custom_user = self.validated_data["custom_user"]

        # Change the otp to none
        user.otp = None
        user.save()

        # Generate tokens (using Simple JWT library)
        refresh = RefreshToken.for_user(custom_user)
        access = refresh.access_token 

        tokens = {
            'access': str(access),
            'refresh': str(refresh)
        }
        return tokens

