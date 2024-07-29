import random
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404

# Third party imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# local imports
from .serializers import UserRegisterSerializer, GetOTPSerializer, OTPVerficationSerializer
from core.models import MobileUsers, CustomUser
from core.apis.permissions import IsAuthenticatedAndInUserGroup


# Create your apis here.
# USERS MANAGEMENT API'S
class UserRegisterView(APIView):
    """
    API endpoint where new user can register
    """

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            return Response({'detail': "Mobile user created successfully"}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UserGetOTPView(APIView):
    """
    API endpoint to generate otp.
    """

    def post(self, request):
        serializer = GetOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone_no = serializer.validated_data["phone_no"]

            user = get_object_or_404(MobileUsers, phone_no=phone_no)

            otp = random.randint(1000, 9999)
            user.otp = otp
            user.save()

            return Response({"detail": "OTP send successfully!", "otp": otp}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class OTPVerificationView(APIView):
    """
    To verify the given otp.
    """

    def post(self, request):
        serializer = OTPVerficationSerializer(data=request.data)
        if serializer.is_valid():

            token = serializer.save()
            return Response(token, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)