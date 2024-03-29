# Generated by Django 3.2.9 on 2021-12-06 17:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wifirooms', '0003_room_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='floorplan',
            name='pub_date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='date uploaded'),
        ),
        migrations.CreateModel(
            name='SignalPoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('x', models.IntegerField(default=0)),
                ('y', models.IntegerField(default=0)),
                ('networks', models.TextField()),
                ('FloorPlan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wifirooms.floorplan')),
            ],
        ),
    ]
