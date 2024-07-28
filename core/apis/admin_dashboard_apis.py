import datetime
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from django.db.models.aggregates import Count
from django.db.models.functions import TruncMonth 
from django.utils import timezone

# Third party imports
from rest_framework.views import APIView
from .permissions import IsAuthenticatedAndAdmin
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

# Local imports
from .serializers import AdminLoginSerializer, AdminLogoutSerializer, AccountSettingsRetrieveSerializer, AccountSettingsUpdateSerializer, AccountSettingsProfilePictureSerializer, AdminChangePasswordSerializer, ProfessionalsCreateRetrieveSerializer, ProfessionalsDeleteSerializer, ProfessionalsListSerializer, ProfessionalsUpdateSerializer
from . paginations import ProfessionalsPagination
from core.models import CustomUser, AdminUsers, Professionals, ProReview

# Create your views apis.
# ADMIN MANAGEMENT APIS
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
            return Response(tokens, status=status.HTTP_202_ACCEPTED)  
          
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)       
     

class AdminLogoutView(APIView):
    """
    API endpoint to logout a Admin user by blacklisting their refresh token.

    required params: refresh
    """
    
    permission_classes = [IsAuthenticatedAndAdmin]

    def post(self, request):
        serializer = AdminLogoutSerializer(data=request.data)
        if serializer.is_valid():
            
            serializer.save()
            return Response({"detail": "Admin logged out successfully!"}, status=status.HTTP_200_OK)
            
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ACCOUNT SETTINGS API'S *******
class AdminAccountSettingsView(APIView):
    # Ensure the view is accessible only to authenticated users in the 'Admin' group
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request):
        """
        Retrive admin user profile
        """

        admin_user = get_object_or_404(AdminUsers, user=request.user)
        serializer = AccountSettingsRetrieveSerializer(admin_user)

        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request):
        """
        Allow authenticated admin users to update their profile information.
        """

        user = get_object_or_404(AdminUsers, user=request.user)

        serializer = AccountSettingsUpdateSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Profile updated successfully!!"}, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        """
        Allow authenticated admin users to update their profile picture.
        """

        user = get_object_or_404(AdminUsers, user=request.user)

        serializer = AccountSettingsProfilePictureSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Profile picture updated successfully!!"}, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class AdminSecurityView(APIView):
    # Ensure the view is accessible only to authenticated users in the 'Admin' group
    permission_classes = [IsAuthenticatedAndAdmin]

    def post(self, request):
        """
        API endpoint that allows admin users to change their password.
        """
        
        serializer = AdminChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Password changed successfully!!"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# PROFESSIONALS MODULE API'S *******
class ProfessionalsListCreateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def post(self, request):
        """
        Creates a new Professional and its associated ADMIN review.
        """
        serializer = ProfessionalsCreateRetrieveSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
        
            serializer.save()

            return Response({"detail": "Professional created successfully!!"}, status=status.HTTP_201_CREATED)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """
        List all professionals.
        """
        expertise = request.query_params.get("expertise", None)
        location = request.query_params.get("location", None)
        search = request.query_params.get("search", None)

        if not expertise and not location and not search:
            professionals = Professionals.objects.all()

        else:
            filters = Q()
            if expertise:
                filters &= Q(expertise=expertise)

            if location:
                filters &= Q(location=location)

            if search:
                filters &= Q(name__icontains=search)

            professionals = Professionals.objects.filter(filters)

        pagination = ProfessionalsPagination()
        paginated_professionals = pagination.paginate_queryset(professionals, request)
        serializer = ProfessionalsListSerializer(paginated_professionals, many=True)
        return pagination.get_paginated_response(serializer.data)
    
    def delete(self, request):
        """
        Delete multiple Profesionals and their corresponding reviews.
        """
        serializer = ProfessionalsDeleteSerializer(data=request.data)
        if serializer.is_valid():
            try:
                deleted_count, deleted_objects = Professionals.objects.filter(id__in=serializer.validated_data["ids"]).delete()
                professional_deleted_count = deleted_objects.get(Professionals._meta.label, 0)
                review_count, _ = ProReview.objects.filter(professional_id__in=serializer.validated_data["ids"]).delete()

                if deleted_count == 0:
                    return Response({"detail": "No Professionals were deleted"}, status=status.HTTP_404_NOT_FOUND)
                return Response({"detail": f"{professional_deleted_count} Professionals deleted successfully!"}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST) 
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ProfessionalsRetrieveUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request, pk):
        """
        Retrieve specific professional.
        """

        professional = get_object_or_404(Professionals, id=pk)

        serializer = ProfessionalsCreateRetrieveSerializer(professional, context={'request': request, 'id': pk})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """
        Updates a specific Professional and its associated ADMIN review.
        """

        professional = get_object_or_404(Professionals, id=pk)

        serializer = ProfessionalsUpdateSerializer(professional, data=request.data, context={'request': request, 'id': pk})
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Professional updated successfully!!"}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
           
    def delete(self, request, pk):
        """
        Delets specific Professional and all its reviews.
        """
        # Retrieve and mark the Professional instance as deleted
        professional = get_object_or_404(Professionals, id=pk)
        try:
            professional.delete()
            return Response({"detail": "Professional deleted successfully!!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)