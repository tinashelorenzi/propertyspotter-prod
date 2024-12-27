from django.contrib import admin
from .models import Property

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('property_type', 'status', 'spotter', 'price', 'created_at')
    list_filter = ('status', 'property_type', 'created_at')
    search_fields = ('address', 'owner_name', 'lead_source')
