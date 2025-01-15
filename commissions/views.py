from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Commission
from .serializers import CommissionSerializer
from leads.models import Lead

from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .serializers import CommissionCreateSerializer

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_commission_paid(request, commission_id):
    from .models import Commission, CommissionStatus
    try:
        commission = Commission.objects.get(id=commission_id)
        
        # Add payment details
        payment_reference = request.data.get('payment_reference')
        payment_date = request.data.get('payment_date')
        
        commission.status = CommissionStatus.PAID
        commission.payment_reference = payment_reference
        commission.paid_at = payment_date
        commission.save()
        
        serializer = CommissionSerializer(commission)
        return Response(serializer.data)
        
    except Commission.DoesNotExist:
        return Response(
            {"error": "Commission not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_payment(request):
    import requests
    from commissions.models import Commission
    from leads.models import Lead
    from properties.models import Property
    from rest_framework.response import Response
    from rest_framework import status

    base_url = request.build_absolute_uri('/')[:-1]
    try:
        commission_id = request.data.get('commission_id')
        lead_id = request.data.get('lead_id')
        property_id = request.data.get('property_id')
        payment_reference = request.data.get('payment_reference')
        payment_date = request.data.get('payment_date')

        if not all([commission_id, lead_id, property_id, payment_reference, payment_date]):
            return Response({
                "error": "Missing required fields"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update Commission
        commission_response = requests.post(
            f"{base_url}/api/commissions/{commission_id}/mark-paid/",
            headers={'Authorization': f'Bearer {request.auth}'},
            data={'payment_reference': payment_reference, 'payment_date': payment_date}
        )
        if not commission_response.ok:
            raise Exception("Failed to update commission")

        # Update Lead
        lead_response = requests.post(
            f"{base_url}/api/leads/{lead_id}/mark-paid/",
            headers={'Authorization': f'Bearer {request.auth}'}
        )
        if not lead_response.ok:
            raise Exception("Failed to update lead")

        # Update Property
        property_response = requests.post(
            f"{base_url}/api/properties/{property_id}/mark-paid/",
            headers={'Authorization': f'Bearer {request.auth}'}
        )
        if not property_response.ok:
            raise Exception("Failed to update property")

        return Response({
            "message": "Commission payment processed successfully",
            "commission": commission_response.json(),
            "lead": lead_response.json(),
            "property": property_response.json()
        })

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CommissionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def post(self, request):
        serializer = CommissionCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                commission = serializer.save()
                return Response({
                    'message': 'Commission created successfully',
                    'commission_id': commission.id
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)