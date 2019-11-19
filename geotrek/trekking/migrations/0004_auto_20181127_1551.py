# Generated by Django 1.11.14 on 2018-11-27 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trekking', '0003_auto_20181113_1755'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trek',
            name='pois_excluded',
            field=models.ManyToManyField(blank=True, db_table='l_r_troncon_poi_exclus', related_name='excluded_treks', to='trekking.POI', verbose_name='Excluded POIs'),
        ),
    ]
