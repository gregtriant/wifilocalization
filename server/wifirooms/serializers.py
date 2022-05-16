from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import FloorPlan, Room, SignalPoint


class SignalPointSerializer(serializers.HyperlinkedModelSerializer):
    floor_plan_id = serializers.IntegerField(source='FloorPlan.id', read_only=True)

    class Meta:
        model = SignalPoint
        fields = ['id', 'x', 'y', 'networks', 'floor_plan_id']


class RoomSerializer(serializers.HyperlinkedModelSerializer):
    floor_plan_id = serializers.IntegerField(source='FloorPlan.id', read_only=True)

    class Meta:
        model = Room
        fields = ['id', 'name', 'x', 'y', 'width', 'height', 'floor_plan_id']


class FloorPlanSerializer(serializers.HyperlinkedModelSerializer):
    # rooms = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    rooms = RoomSerializer(many=True, read_only=True)
    signal_points = SignalPointSerializer(many=True, read_only=True)

    class Meta:
        model = FloorPlan
        fields = ['id', 'name', 'imagePath', 'pub_date', 'rooms', 'signal_points']


