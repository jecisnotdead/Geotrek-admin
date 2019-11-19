# Generated by Django 1.11.14 on 2019-10-29 10:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0004_attachment_creation_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filetype',
            name='structure',
            field=models.ForeignKey(blank=True, db_column='structure', null=True, on_delete=django.db.models.deletion.CASCADE, to='authent.Structure', verbose_name='Related structure'),
        ),
        migrations.AlterField(
            model_name='organism',
            name='structure',
            field=models.ForeignKey(blank=True, db_column='structure', null=True, on_delete=django.db.models.deletion.CASCADE, to='authent.Structure', verbose_name='Related structure'),
        ),
    ]
