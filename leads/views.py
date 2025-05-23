# views.py
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from .models import Lead
from .serializers import LeadSerializer, LeadSerializerAPI, LeadCommissionSerializer, LeadStatusSerializer
from properties.models import Property, PropertyStatus
from .models import Lead, LeadPotential
from .serializers import LeadSerializer
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, permissions
from django.db import transaction
from twilio.rest import Client
import os
from dotenv import load_dotenv
import whatsapp

load_dotenv()

TWILIO_AUTH = os.getenv('TWILIO_AUTH')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
NOTIFICATIONS = os.getenv('NOTIFICATIONS')
TWILIO_FROM = os.getenv('TWILIO_FROM')
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH)

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
   # Get assigned agent phone number
   agent = lead.assigned_agent
   agent_phone = agent.phone if agent else None

   # Send WhatsApp message to assigned agent
   if agent_phone:
       from whatsapp import send_whatsapp_message
       message = f"New lead assigned: {lead.property.address if lead.property else 'No Address'} - {lead.potential}"
       send_whatsapp_message(message, agent_phone)

   # Send WhatsApp message to lead spotter
   spotter_phone = lead.spotter.phone if lead.spotter else None
   if spotter_phone:
       from whatsapp import send_whatsapp_message
       message = f"Hi! {lead.spotter.first_name if lead.spotter else 'Spotter'}, your lead has now been pushed to {lead.assigned_agent.first_name if lead.assigned_agent else 'an agent'} from {lead.assigned_agency.name if lead.assigned_agency else 'an agency'}, we will be in touch with more updates!"
       send_whatsapp_message(message, spotter_phone)
    

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
           #Send whatsapp message
           message = client.messages.create(
               from_=f'whatsapp:{TWILIO_FROM}',
               body=f'Hi! We\'ve received a new lead submitted to the platform, please assign it to an agency! Here is the lead Data: \n Spotter: {request.user.first_name} {request.user.last_name} \n Property: {property_instance.address} \n Source: {lead.source} \n Notes: {lead.notes}',
               to=f'whatsapp:{NOTIFICATIONS}'
           )
           print(message.sid)
           return Response(serializer.data, status=status.HTTP_201_CREATED)
       return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
       
   except Property.DoesNotExist:
       print("Property not found")
       return Response({'error': 'Property not found'}, status=status.HTTP_404_NOT_FOUND)
   except Exception as e:
       print(e)
       return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_lead_commission_paid(request, lead_id):
    from properties.models import PropertyStatus
    try:
        lead = Lead.objects.get(id=lead_id)
        lead.status = PropertyStatus.COMMISSION_PAID
        lead.save()
        
        serializer = LeadSerializer(lead)
        return Response(serializer.data)
        
    except Lead.DoesNotExist:
        return Response(
            {"error": "Lead not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([])
def agent_leads(request, agent_id):
    """
    Get all leads for a specific agent with optional filtering
    """
    """
    # Verify the requesting user is either the agent or has admin privileges
    if str(request.user.id) != agent_id and not request.user.is_superuser:
        return Response({"error": "Unauthorized access"}, status=403)
    """
    # Get query parameters
    status = request.GET.get('status')
    potential = request.GET.get('potential')
    days = request.GET.get('days')  # For filtering by date range

    # Base queryset
    queryset = Lead.objects.filter(assigned_agent_id=agent_id)

    # Apply filters if provided
    if status:
        queryset = queryset.filter(status=status)
    if potential:
        queryset = queryset.filter(potential=potential)
    if days:
        date_threshold = timezone.now() - timedelta(days=int(days))
        queryset = queryset.filter(created_at__gte=date_threshold)

    # Order by most recent
    queryset = queryset.order_by('-created_at')

    # Serialize and return
    serializer = LeadSerializer(queryset, many=True)
    print(serializer.data)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([])
def agent_lead_stats(request, agent_id):
    """
    Get comprehensive lead statistics for a specific agent
    """
    """
    # Verify the requesting user is either the agent or has admin privileges
    if str(request.user.id) != agent_id and not request.user.is_superuser:
        return Response({"error": "Unauthorized access"}, status=403)
    """

    # Get all leads for the agent
    leads = Lead.objects.filter(assigned_agent_id=agent_id)
    
    # Calculate time ranges
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    ninety_days_ago = now - timedelta(days=90)

    # Compile statistics
    stats = {
        "total_leads": leads.count(),
        "leads_by_potential": {
            "hot": leads.filter(potential=LeadPotential.HOT).count(),
            "luke_warm": leads.filter(potential=LeadPotential.LUKE_WARM).count(),
            "cold": leads.filter(potential=LeadPotential.COLD).count()
        },
        "leads_by_status": {},
        "recent_activity": {
            "last_30_days": leads.filter(created_at__gte=thirty_days_ago).count(),
            "last_90_days": leads.filter(created_at__gte=ninety_days_ago).count(),
        },
        "conversion_rates": {
            "total_converted": leads.filter(status='COMMISSION_PAID').count(),
            "conversion_rate": calculate_conversion_rate(leads)
        }
    }

    # Add counts for each status
    for status_choice in Lead._meta.get_field('status').choices:
        status_code = status_choice[0]
        stats["leads_by_status"][status_code] = leads.filter(status=status_code).count()

    return Response(stats)

def calculate_conversion_rate(leads_queryset):
    """Helper function to calculate lead conversion rate"""
    total_leads = leads_queryset.count()
    if total_leads == 0:
        return 0
    
    converted_leads = leads_queryset.filter(status='COMMISSION_PAID').count()
    return round((converted_leads / total_leads) * 100, 2)

@api_view(['POST'])
#@authentication_classes([TokenAuthentication])
@permission_classes([])
def set_lead_commission(request, lead_id):
    """
    Update the commission amount for a specific lead and update related statuses
    """
    try:
        with transaction.atomic():  # Use transaction to ensure both updates succeed or fail together
            # Get the lead or return 404
            lead = get_object_or_404(Lead.objects.select_related('assigned_agent', 'property'), id=lead_id)
            
            # Debug prints
            print(f"Request User ID: {request.user.id}")
            print(f"Assigned Agent ID: {lead.assigned_agent.id if lead.assigned_agent else 'No assigned agent'}")
            
            # Check if the user is the assigned agent
            """
            if lead.assigned_agent and request.user.id != lead.assigned_agent.id:
                return Response({
                    "error": "Unauthorized. You must be the assigned agent to update this lead."
                }, status=status.HTTP_403_FORBIDDEN)
            """

            serializer = LeadCommissionSerializer(data=request.data)
            
            if serializer.is_valid():
                commission = serializer.validated_data['commission']
                
                # Update the property's commission and status
                property_instance = lead.property
                property_instance.commission = commission
                
                # Determine status based on commission
                if commission > 0:
                    new_status = PropertyStatus.PENDING_MANDATE
                else:
                    # If commission is removed or set to 0, revert to NEW_SUBMISSION
                    new_status = PropertyStatus.NEW_SUBMISSION

                # Update both property and lead status
                property_instance.status = new_status
                property_instance.save()
                
                # Update lead status
                lead.status = new_status
                lead.save()

                return Response({
                    "message": "Commission and status updated successfully",
                    "commission": commission,
                    "status": new_status
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"Error: {str(e)}")  # Debug print
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
#@authentication_classes([TokenAuthentication])
@permission_classes([])
def update_lead_status(request, lead_id):
    """
    Update the status of a specific lead
    """
    try:
        with transaction.atomic():  # Use transaction to ensure both updates succeed or fail together
            # Get the lead or return 404
            lead = get_object_or_404(Lead.objects.select_related('assigned_agent', 'property'), id=lead_id)
            
            """
            # Check if user is assigned agent
            if lead.assigned_agent and request.user.id != lead.assigned_agent.id:
                return Response({
                    "error": "Unauthorized. You must be the assigned agent to update this lead."
                }, status=status.HTTP_403_FORBIDDEN)
            """

            serializer = LeadStatusSerializer(data=request.data)
            print(request.data)
            
            if serializer.is_valid():
                new_status = serializer.validated_data['status']
                property_listing_link = request.data.get('propertyListingLink')
                
                # Validate status transition based on commission
                if new_status == PropertyStatus.OWNER_NOT_FOUND and lead.property.commission:
                    return Response({
                        "error": "Cannot set status to Owner Not Found when commission is set"
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Update both property and lead status
                property_instance = lead.property
                property_instance.status = new_status
                property_instance.save()
                
                lead.status = new_status
                lead.property_listing_link = property_listing_link
                lead.save()
                #Get lead spotter phone number
                spotter_phone = lead.spotter.phone if lead.spotter else None
                if spotter_phone:
                    from whatsapp import send_whatsapp_message
                    send_whatsapp_message(f"Hi {lead.spotter.first_name if lead.spotter else 'Spotter'}, your lead has been updated to {new_status}, \n Here is the property listing link: {property_listing_link if property_listing_link else 'No link provided Yet'} \n We will be in touch with more updates!", spotter_phone)

                return Response({
                    "message": "Status updated successfully",
                    "status": new_status
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"Error: {str(e)}")  # Debug print
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
