from django.db import models
from users.models import CustomUser
from leads.models import Lead
from commissions.models import Commission
from agency_management.models import Agency, Agent
from properties.models import Property
import uuid


# Dashboard Activity Logs
class ActivityLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'Admin'}
    )
    action = models.CharField(max_length=255)  # e.g., "Assigned Lead to Agency"
    details = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} by {self.admin.username} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']


# Reports for Lead Assignments and Commissions
class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(
        max_length=50,
        choices=[('Lead', 'Lead Report'), ('Commission', 'Commission Report')]
    )
    generated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'Admin'}
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    file_url = models.CharField(max_length=255, null=True, blank=True)  # Path to file (e.g., CSV/Excel)

    def __str__(self):
        return f"{self.report_type} Report - {self.generated_at}"

    class Meta:
        ordering = ['-generated_at']
