from rest_framework import serializers
from .models import Lead
from properties.serializers import PropertySerializerAPI, PropertySerializer
from users.serializers import UserSerializer, AgencySerializer
from agency_management.serializers import AgencySerializer
from properties.models import Property
from properties.models import PropertyStatus

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
            'assigned_to_agent_at', 'property_listing_link'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'potential',
                           'pushed_to_agency_at', 'assigned_to_agent_at']

class LeadSerializerAPI(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['potential']

    def create(self, validated_data):
        try:
            lead = Lead.objects.create(**validated_data)
            return lead
        except Exception as e:
            print(f"Error in serializer create: {e}")
            raise serializers.ValidationError(str(e))

class PropertyMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ['id', 'address', 'price', 'total_bedrooms', 'total_bathrooms', 'property_type']

class LeadSerializerAgent(serializers.ModelSerializer):
    property_details = PropertyMinimalSerializer(source='property', read_only=True)
    days_since_created = serializers.SerializerMethodField()
    days_since_updated = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = [
            'id', 'potential', 'status', 'source', 'notes',
            'created_at', 'updated_at', 'property_details',
            'days_since_created', 'days_since_updated'
        ]

    def get_days_since_created(self, obj):
        from django.utils import timezone
        delta = timezone.now() - obj.created_at
        return delta.days

    def get_days_since_updated(self, obj):
        from django.utils import timezone
        delta = timezone.now() - obj.updated_at
        return delta.days

class LeadCommissionSerializer(serializers.ModelSerializer):
    commission = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Lead
        fields = ['commission']

class LeadStatusSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=PropertyStatus.choices)

    class Meta:
        model = Lead
        fields = ['status']
