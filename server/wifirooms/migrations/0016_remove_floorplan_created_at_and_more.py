# Generated by Django 4.0.5 on 2022-08-24 17:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wifirooms', '0015_alter_floorplan_created_at_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='floorplan',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='floorplan',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='room',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='room',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='route',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='route',
            name='updated_at',
        ),
    ]