# Generated by Django 3.1.13 on 2022-01-14 14:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0020_reportstatus_color'),
    ]

    operations = [
        migrations.RenameField(
            model_name='attachedmessage',
            old_name='suricate_id',
            new_name='identifier',
        ),
        migrations.RenameField(
            model_name='reportactivity',
            old_name='suricate_id',
            new_name='identifier',
        ),
        migrations.RenameField(
            model_name='reportcategory',
            old_name='suricate_id',
            new_name='identifier',
        ),
        migrations.RenameField(
            model_name='reportproblemmagnitude',
            old_name='suricate_id',
            new_name='identifier',
        ),
        migrations.RenameField(
            model_name='reportstatus',
            old_name='suricate_id',
            new_name='identifier',
        ),
        migrations.AlterUniqueTogether(
            name='attachedmessage',
            unique_together={('identifier', 'date', 'report')},
        ),
    ]
