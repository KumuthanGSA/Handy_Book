from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.core.validators import RegexValidator

# Third party imports
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
    

class CustomUser(AbstractUser):

    objects = CustomUserManager()

    USERNAME_FIELD = 'id'
    REQUIRED_FIELDS = []
    username = None

    def __str__(self) -> str:
        return f' {self.id} - {self.otp}'


class AdminUsers(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    email = models.EmailField(unique=True)
    phone_no = PhoneNumberField(region='IN', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('self', related_name='created_users', on_delete=models.SET_NULL, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    edited_by = models.ForeignKey('self', related_name='edited_users', on_delete=models.SET_NULL, null=True, blank=True)
    last_edited = models.DateTimeField(auto_now=True)
    designation = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self) -> str:
        return f' {self.id} - {self.first_name}'
    