from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class Role(models.TextChoices):
    SPOTTER = 'Spotter', 'Spotter'
    AGENT = 'Agent', 'Agent'
    AGENCY_MASTER = 'Master Agent', 'Master Agent'
    AGENCY_ADMIN = 'Agency_Admin', 'Agency Administrator' 
    ADMIN = 'Admin', 'System Administrator'

class Agency(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    license_valid_until = models.DateField(null=True, blank=True)
    master_user = models.OneToOneField(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='master_agency',
    )

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    ROLE_CHOICES = [(role.value, role.label) for role in Role]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default="Spotter")
    agency = models.ForeignKey(
        'users.Agency',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='customuser_set',
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='customuser_set',
        help_text='Specific permissions for this user.'
    )
    phone = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    profile_complete = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_users'
    )

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        ordering = ['-created_at']