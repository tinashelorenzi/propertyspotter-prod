from django.db import models
from django.contrib.auth import get_user_model
from leads.models import Lead
from users.models import CustomUser
from django.db.models import Q
import uuid


User = get_user_model()  # Using CustomUser defined earlier


# Agency Model
class Agency(models.Model):
    id = models.UUIDField(primary_key=True, default=models.UUIDField, editable=False)
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    license_valid_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Principal User (Master Agent/Admin)
    principal_user = models.OneToOneField(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agency_principal'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    # Custom Manager for filtering Master Agents only
    @property
    def master_agent_choices(self):
        return CustomUser.objects.filter(role='Master Agent')


# Agent Model
class Agent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="agent_profile",
        limit_choices_to=Q(role='Agent')
    )
    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE,
        related_name="agents"
    )
    is_active = models.BooleanField(default=True)
    assigned_leads = models.ManyToManyField(
        Lead,
        blank=True,
        related_name="assigned_agents"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.agency.name}"

    # Count active leads assigned to the agent
    @property
    def active_leads_count(self):
        return self.assigned_leads.filter(status='New Submission').count()
