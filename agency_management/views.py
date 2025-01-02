from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Agency
from .serializers import AgencySerializer

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