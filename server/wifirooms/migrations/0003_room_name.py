# Generated by Django 3.2.9 on 2021-12-02 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wifirooms', '0002_floorplan_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='name',
            field=models.CharField(default='', max_length=100),
        ),
    ]