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
from .serializers import AdminLoginSerializer, AdminLogoutSerializer, AccountSettingsRetrieveSerializer, AccountSettingsUpdateSerializer, AccountSettingsProfilePictureSerializer, AdminChangePasswordSerializer, BooksCreateRetrieveUpdateSerializer, BooksListSerializer, BooksMultipleDeleteSerializer, EventsCreateSerializer, EventsListSerializer, EventsMultipleDeleteSerializer, EventsRetrieveUpdateSerializer, MaterialsCreateSerializer, MaterialsListSerializer, MaterialsMultipleDeleteSerializer, MaterialsRetrieveUpdateSerializer, ProfessionalsCreateRetrieveSerializer, ProfessionalsDeleteSerializer, ProfessionalsListSerializer, ProfessionalsUpdateSerializer, UserListSerializer, UsersMultipleDeleteSerializer, UsersProfilePictureSerializer, UsersRetrieveUpdateSerializer
from . paginations import BooksPagination, EventsPagination, MaterialsPagination, ProfessionalsPagination, UsersPagination
from core.models import Books, CustomUser, AdminUsers, Events, Materials, MobileUsers, Professionals, ProReview

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
        serializer = AccountSettingsRetrieveSerializer(admin_user, context={'request': request})

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
        

# BOOKS MODULE API'S *******
class BooksListCreateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def post(self, request):
        """
        To create new book.
        """

        serializer = BooksCreateRetrieveUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Book created successfully!!"}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """
        List all books.
        """
        name = request.query_params.get("name")

        if name:
            books = Books.objects.filter(name__icontains=name)
        else:
            books = Books.objects.all()

        pagination = BooksPagination()
        paginated_books = pagination.paginate_queryset(books, request)
        serializer = BooksListSerializer(paginated_books, many=True, context={'request': request})
        return pagination.get_paginated_response(serializer.data)
    
    def delete(self, request):
        """
        Delete multiple books at the same time.
        """

        serializer = BooksMultipleDeleteSerializer(data=request.data)
        if serializer.is_valid():
            try:
                deleted_count, _ = Books.objects.filter(id__in=serializer.validated_data["ids"]).delete()

                if deleted_count == 0:
                    return Response({"detail": "No books were deactivated"}, status=status.HTTP_404_NOT_FOUND)
                
                return Response({"detail": f"{deleted_count} books deleted successfully!!"}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class BooksRetriveUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request, pk):
        """
        Retrieve specific book
        """

        book = get_object_or_404(Books, id=pk)
        serializer = BooksCreateRetrieveUpdateSerializer(book, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """
        Update specific book.
        """

        book = get_object_or_404(Books, id=pk)

        serializer = BooksCreateRetrieveUpdateSerializer(book, request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Book updated successfully!!"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """
        Delete specific book.
        """

        book = get_object_or_404(Books, id=pk)

        try:
            book.delete()
            return Response({"detail": "Book deleted successfully!!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

# EVENTS MODULE API'S
class EventsListCreateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def post(self, request):
        """
        To create new events.
        """

        serializer = EventsCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Event created successfully!!"}, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """
        List all events.
        """

        search = request.query_params.get("search")

        if not search:
            events = Events.objects.all()
        
        else:
            events = Events.objects.filter(Q(title__icontains=search)|Q(location__icontains=search))
        
        pagination = EventsPagination()
        paginated_events = pagination.paginate_queryset(events, request)
        serializer = EventsListSerializer(paginated_events, many=True, context={'request': request})

        return pagination.get_paginated_response(serializer.data)
    
    def delete(self, request):
        """
        Delete multiple events at the same time.
        """

        serializer = EventsMultipleDeleteSerializer(data=request.data)
        if serializer.is_valid():
            try:
                deleted_count, _ = Events.objects.filter(id__in=serializer.validated_data["ids"]).delete()

                if deleted_count == 0:
                    return Response({"detail": "No events were deactivated"}, status=status.HTTP_404_NOT_FOUND)
                return Response({"detail": f"{deleted_count} events deleted successfully!!"}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class EventsRetriveUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request, pk):
        """
        Retrieve specific material.
        """

        event = get_object_or_404(Events, id=pk)
        serializer = EventsRetrieveUpdateSerializer(event, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """
        Update specific material.
        """

        event = get_object_or_404(Events, id=pk)

        serializer = EventsRetrieveUpdateSerializer(event, request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Event updated successfully!!"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """
        Delete specific event.
        """

        event = get_object_or_404(Events, id=pk)

        try:
            event.delete()
            return Response({"detail": "Event deleted successfully!!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

# MATERIALS MODULE APIS *******
class MaterialsListCreateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def post(self, request):
        """
        To create new material.
        """

        admin_user = get_object_or_404(AdminUsers, user=request.user)
        serializer = MaterialsCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Material created successfully!!"}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """
        List all materials.
        """
        type = request.query_params.get("type", None)
        supplier_name = request.query_params.get("supplier_name", None)
        search = request.query_params.get("search", None)

        if not type and not supplier_name and not search:
            materials = Materials.objects.all()

        else:
            filters = Q()
            if type:
                filters &= Q(type=type)

            if supplier_name:
                filters &= Q(supplier_name=supplier_name)

            if search:
                filters &= Q(supplier_name__icontains=search) | Q(type__icontains=search)

            materials = Materials.objects.filter(filters)

        pagination = MaterialsPagination()
        paginated_materials = pagination.paginate_queryset(materials, request)
        serializer = MaterialsListSerializer(paginated_materials, many=True, context={"request": request})
        return pagination.get_paginated_response(serializer.data)
    
    def delete(self, request):
        """
        Delete multiple materials at the same time.
        """

        serializer = MaterialsMultipleDeleteSerializer(data=request.data)
        if serializer.is_valid():
            try:
                deleted_count, _ = Materials.objects.filter(id__in=serializer.validated_data["ids"]).delete()

                if deleted_count == 0:
                    return Response({"detail": "No material were deactivated"}, status=status.HTTP_404_NOT_FOUND)
                return Response({"detail": f"{deleted_count} materials deleted successfully!!"}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class MaterialsRetriveUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request, pk):
        """
        Retrieve specific material.
        """

        material = get_object_or_404(Materials, id=pk)
        serializer = MaterialsRetrieveUpdateSerializer(material, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """
        Update specific material.
        """

        material = get_object_or_404(Materials, id=pk)

        serializer = MaterialsRetrieveUpdateSerializer(material, request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Material updated successfully!!"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """
        Delete specific material.
        """

        material = get_object_or_404(Materials, id=pk)
        try:
            material.delete()
            return Response({"detail": "Material deleted successfully!!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

# USERS MODULE APIS *******
class UsersListDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request):
        """
        List all users.
        """

        date_range = request.query_params.get("date_range", None)
        # To avoid name conflicts use '_'
        status_ = request.query_params.get("status", None)
        search = request.query_params.get("search", None)

        if not date_range and not status_ and not search:
            users = MobileUsers.objects.all()

        else:
            filters = Q()
            if date_range:
                filters &= Q(date_range=date_range)

            if status_:
                choices = [1, 0, "1", "0"]
                print(status_, "here")
                if status_ not in choices:
                    return Response({"detail": {"status": ["Invalid value; the choices are '1', '0'"]}}, status=status.HTTP_400_BAD_REQUEST)
                filters &= Q(is_active=status_)

            if search:
                filters &= Q(first_name__icontains=search) | Q(email__icontains=search)

            users = MobileUsers.objects.filter(filters)

        pagination = UsersPagination()
        paginated_users = pagination.paginate_queryset(users, request)
        serializer = UserListSerializer(paginated_users, many=True, context={"request": request})
        return pagination.get_paginated_response(serializer.data)
    
    def delete(self, request):
        """
        Delete multiple users.
        """
        serializer = UsersMultipleDeleteSerializer(data=request.data)
        if serializer.is_valid():
        
            try:
                deleted_count = MobileUsers.objects.filter(id__in=serializer.validated_data["ids"], is_active=True).update(is_active=False)

                if deleted_count == 0:
                    return Response({"detail": "No users were deactivated"}, status=status.HTTP_404_NOT_FOUND)
                return Response({"detail": f"{deleted_count} users deactivated successfully!!"}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UsersDetailView(APIView):
    """
    Retrieve specific user
    """
    def get(self, request, pk):
        user = get_object_or_404(MobileUsers, id=pk)
        serializer = UsersRetrieveUpdateSerializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """
        Update specific user
        """

        user = get_object_or_404(MobileUsers, id=pk)

        serializer = UsersRetrieveUpdateSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Profile updated successfully!!"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        """
        Allow authenticated admin users to update user's profile picture.
        """

        user = get_object_or_404(MobileUsers, id=pk)

        serializer = UsersProfilePictureSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Profile picture updated successfully!!"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """
        Marks specific user as deactivated.
        """

        user = get_object_or_404(MobileUsers, id=pk, is_active=True)
        user.is_active=False
        user.save()

        return Response({"detail": "User marked as deactivated"}, status=status.HTTP_200_OK)