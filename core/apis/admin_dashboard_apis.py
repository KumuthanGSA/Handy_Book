from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.db.models.aggregates import Count
from django.db.models.functions import TruncMonth 
from django.utils import timezone
import datetime

# Third party imports
from rest_framework.views import APIView
from .permissions import IsAuthenticatedAndInAdminGroup
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

# Local imports
from core.models import AdminUsers
from .serializers import AdminLoginSerializer

# Create your views apis.
class AdminLoginView(APIView):
    """
    API endpoint for Admin login.
    Validates user credentials, active status and generates access and refresh tokens upon successful login.

    required params: email, password
    """

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            
            tokens = serializer.save()
            return Response(tokens, status=status.HTTP_200_OK)  
          
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)       
     


    
