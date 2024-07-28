from rest_framework.pagination import PageNumberPagination

# Create your paginators here

# PROFESSIONALS MODULE PAGINATIONS
class ProfessionalsPagination(PageNumberPagination):
    page_size = 10