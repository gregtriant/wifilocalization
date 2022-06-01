from django.db import models


# Create your models here.
class FloorPlan(models.Model):
    name = models.CharField(max_length=100, default='', blank=False)
    imagePath = models.CharField(max_length=100, blank=False)
    pub_date = models.DateTimeField('date uploaded', auto_now_add=True, blank=False)


class Room(models.Model):
    FloorPlan = models.ForeignKey(FloorPlan, related_name='rooms', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default='', blank=False)
    x = models.FloatField(default=0, blank=False)
    y = models.FloatField(default=0, blank=False)
    width = models.FloatField(default=0, blank=False)
    height = models.FloatField(default=0, blank=False)


class SignalPoint(models.Model):
    FloorPlan = models.ForeignKey(FloorPlan, related_name='signal_points', on_delete=models.CASCADE)
    x = models.FloatField(default=0, blank=False)
    y = models.FloatField(default=0, blank=False)
    networks = models.TextField(blank=False)


class Route(models.Model):
    FloorPlan = models.ForeignKey(FloorPlan, related_name='routes', on_delete=models.CASCADE)
    points = models.TextField(blank=False)
