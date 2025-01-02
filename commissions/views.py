from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Commission
from .serializers import CommissionSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_commissions(request):
   commissions = Commission.objects.all()
   serializer = CommissionSerializer(commissions, many=True)
   return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated]) 
def get_commission_by_lead(request, lead_id):
   try:
       commission = Commission.objects.get(property__leads__id=lead_id)
       serializer = CommissionSerializer(commission)
       return Response(serializer.data)
   except Commission.DoesNotExist:
       return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_commissions_by_spotter(request, spotter_id):
   commissions = Commission.objects.filter(spotter__id=spotter_id)
   serializer = CommissionSerializer(commissions, many=True)
   return Response(serializer.data)