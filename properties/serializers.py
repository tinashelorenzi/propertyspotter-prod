from rest_framework import serializers
from .models import Property
from users.serializers import UserSerializer

class PropertySerializer(serializers.ModelSerializer):
    spotter = UserSerializer(read_only=True)
    spotter_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = Property
        fields = [
            'id', 'spotter', 'spotter_id', 'property_type', 'status',
            'owner_name', 'owner_contact', 'lead_source', 'price',
            'commission', 'reference_name', 'reference_details',
            'total_bedrooms', 'total_bathrooms', 'address',
            'featured_image', 'images', 'created_at', 'updated_at',
            'spotter_notes', 'agent_notes'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
