from rest_framework import serializers
from .models import Agency

class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = '__all__'
        read_only = True  # This ensures all fields are read-only