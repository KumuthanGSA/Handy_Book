from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator

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

        admin_user = AdminUsers.objects.create(email=email, user=user)
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
    email = models.EmailField(unique=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    username = None

    def __str__(self) -> str:
        return f' {self.id}'


class AdminUsers(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    email = models.EmailField(unique=True)
    designation = models.CharField(max_length=200, blank=True, null=True)
    phone_no = PhoneNumberField(region='IN', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f' {self.id} - {self.first_name}'
    

# PROFESSIONALS MODULE MODELS
"""
Represents individual professionals, including their personal details and associated expertise.
"""
class Professionals(models.Model):
    name = models.CharField(max_length=150)
    phone_no = PhoneNumberField(region='IN', unique=True)
    email = models.EmailField(unique=True)
    expertise = models.CharField(max_length=250)
    location = models.CharField(max_length=150)
    about = models.TextField()
    experiance = models.TextField()
    portfolio = models.FileField(upload_to='professionals/portfolios')

    """
    reviews and ratings is in separate model as relational fields.
    """

    banner = models.ImageField(upload_to='professionals/banners')
    website = models.URLField(max_length=500, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f' {self.id} - {self.name}'
    
    @classmethod
    def count(cls):
        return cls.objects.count()



"""
Contains reviews for professionals, including ratings and comments.
"""
class ProReview(models.Model):
    created_by = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='reviewed_by')
    created_on = models.DateField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)
    professional = models.ForeignKey(Professionals, related_name='review_professional', on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField()

    def __str__(self) -> str:
        return f' {self.id} - {self.review}'