from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Commission
from .serializers import CommissionSerializer
from leads.models import Lead

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
        # First get the lead's property
        lead = Lead.objects.select_related('property').get(id=lead_id)
        
        # Then get the commission for that property
        commission = Commission.objects.get(property=lead.property)
        serializer = CommissionSerializer(commission)
        return Response(serializer.data)
        
    except Lead.DoesNotExist:
        return Response({
            "detail": "Lead not found",
            "lead_id": lead_id
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Commission.DoesNotExist:
        return Response({
            "detail": "No commission found for this lead's property",
            "lead_id": lead_id,
            "property_id": str(lead.property.id) if lead.property else None
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            "error": str(e),
            "detail": "An error occurred while fetching the commission"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_commissions_by_spotter(request, spotter_id):
   commissions = Commission.objects.filter(spotter__id=spotter_id)
   serializer = CommissionSerializer(commissions, many=True)
   return Response(serializer.data)