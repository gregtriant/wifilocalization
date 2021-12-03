from django.db import models


# Create your models here.
class FloorPlan(models.Model):
    name = models.CharField(max_length=100, default='')
    imagePath = models.CharField(max_length=100)
    pub_date = models.DateTimeField('date uploaded')


class Room(models.Model):
    name = models.CharField(max_length=100, default='')
    FloorPlan = models.ForeignKey(FloorPlan, on_delete=models.CASCADE)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
