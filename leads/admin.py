from django.contrib import admin
from .models import Lead

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('property', 'spotter', 'potential', 'status', 'created_at')
    list_filter = ('potential', 'status', 'created_at')
    search_fields = ('property__address', 'source', 'notes')
