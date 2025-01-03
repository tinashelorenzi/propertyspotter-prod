# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Lead
from .serializers import LeadSerializer, LeadSerializerAPI
from properties.models import Property

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lead_list(request):
   leads = Lead.objects.all()
   serializer = LeadSerializer(leads, many=True)
   return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leads_by_spotter(request, spotter_id):
   leads = Lead.objects.filter(spotter_id=spotter_id)
   serializer = LeadSerializer(leads, many=True)
   return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leads_by_agency(request, agency_id):
   leads = Lead.objects.filter(assigned_agency_id=agency_id)
   serializer = LeadSerializer(leads, many=True)
   return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_to_agency(request, lead_id):
   lead = Lead.objects.get(id=lead_id)
   agency_id = request.data.get('agency_id')
   lead.assigned_agency_id = agency_id
   lead.save()
   serializer = LeadSerializer(lead)
   return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_to_agent(request, lead_id):
   lead = Lead.objects.get(id=lead_id)
   agent_id = request.data.get('agent_id')
   lead.assigned_agent_id = agent_id
   lead.save()
   serializer = LeadSerializer(lead)
   return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_lead(request):
   try:
       # Get property instance
       property_id = request.data.get('property')
       print(f"Attempting to find property with ID: {property_id}")
       property_instance = Property.objects.get(id=property_id)
       print(f"Property found: {property_instance}")

       lead_data = {
           'spotter': request.user.id,
           'property': property_id,
           'source': request.data.get('source'),
           'notes': request.data.get('notes'),
           'status': 'New Submission'
           # potential will be auto-determined in save() method
       }

       print(f"Lead data: {lead_data}")

       serializer = LeadSerializerAPI(data=lead_data)
       if serializer.is_valid():
           print("Serializer is valid")
           lead = serializer.save()
           print(f"Lead saved: {lead}")
           return Response(serializer.data, status=status.HTTP_201_CREATED)
       return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
       
   except Property.DoesNotExist:
       print("Property not found")
       return Response({'error': 'Property not found'}, status=status.HTTP_404_NOT_FOUND)
   except Exception as e:
       print(e)
       return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)