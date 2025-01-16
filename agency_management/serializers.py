from rest_framework import serializers
from .models import Agency, Agent
from users.serializers import CustomUserSerializer
from users.models import CustomUser
from leads.models import Lead
from django.db.models import Q

class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = '__all__'
        read_only = True  # This ensures all fields are read-only

class AgencySerializerAPI(serializers.ModelSerializer):
    principal_user = CustomUserSerializer(read_only=True)
    agents_count = serializers.SerializerMethodField()
    active_leads_count = serializers.SerializerMethodField()
    total_sales = serializers.SerializerMethodField()

    class Meta:
        model = Agency
        fields = [
            'id', 
            'name', 
            'email', 
            'phone', 
            'address', 
            'license_valid_until',
            'is_active',
            'principal_user',
            'logo',
            'logo_url',
            'created_at',
            'updated_at',
            'agents_count',
            'active_leads_count',
            'total_sales'
        ]

    def get_agents_count(self, obj):
        return obj.agents.filter(is_active=True).count()

    def get_active_leads_count(self, obj):
        from leads.models import Lead
        return Lead.objects.filter(
            assigned_agent__agent_profile__agency=obj,
            status='New_Submission'
        ).count()

    def get_total_sales(self, obj):
        from leads.models import Lead
        completed_leads = Lead.objects.filter(
            assigned_agent__agent_profile__agency=obj,
            status='Completed'
        )
        return sum(lead.property_value for lead in completed_leads if lead.property_value)

class AgentSerializerAgency(serializers.ModelSerializer):
    print("AgentSerializerAgency")
    properties_sold = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
            'role',
            'is_active',
            'created_at',
            'last_login',
            'profile_image_url',
            'properties_sold'
        ]
    
    def get_properties_sold(self, obj):
        print("All properties sold")
        return Lead.objects.filter(
            Q(assigned_agent=obj),
            Q(status='Commission_Paid') | Q(status='Sold')
        ).count()

class AgencyUpdateSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(required=False)
    
    class Meta:
        model = Agency
        fields = [
            'id', 'name', 'email', 'phone', 'address', 
            'logo', 'logo_url', 'license_valid_until'
        ]
        read_only_fields = ['id', 'logo_url']  # These fields cannot be modified directly

    def validate_email(self, value):
        """
        Check if email is unique, excluding current instance
        """
        instance = self.instance
        if Agency.objects.exclude(pk=instance.pk).filter(email=value).exists():
            raise serializers.ValidationError("An agency with this email already exists.")
        return value

    def validate_name(self, value):
        """
        Check if name is unique, excluding current instance
        """
        instance = self.instance
        if Agency.objects.exclude(pk=instance.pk).filter(name=value).exists():
            raise serializers.ValidationError("An agency with this name already exists.")
        return value

    def update(self, instance, validated_data):
        """
        Handle the logo upload separately
        """
        # Handle logo upload if provided
        if 'logo' in validated_data:
            logo = validated_data.pop('logo')
            instance.logo = logo
            # logo_url will be updated in the model's save method
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance