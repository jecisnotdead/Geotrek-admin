# Generated by Django 1.11.14 on 2019-03-22 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tourism', '0003_auto_20190306_1417'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='touristiccontenttype1',
            options={'verbose_name': 'Type1', 'verbose_name_plural': 'First list types'},
        ),
        migrations.AlterModelOptions(
            name='touristiccontenttype2',
            options={'verbose_name': 'Type2', 'verbose_name_plural': 'Second list types'},
        ),
        migrations.AlterField(
            model_name='touristiccontent',
            name='type1',
            field=models.ManyToManyField(blank=True, db_table='t_r_contenu_touristique_type1', related_name='contents1', to='tourism.TouristicContentType1', verbose_name='Type 1'),
        ),
        migrations.AlterField(
            model_name='touristiccontent',
            name='type2',
            field=models.ManyToManyField(blank=True, db_table='t_r_contenu_touristique_type2', related_name='contents2', to='tourism.TouristicContentType2', verbose_name='Type 2'),
        ),
    ]
