from rest_framework import serializers
from .models import CustomUser, Agency

class AgencyMinimalSerializer(serializers.ModelSerializer):
    """Minimal Agency serializer to prevent circular imports"""
    class Meta:
        model = Agency
        fields = ['id', 'name', 'email']

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
                 'is_active', 'profile_complete', 'created_at', 'last_login', 'profile_image', 'profile_image_url', 'bank_name', 'account_number', 'bank_branch_code', 'account_type', 'account_name']
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

class CustomUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    agency_details = AgencyMinimalSerializer(source='agency', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'phone',
            'agency',
            'agency_details',
            'is_active',
            'profile_complete',
            'profile_image',
            'profile_image_url',
            'created_at',
            'last_login',
            'approved_at',
            'bank_name',
            'bank_branch_code',
            'account_number',
            'account_name',
            'account_type'
        ]
        read_only_fields = [
            'id', 
            'created_at', 
            'last_login', 
            'approved_at',
            'profile_image_url'
        ]
        extra_kwargs = {
            'agency': {'write_only': True},  # Only show agency_details in response
            'account_number': {'write_only': True},  # Hide sensitive banking info
            'bank_branch_code': {'write_only': True}
        }

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def to_representation(self, instance):
        """Customize the output representation"""
        ret = super().to_representation(instance)
        
        # Only include banking details if the user is requesting their own data
        request = self.context.get('request')
        if not request or str(request.user.id) != str(instance.id):
            # Remove banking details for other users
            banking_fields = [
                'bank_name', 'bank_branch_code', 'account_number', 
                'account_name', 'account_type'
            ]
            for field in banking_fields:
                ret.pop(field, None)
        
        return ret