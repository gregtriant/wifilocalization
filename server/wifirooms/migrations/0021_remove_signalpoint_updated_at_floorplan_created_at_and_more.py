# Generated by Django 4.0.5 on 2022-08-24 17:22

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('wifirooms', '0020_signalpoint_updated_at_alter_signalpoint_created_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='signalpoint',
            name='updated_at',
        ),
        migrations.AddField(
            model_name='floorplan',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='room',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='route',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
