# Generated by Django 3.1.14 on 2022-07-26 09:03

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tourism', '0024_auto_20220726_0901'),
    ]

    operations = [
        migrations.AlterField(
            model_name='informationdesk',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
