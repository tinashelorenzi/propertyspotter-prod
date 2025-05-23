# Generated by Django 5.1.4 on 2024-12-27 19:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency_management', '0002_alter_agency_id_alter_agency_principal_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='agent',
            name='user',
            field=models.OneToOneField(limit_choices_to={'role': 'agent_profile'}, on_delete=django.db.models.deletion.CASCADE, related_name='agent_profile', to=settings.AUTH_USER_MODEL),
        ),
    ]
