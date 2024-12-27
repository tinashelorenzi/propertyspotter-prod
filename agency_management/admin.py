from django.contrib import admin
from .models import Agency, Agent
from users.models import CustomUser


class AgentAdmin(admin.ModelAdmin):
    list_display = ('user', 'agency', 'is_active', 'created_at')
    list_filter = ('agency', 'is_active')
    search_fields = ('user__username', 'agency__name')

    # Filter agents to show only users with the "Agent" role
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs["queryset"] = CustomUser.objects.filter(role='Agent')  # Filter by role
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'license_valid_until', 'is_active', 'principal_user')
    list_filter = ('is_active', 'license_valid_until')
    search_fields = ('name', 'email', 'principal_user__username')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'principal_user':
            kwargs["queryset"] = CustomUser.objects.filter(role='Master Agent')  # Filter Master Agents
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Agent, AgentAdmin)
admin.site.register(Agency, AgencyAdmin)
