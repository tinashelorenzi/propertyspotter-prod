from rest_framework import serializers
from .models import CustomUser, Agency

class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = ['id', 'name', 'email', 'phone', 'address', 'is_active', 'license_valid_until']

class UserSerializer(serializers.ModelSerializer):
    agency = AgencySerializer(read_only=True)
    agency_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name' ,'email', 'role', 'agency', 'agency_id', 'phone', 
                 'is_active', 'profile_complete', 'created_at', 'last_login', 'profile_image', 'profile_image_url']
        read_only_fields = ['id', 'created_at', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        agency_id = validated_data.pop('agency_id', None)
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        
        if password:
            user.set_password(password)
        if agency_id:
            user.agency_id = agency_id
            
        user.save()
        return user