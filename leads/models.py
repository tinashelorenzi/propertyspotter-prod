from django.db import models
from users.models import CustomUser
from properties.models import Property, PropertyStatus, PropertyType
import uuid

# Lead Potential Choices
class LeadPotential(models.TextChoices):
    COLD = 'Cold', 'Cold Lead'            # Minimal information, e.g., billboard or address only
    LUKE_WARM = 'Luke Warm', 'Luke Warm Lead'  # Address, owner name, and some contact info
    HOT = 'Hot', 'Hot Lead'               # All property details provided

# Lead Model
class Lead(models.Model):
    # Core Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    spotter = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="leads"
    )
    property = models.OneToOneField(
        Property, on_delete=models.CASCADE, related_name="lead"
    )  # Links to the associated property
    potential = models.CharField(
        max_length=10, choices=LeadPotential.choices, default=LeadPotential.COLD
    )
    assigned_agency = models.ForeignKey(
        'agency_management.Agency',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads'
    )
    assigned_agent = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Notes and Source
    source = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    # Status Tracking
    status = models.CharField(
        max_length=30, choices=PropertyStatus.choices, default=PropertyStatus.NEW_SUBMISSION
    )
    pushed_to_agency_at = models.DateTimeField(null=True, blank=True)
    assigned_to_agent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Lead: {self.property.address if self.property else 'No Address'} - {self.potential}"

    class Meta:
        ordering = ['-created_at']

    # Automatically determine lead potential based on details
    def save(self, *args, **kwargs):
        # Update lead potential based on details provided in the property
        if self.property:
            if self.property.owner_name and self.property.owner_contact:
                if self.property.price and self.property.total_bedrooms > 0:
                    self.potential = LeadPotential.HOT
                else:
                    self.potential = LeadPotential.LUKE_WARM
            else:
                self.potential = LeadPotential.COLD

        # Update Property Status based on Lead Status
        if self.property:
            self.property.status = self.status
            self.property.save()

        super().save(*args, **kwargs)
