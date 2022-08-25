from django.contrib import admin
from .models import FloorPlan, Room, SignalPoint, Route


# Register your models here.
admin.site.register(FloorPlan)
admin.site.register(Room)
admin.site.register(SignalPoint)
admin.site.register(Route)