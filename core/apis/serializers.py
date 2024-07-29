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
from core.models import Books, CustomUser, AdminUsers, Events, Materials, MobileUsers, Professionals, ProReview

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
    

class AdminLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)

    def save(self):
        # Attempt to blacklist the refresh token to log out the user
        try:
            RefreshToken(self.validated_data['refresh']).blacklist()
        except Exception as e:
            raise serializers.ValidationError({"refresh": str(e)})
        
        return
    

# ACCOUNTSETTINGS SERIALIZERS
class AccountSettingsRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUsers
        fields = ["first_name", "last_name", "email", "phone_no", "designation", "image"]


class AccountSettingsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUsers
        fields = ["first_name", "last_name", "email", "phone_no", "designation"]

        extra_kwargs = {
            'phone_no': {'required': True, 'allow_blank': False, 'allow_null': False},
            'designation': {'required': True, 'allow_blank': False, 'allow_null': False}
        }


class AccountSettingsProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUsers
        fields = ["image"]
    
        extra_kwargs = {
            'image': {'required': True, 'allow_null': False}
        }


class AdminChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user

        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        # Check if the current password is correct
        if not user.check_password(current_password):
            raise serializers.ValidationError({'current_password': 'Wrong password'})
        
        # Check if new password and confirm password match
        if new_password != confirm_password:
            raise serializers.ValidationError({'confirm_password': 'Passwords mismatch'})
        
        # Validate the new password
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})
        
        return data
    
    def save(self):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user
    

# PROFESSIONALS MODULE SERIALIZERS
class ProfessionalsCreateRetrieveSerializer(serializers.ModelSerializer):
    review = serializers.CharField(write_only=True)
    rating = serializers.IntegerField(write_only=True)

    class Meta:
        model = Professionals
        fields = ['name', 'phone_no', 'email', 'expertise', 'location', 'about', 'experiance', 'portfolio', 'review', 'rating', 'banner', 'website']

    def create(self, validated_data):
        review = validated_data.pop('review')
        rating = validated_data.pop('rating')
        request = self.context.get('request')

        # Roll back if any error occurs
        with transaction.atomic():
            professional = Professionals.objects.create(**validated_data)
            ProReview.objects.create(professional=professional, review=review, rating=rating, created_by=request.user)

        return professional
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        id = self.context.get("id")
        admin_review = get_object_or_404(ProReview, professional_id=id, created_by__is_superuser=True)

        representation['review'] = admin_review.review
        representation['rating'] = admin_review.rating

        return representation
    

class ProfessionalsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professionals
        fields = ['id', 'name', 'phone_no', 'email', 'expertise', 'location']


class ProfessionalsDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())


class ProfessionalsUpdateSerializer(serializers.ModelSerializer):
    review = serializers.CharField(write_only=True)
    rating = serializers.IntegerField(write_only=True)

    class Meta:
        model = Professionals
        fields = ['name', 'phone_no', 'email', 'expertise', 'location', 'about', 'experiance', 'portfolio', 'review', 'rating', 'banner', 'website']

        extra_kwargs ={
            "website": {"required": True}
        }

    def update(self, instance, validated_data):
        id = self.context.get("id")
        review_data = validated_data.pop('review', None)
        rating_data = validated_data.pop('rating', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        admin_review = get_object_or_404(ProReview, professional_id=id, created_by__is_superuser=True)
        admin_review.review = review_data
        admin_review.rating = rating_data

        with transaction.atomic():
            instance.save()
            admin_review.save()

        return instance
    

# BOOKS MODULE SERIALIZERS *******
class BooksCreateRetrieveUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Books
        fields = ["name", "price", "description", "additional_details", "image", "availability"]

        extra_kwargs ={
            "availability": {"required": True}
        }
    

class BooksListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Books
        fields = ["id", "image", "name", "price", "availability"]


class BooksMultipleDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())


# EVENTS MODULE SERIALIZERS *******
class EventsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = ["title", "date", "location", "description", "image", "additional_informations"]


class EventsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = ["id", "title", "date", "location"]


class EventsMultipleDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())


class EventsRetrieveUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = ["title", "date", "location", "description", "image", "additional_informations"]

        extra_kwargs ={
            "additional_informations": {"required": True}
        }

# MATERIALS MODULE SERIALIZERS
class MaterialsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materials
        fields = ["name", "type", "supplier_name", "supplier_phone_no", "price", "discount_percentage", "title", "availability", "image", "description", "overview", "additional_details"]


class MaterialsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materials
        fields = ["id", "name", "image", "type", "supplier_name", "supplier_phone_no", "price", "availability"]


class MaterialsMultipleDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())


class MaterialsRetrieveUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materials
        fields = ["name", "type", "supplier_name", "supplier_phone_no", "price", "discount_percentage", "title", "availability", "image", "description", "overview", "additional_details"]

        extra_kwargs ={
            "availability": {"required": True},
            "overview": {"required": True},
            "additional_details": {"required": True}
        }


# USERS MODULE SERIALIZERS
class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileUsers
        fields = ["id", "first_name", "email", "phone_no", "created_on", "is_active"]


class UsersMultipleDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())
        

class UsersRetrieveUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileUsers
        fields = ["id", "first_name", "email", "phone_no", "created_on", "image"]

        extra_kwargs = {
            'phone_no': {'required': True, 'allow_blank': False, 'allow_null': False},
        }

class UsersProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileUsers
        fields = ["image"]
    
        extra_kwargs = {
            'image': {'required': True, 'allow_null': False}
        }