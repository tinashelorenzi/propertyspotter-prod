# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Lead
from .serializers import LeadSerializer

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
   # Check if property_id is provided
   property_id = request.data.get('property_id')
   if not property_id:
       return Response({'error': 'property_id is required'}, status=400)

   # Create lead data with the requesting user as spotter
   lead_data = {
       'property_id': property_id,
       'spotter': request.user.id,
       'source': request.data.get('source'),
       'notes': request.data.get('notes')
   }

   serializer = LeadSerializer(data=lead_data)
   if serializer.is_valid():
       serializer.save()
       return Response(serializer.data, status=201)
   return Response(serializer.errors, status=400)