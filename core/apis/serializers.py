import datetime
from django.db import transaction
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.core.validators import MinValueValidator, MaxValueValidator

# Third party imports
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

# Local imports
from core.models import CustomUser, AdminUsers

# Create your serializers here

# ADMIN MANAGEMENT SERIALIZERS
class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Check if the user exists
        try:
            admin_user = AdminUsers.objects.get(email=email)
        except AdminUsers.DoesNotExist:
            raise serializers.ValidationError({"email": 'User does not exists'})

        # Check the password
        if not admin_user.user.check_password(password):
            raise serializers.ValidationError({'password': 'Wrong password'})
        
        attrs['custom_user'] = admin_user.user
        return attrs
    
    def save(self):
        custom_user = self.validated_data['custom_user']

        # Generate tokens (using Simple JWT library)
        refresh = RefreshToken.for_user(custom_user)
        access = refresh.access_token 

        tokens = {
            'access': str(access),
            'refresh': str(refresh)
        }

        return tokens