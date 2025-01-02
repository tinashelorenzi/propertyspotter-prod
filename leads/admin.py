from django.contrib import admin
from .models import Lead
from django import forms
from agency_management.models import Agency

class LeadAdminForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_agency'].queryset = Agency.objects.filter(is_active=True)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    form = LeadAdminForm
    list_display = ('property', 'spotter', 'potential', 'status', 'created_at')
    list_filter = ('potential', 'status', 'created_at')
    search_fields = ('property__address', 'source', 'notes')
