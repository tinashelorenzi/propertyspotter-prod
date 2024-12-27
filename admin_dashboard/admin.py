from django.contrib import admin
from .models import ActivityLog, Report


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'admin', 'timestamp')
    list_filter = ('timestamp', 'admin')
    search_fields = ('action', 'details')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'generated_by', 'generated_at', 'file_url')
    list_filter = ('report_type', 'generated_at')
    search_fields = ('report_type', 'file_url')