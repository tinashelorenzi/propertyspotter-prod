from django.db import models
from users.models import CustomUser
from properties.models import Property
import uuid


# Commission Payment Status
class CommissionStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    PAID = 'Paid', 'Paid'
    FAILED = 'Failed', 'Failed'
    CANCELLED = 'Cancelled', 'Cancelled'


# Commission Model
class Commission(models.Model):
    # Core Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    spotter = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="commissions",
        limit_choices_to={'role': 'Spotter'}  # Ensure only Spotters are linked
    )
    property = models.OneToOneField(
        Property, on_delete=models.CASCADE, related_name="property_commision"
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Commission amount agreed for this property."
    )
    status = models.CharField(
        max_length=10, choices=CommissionStatus.choices, default=CommissionStatus.PENDING
    )
    payment_reference = models.CharField(
        max_length=255, null=True, blank=True,
        help_text="Transaction reference or receipt number."
    )
    notes = models.TextField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Commission: {self.property.address} - {self.amount} - {self.status}"

    class Meta:
        ordering = ['-created_at']

    # Mark Commission as Paid
    def mark_as_paid(self, reference=None):
        """Mark the commission as paid with an optional payment reference."""
        from django.utils.timezone import now
        self.status = CommissionStatus.PAID
        self.paid_at = now()
        if reference:
            self.payment_reference = reference
        self.save()
