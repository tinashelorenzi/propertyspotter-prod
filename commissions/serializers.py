from rest_framework import serializers
from .models import Commission
from users.models import CustomUser
from properties.models import Property
import uuid

class CommissionSerializer(serializers.ModelSerializer):
   class Meta:
       model = Commission 
       fields = '__all__'

class CommissionCreateSerializer(serializers.ModelSerializer):
    spotter_id = serializers.UUIDField(write_only=True)
    property_id = serializers.CharField(write_only=True)
    payment_date = serializers.DateTimeField(write_only=True, required=True)

    class Meta:
        model = Commission
        fields = [
            'id', 'spotter_id', 'property_id', 'amount', 
            'payment_reference', 'notes', 'payment_date'
        ]
        read_only_fields = ['id']

    def validate_spotter_id(self, value):
        try:
            spotter = CustomUser.objects.get(id=value, role='Spotter')
            return value
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid spotter ID or user is not a spotter.")

    def validate_property_id(self, value):
        try:
            # Convert string to UUID
            print("Converting to UUID")
            property_uuid = uuid.UUID(str(value))
            
            try:
                property_obj = Property.objects.get(id=property_uuid)
                if Commission.objects.filter(property=property_obj).exists():
                    raise serializers.ValidationError("Commission already exists for this property.")
                return property_uuid
            except Property.DoesNotExist:
                raise serializers.ValidationError("Invalid property ID.")
                
        except ValueError:
            raise serializers.ValidationError("Invalid UUID format for property ID.")

    def create(self, validated_data):
        payment_date = validated_data.pop('payment_date')
        spotter_id = validated_data.pop('spotter_id')
        property_id = validated_data.pop('property_id')

        # Get the related objects
        spotter = CustomUser.objects.get(id=spotter_id)
        property_obj = Property.objects.get(id=property_id)

        # Create the commission
        commission = Commission.objects.create(
            spotter=spotter,
            property=property_obj,
            status='Paid',
            **validated_data
        )

        # Mark as paid with the provided payment date
        commission.mark_as_paid(reference=validated_data.get('payment_reference'))
        commission.paid_at = payment_date
        commission.save()

        return commission