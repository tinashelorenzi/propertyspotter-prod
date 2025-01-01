from rest_framework import serializers
from .models import Lead
from properties.serializers import PropertySerializer
from users.serializers import UserSerializer, AgencySerializer

class LeadSerializer(serializers.ModelSerializer):
    spotter = UserSerializer(read_only=True)
    property = PropertySerializer(read_only=True)
    property_id = serializers.UUIDField(write_only=True)
    assigned_agency = AgencySerializer(read_only=True)
    assigned_agent = UserSerializer(read_only=True)
    
    class Meta:
        model = Lead
        fields = [
            'id', 'spotter', 'property', 'property_id', 'potential',
            'created_at', 'updated_at', 'source', 'notes', 'status',
            'assigned_agency', 'assigned_agent', 'pushed_to_agency_at',
            'assigned_to_agent_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'potential',
                           'pushed_to_agency_at', 'assigned_to_agent_at']


