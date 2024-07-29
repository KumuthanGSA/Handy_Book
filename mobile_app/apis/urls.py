from django.urls import path

# Third part imports
from rest_framework_simplejwt.views import TokenRefreshView

# Local imports
from .apis import UserRegisterView, UserGetOTPView, OTPVerificationView

urlpatterns = [
    path('register', UserRegisterView.as_view()),
    path('getotp', UserGetOTPView.as_view()),
    path('validate_otp', OTPVerificationView.as_view())
]