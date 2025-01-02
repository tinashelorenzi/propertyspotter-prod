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
    list_display = ('name', 'email', 'phone', 'license_valid_until', 'is_active', 'principal_user', 'logo_thumbnail')
    list_filter = ('is_active', 'license_valid_until')
    search_fields = ('name', 'email', 'principal_user__username')

    # Method to display logo thumbnail in the admin list
    def logo_thumbnail(self, obj):
        if obj.logo:
            return f'<img src="{obj.logo.url}" width="50" height="50" />'  # You can adjust the size
        return "No Logo"
    logo_thumbnail.allow_tags = True  # This allows the HTML to render
    logo_thumbnail.short_description = 'Logo Preview'  # The label for the field in the admin interface

    # Optional: Display the logo's URL in the admin list view (you can add this if needed)
    def logo_url_display(self, obj):
        return obj.logo_url or "No URL"
    logo_url_display.short_description = 'Logo URL'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'principal_user':
            kwargs["queryset"] = CustomUser.objects.filter(role='Agency_Admin')  # Filter Master Agents
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Agent, AgentAdmin)
admin.site.register(Agency, AgencyAdmin)
