from django.db import models
from django.template import Template, Context
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
import uuid

class EmailTemplate(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=36,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=255)
    html_content = models.TextField(
        help_text="HTML content with template variables in Django template syntax e.g. {{ user.name }}"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def send_email(self, to_email, context_data=None, from_email=None):
        """
        Send email using this template
        
        Args:
            to_email (str or list): Email recipient(s)
            context_data (dict): Context data for template rendering
            from_email (str): Override default from email
        """
        if context_data is None:
            context_data = {}

        # Render the template with context
        template = Template(self.html_content)
        context = Context(context_data)
        rendered_content = template.render(context)

        # Render subject with context
        subject_template = Template(self.subject)
        rendered_subject = subject_template.render(context)

        # Use default from email if not specified
        sender = from_email or settings.DEFAULT_FROM_EMAIL

        # Create and send email
        email = EmailMessage(
            subject=rendered_subject,
            body=rendered_content,
            from_email=sender,
            to=[to_email] if isinstance(to_email, str) else to_email,
            reply_to=[sender]
        )
        email.content_subtype = "html"  # Main content is now text/html
        return email.send()

class EmailLog(models.Model):
    """Log of all emails sent through the system"""
    id = models.CharField(
        primary_key=True,
        max_length=36,
        default=uuid.uuid4,
        editable=False
    )
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='email_logs'
    )
    subject = models.CharField(max_length=255)
    recipient = models.EmailField()
    sender = models.EmailField()
    content = models.TextField()
    context_data = models.JSONField(
        null=True, 
        blank=True,
        help_text="JSON data used to render the template"
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('SUCCESS', 'Success'),
            ('FAILED', 'Failed'),
        ],
        default='SUCCESS'
    )
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Email to {self.recipient} - {self.subject}"

# Signal to log emails
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=EmailTemplate)
def log_email_send(sender, instance, created, **kwargs):
    if not created:  # Only log when sending, not when creating template
        try:
            EmailLog.objects.create(
                template=instance,
                subject=instance.subject,
                recipient=kwargs.get('to_email', ''),
                sender=kwargs.get('from_email', settings.DEFAULT_FROM_EMAIL),
                content=instance.html_content,
                context_data=kwargs.get('context_data'),
                status='SUCCESS'
            )
        except Exception as e:
            EmailLog.objects.create(
                template=instance,
                subject=instance.subject,
                recipient=kwargs.get('to_email', ''),
                sender=kwargs.get('from_email', settings.DEFAULT_FROM_EMAIL),
                content=instance.html_content,
                context_data=kwargs.get('context_data'),
                status='FAILED',
                error_message=str(e)
            )