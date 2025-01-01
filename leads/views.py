from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.utils import timezone
from users.authentication import BodyTokenAuthentication
from users.models import CustomUser, Agency
from .models import Lead
from properties.models import Property
from .serializers import LeadSerializer

# Create your views here.
# Updated access check function
def check_lead_access(user, lead=None):
    """Check if user has access to lead based on their role and agency assignment"""
    if user.role == 'Admin':
        return True
    elif user.role == 'Agency_Admin':
        return lead and lead.assigned_agency == user.agency
    elif user.role == 'Agent':
        return lead and lead.assigned_agency == user.agency and (
            lead.assigned_agent is None or lead.assigned_agent == user
        )
    elif user.role == 'Spotter':
        return lead and lead.spotter == user
    return False

# New endpoint to push lead to agency
@api_view(['POST'])
@authentication_classes([BodyTokenAuthentication])
@permission_classes([IsAuthenticated])
def push_lead_to_agency(request):
    """Push a lead to a specific agency"""
    lead_id = request.data.get('lead_id')
    agency_id = request.data.get('agency_id')
    
    if not lead_id or not agency_id:
        return Response(
            {"error": "Both lead_id and agency_id are required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        lead = Lead.objects.get(id=lead_id)
        agency = Agency.objects.get(id=agency_id)
        
        # Check permissions
        if request.user.role not in ['Admin', 'Spotter']:
            return Response(
                {"error": "Only Admin or Spotter can push leads to agencies"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.user.role == 'Spotter' and lead.spotter != request.user:
            return Response(
                {"error": "You can only push your own leads"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update lead with agency assignment
        from django.utils import timezone
        lead.assigned_agency = agency
        lead.pushed_to_agency_at = timezone.now()
        lead.assigned_agent = None  # Reset any previous agent assignment
        lead.assigned_to_agent_at = None
        lead.save()
        
        return Response(LeadSerializer(lead).data)
        
    except (Lead.DoesNotExist, Agency.DoesNotExist):
        return Response(
            {"error": "Lead or Agency not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

# New endpoint to assign lead to agent
@api_view(['POST'])
@authentication_classes([BodyTokenAuthentication])
@permission_classes([IsAuthenticated])
def assign_lead_to_agent(request):
    """Assign a lead to a specific agent within the agency"""
    lead_id = request.data.get('lead_id')
    agent_id = request.data.get('agent_id')
    
    if not lead_id or not agent_id:
        return Response(
            {"error": "Both lead_id and agent_id are required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        lead = Lead.objects.get(id=lead_id)
        agent = CustomUser.objects.get(id=agent_id)
        
        # Check permissions
        if request.user.role != 'Agency_Admin':
            return Response(
                {"error": "Only Agency Administrators can assign leads to agents"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if lead.assigned_agency != request.user.agency:
            return Response(
                {"error": "This lead is not assigned to your agency"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if agent.agency != request.user.agency or agent.role != 'Agent':
            return Response(
                {"error": "Invalid agent selection"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update lead with agent assignment
        from django.utils import timezone
        lead.assigned_agent = agent
        lead.assigned_to_agent_at = timezone.now()
        lead.save()
        
        return Response(LeadSerializer(lead).data)
        
    except (Lead.DoesNotExist, CustomUser.DoesNotExist):
        return Response(
            {"error": "Lead or Agent not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

# Update the list_leads view to handle agency assignments
@api_view(['POST'])
@authentication_classes([BodyTokenAuthentication])
@permission_classes([IsAuthenticated])
def list_leads(request):
    """List leads with role-based filtering"""
    user = request.user
    
    # Filter leads based on user role and agency assignment
    if user.role == 'Admin':
        leads = Lead.objects.all()
    elif user.role == 'Agency_Admin':
        leads = Lead.objects.filter(assigned_agency=user.agency)
    elif user.role == 'Agent':
        leads = Lead.objects.filter(
            assigned_agency=user.agency
        ).filter(
            models.Q(assigned_agent=user) | models.Q(assigned_agent=None)
        )
    elif user.role == 'Spotter':
        leads = Lead.objects.filter(spotter=user)
    else:
        return Response(
            {"error": "Insufficient permissions"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Apply additional filters
    potential = request.data.get('potential')
    lead_status = request.data.get('status')
    assigned_only = request.data.get('assigned_only', False)
    
    if potential:
        leads = leads.filter(potential=potential)
    if lead_status:
        leads = leads.filter(status=lead_status)
    if assigned_only and user.role == 'Agent':
        leads = leads.filter(assigned_agent=user)
    
    serializer = LeadSerializer(leads, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([BodyTokenAuthentication])
@permission_classes([IsAuthenticated])
def create_lead(request):
    """Create a new lead"""
    if request.user.role not in ['Spotter', 'Agent', 'Admin', 'Agency_Admin']:
        return Response(
            {"error": "You don't have permission to create leads"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Validate property existence
    property_id = request.data.get('property_id')
    try:
        property_obj = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return Response(
            {"error": "Property not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if lead already exists for this property
    if Lead.objects.filter(property=property_obj).exists():
        return Response(
            {"error": "A lead already exists for this property"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create lead data
    data = request.data.copy()
    data['spotter'] = request.user.id
    
    serializer = LeadSerializer(data=data)
    if serializer.is_valid():
        lead = serializer.save(spotter=request.user)
        return Response(LeadSerializer(lead).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([BodyTokenAuthentication])
@permission_classes([IsAuthenticated])
def update_lead(request):
    """Update lead details"""
    lead_id = request.data.get('lead_id')
    if not lead_id:
        return Response(
            {"error": "Lead ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        lead = Lead.objects.get(id=lead_id)
        if not check_lead_access(request.user, lead):
            return Response(
                {"error": "You don't have permission to update this lead"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Remove lead_id from update data
        update_data = request.data.copy()
        update_data.pop('lead_id', None)
        update_data.pop('token', None)
        
        serializer = LeadSerializer(lead, data=update_data, partial=True)
        if serializer.is_valid():
            updated_lead = serializer.save()
            return Response(LeadSerializer(updated_lead).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Lead.DoesNotExist:
        return Response(
            {"error": "Lead not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@authentication_classes([BodyTokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_lead(request):
    """Delete lead"""
    lead_id = request.data.get('lead_id')
    if not lead_id:
        return Response(
            {"error": "Lead ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        lead = Lead.objects.get(id=lead_id)
        if not check_lead_access(request.user, lead):
            return Response(
                {"error": "You don't have permission to delete this lead"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        lead.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Lead.DoesNotExist:
        return Response(
            {"error": "Lead not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@authentication_classes([BodyTokenAuthentication])
@permission_classes([IsAuthenticated])
def get_lead(request):
    """Get single lead details"""
    lead_id = request.data.get('lead_id')
    if not lead_id:
        return Response(
            {"error": "Lead ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        lead = Lead.objects.get(id=lead_id)
        if not check_lead_access(request.user, lead):
            return Response(
                {"error": "You don't have permission to view this lead"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = LeadSerializer(lead)
        return Response(serializer.data)
    except Lead.DoesNotExist:
        return Response(
            {"error": "Lead not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )