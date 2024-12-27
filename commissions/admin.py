from django.contrib import admin
from .models import Commission

@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('property', 'spotter', 'amount', 'status', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at', 'paid_at')
    search_fields = ('property__address', 'payment_reference', 'spotter__username')
