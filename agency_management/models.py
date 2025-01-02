from django.db import models
from django.contrib.auth import get_user_model
from leads.models import Lead
from users.models import CustomUser
from django.db.models import Q
import uuid,os
from dotenv import load_dotenv

User = get_user_model()  # Using CustomUser defined earlier

WEBURL = os.getenv('WEBURL')

def generate_secure_filename(instance, filename):
    # Generate a unique UUID for the file name
    extension = filename.split('.')[-1]  # Get the file extension (e.g., jpg, png)
    secure_filename = f"{uuid.uuid4().hex}.{extension}"
    
    # Define the upload path (e.g., 'uploads/logos/')
    upload_path = f"uploads/logos/{secure_filename}"
    return upload_path

# Agency Model
class Agency(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
        related_name='Agency_Admin'
    )

    # Agency Logo
    logo = models.ImageField(upload_to=generate_secure_filename, null=True, blank=True)
    logo_url = models.URLField(max_length=500, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.logo:
            print(WEBURL)
            #Append weburl with media/uploads/logos and generated filename
            self.logo_url = WEBURL + "/media/uploads/logos/" + self.logo.name
        super().save(*args, **kwargs)

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.agency.name}"

    # Count active leads assigned to the agent
    @property
    def active_leads_count(self):
        from leads.models import Lead  # Import here to avoid circular import
        return Lead.objects.filter(
            assigned_agent=self.user,
            status='New_Submission'
        ).count()

    class Meta:
        ordering = ['-created_at']
