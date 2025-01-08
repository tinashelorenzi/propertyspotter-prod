from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Agency
from .serializers import AgencySerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Agency
from .serializers import AgencySerializer
from .serializers import AgencySerializerAPI
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class AgencyViewSet(viewsets.ReadOnlyModelViewSet):  # Using ReadOnlyModelViewSet instead of ModelViewSet
    """
    API endpoint that allows agencies to be viewed.
    Read-only endpoints - modifications should be done through the Django admin panel.
    """
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """
        Get list of all agencies
        """
        agencies = self.get_queryset()
        serializer = self.get_serializer(agencies, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
        Get a specific agency by ID
        """
        agency = get_object_or_404(Agency, pk=pk)
        serializer = self.get_serializer(agency)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_agency_by_admin(request, admin_id):
    try:
        # Get agency where the admin_id matches the principal_user
        agency = get_object_or_404(Agency, principal_user_id=admin_id)
        
        # Check if the requesting user is the principal_user or an agent of the agency
        is_authorized = (
            request.user.id == admin_id or
            agency.agents.filter(user=request.user).exists()
        )
        
        """"
        if not is_authorized:
            return Response(
                {"error": "You are not authorized to view this agency's details"},
                status=status.HTTP_403_FORBIDDEN
            )
            """
        
        serializer = AgencySerializerAPI(agency)
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_agencies(request):
    try:
        # Initialize pagination
        paginator = StandardResultsSetPagination()
        
        # Get query parameters
        search_query = request.query_params.get('search', '')
        is_active = request.query_params.get('is_active', None)
        
        # Start with all agencies
        agencies = Agency.objects.all()
        
        # Apply filters based on user role
        if request.user.role == 'Admin':
            # System admin can see all agencies
            pass
        elif request.user.role == 'Agency_Admin':
            # Agency admin can only see their own agency
            agencies = agencies.filter(principal_user=request.user)
        elif request.user.role == 'Agent':
            # Agents can only see their associated agency
            agencies = agencies.filter(agents__user=request.user)
        else:
            # Other roles (like spotters) might have limited or no access
            return Response(
                {"error": "You don't have permission to view agencies"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Apply search filter
        if search_query:
            agencies = agencies.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(principal_user__email__icontains=search_query)
            )
        
        # Apply active status filter
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            agencies = agencies.filter(is_active=is_active)
        
        # Order by created date
        agencies = agencies.order_by('-created_at')
        
        # Paginate results
        result_page = paginator.paginate_queryset(agencies, request)
        
        # Serialize the data
        serializer = AgencySerializer(result_page, many=True)
        
        # Return paginated response
        return paginator.get_paginated_response(serializer.data)
        
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
