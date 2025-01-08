from rest_framework import serializers
from .models import Agency, Agent
from users.serializers import CustomUserSerializer

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