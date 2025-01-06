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
    id = models.CharField(
    primary_key=True,
    max_length=36,
    default=uuid.uuid4,
    editable=False
)
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

def user_profile_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'uploads/profile_images/{uuid.uuid4()}.{ext}'

class CustomUser(AbstractUser):
    ROLE_CHOICES = [(role.value, role.label) for role in Role]

    id = id = models.CharField(
    primary_key=True,
    max_length=36,
    default=uuid.uuid4,
    editable=False
)
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
    profile_image = models.ImageField(
        upload_to=user_profile_path,
        null=True,
        blank=True
    )
    profile_image_url = models.URLField(null=True, blank=True)
    def save(self, *args, **kwargs):
        if self.profile_image:
            self.profile_image_url = self.profile_image.url
        super().save(*args, **kwargs)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_users'
    )
    #Banking details
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    bank_branch_code = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=255, null=True, blank=True)
    account_name = models.CharField(max_length=255, null=True, blank=True)
    account_type = models.CharField(max_length=255, null=True, blank=True)

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        ordering = ['-created_at']

class VerificationToken(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=36,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='verification_tokens'
    )
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Token expiration
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Verification token for {self.user.email}"