# Generated by Django 5.1.4 on 2025-01-02 11:29

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency_management', '0005_alter_agency_principal_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agency',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
