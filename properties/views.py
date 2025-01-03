from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from users.authentication import BodyTokenAuthentication
from .models import Property, PropertyImage
from .serializers import PropertySerializer, PropertyImageSerializer, PropertySerializerAPI
from rest_framework_simplejwt.authentication import JWTAuthentication

def check_property_access(user, property_obj=None):
    """Check if user has access to property based on their role"""
    if user.role in ['Admin', 'Agency_Admin']:
        return True
    elif user.role == 'Agent' and property_obj and property_obj.spotter.agency == user.agency:
        return True
    elif user.role == 'Spotter' and property_obj and property_obj.spotter == user:
        return True
    return False

@api_view(['GET'])
@permission_classes([])
def list_properties(request):
    # Get any user filters from request
    property_type = request.data.get('property_type')
    status_filter = request.data.get('status')
    
    # Start with all properties
    properties = Property.objects.all()
    
    # Apply filters if provided
    if property_type:
        properties = properties.filter(property_type=property_type)
    if status_filter:
        properties = properties.filter(status=status_filter)
    
    serializer = PropertySerializer(properties, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([BodyTokenAuthentication])
@permission_classes([IsAuthenticated])
def get_property(request):
    """Get single property details"""
    property_id = request.data.get('property_id')
    if not property_id:
        return Response(
            {"error": "Property ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        property_obj = Property.objects.get(id=property_id)
        if not check_property_access(request.user, property_obj):
            return Response(
                {"error": "You don't have permission to view this property"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = PropertySerializer(property_obj)
        return Response(serializer.data)
    except Property.DoesNotExist:
        return Response(
            {"error": "Property not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_property(request):
    # Handle form data and files
    property_data = {
        'spotter': request.user.id,
        'property_type': request.POST.get('property_type'),
        'owner_name': request.POST.get('owner_name'),
        'owner_contact': request.POST.get('owner_contact'),
        'lead_source': request.POST.get('lead_source'),
        'price': request.POST.get('price'),
        'reference_name': request.POST.get('reference_name'),
        'reference_details': request.POST.get('reference_details'),
        'total_bedrooms': request.POST.get('total_bedrooms'),
        'total_bathrooms': request.POST.get('total_bathrooms'),
        'address': request.POST.get('address'),
        'spotter_notes': request.POST.get('spotter_notes')
    }

    serializer = PropertySerializerAPI(data=property_data)
    if serializer.is_valid():
        property_instance = serializer.save()

        # Handle featured image
        if 'featured_image' in request.FILES:
            property_instance.featured_image = request.FILES['featured_image']
            property_instance.save()

        # Handle additional property images
        if 'property_images[]' in request.FILES:
            images = request.FILES.getlist('property_images[]')
            for image in images:
                PropertyImage.objects.create(
                    property=property_instance,
                    image=image
                )
        print(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([BodyTokenAuthentication])
@permission_classes([IsAuthenticated])
def update_property(request):
    """Update property details"""
    property_id = request.data.get('property_id')
    if not property_id:
        return Response(
            {"error": "Property ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        property_obj = Property.objects.get(id=property_id)
        if not check_property_access(request.user, property_obj):
            return Response(
                {"error": "You don't have permission to update this property"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Remove property_id from update data
        update_data = request.data.copy()
        update_data.pop('property_id', None)
        update_data.pop('token', None)
        
        serializer = PropertySerializer(property_obj, data=update_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Property.DoesNotExist:
        return Response(
            {"error": "Property not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@authentication_classes([BodyTokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_property(request):
    """Delete property"""
    property_id = request.data.get('property_id')
    if not property_id:
        return Response(
            {"error": "Property ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        property_obj = Property.objects.get(id=property_id)
        if not check_property_access(request.user, property_obj):
            return Response(
                {"error": "You don't have permission to delete this property"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        property_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Property.DoesNotExist:
        return Response(
            {"error": "Property not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )