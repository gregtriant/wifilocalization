from django.core import serializers
from django.shortcuts import render, get_object_or_404
from .models import FloorPlan, Room, SignalPoint
from django.http import JsonResponse, HttpResponseServerError, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, permissions
from .serializers import FloorPlanSerializer, RoomSerializer, SignalPointSerializer
from .wifi_localization import Localization
from django.core import serializers


@csrf_exempt
def index(request):
    floor_plans = FloorPlan.objects.order_by('-pub_date')
    context = {'floor_plans': floor_plans}
    return render(request, 'wifirooms/index.html', context)
    # return HttpResponse("Hello, world. You're at the polls index.")

@csrf_exempt
def knn(request):
    # get all points from the database
    data = serializers.serialize("json", SignalPoint.objects.all())
    data = json.loads(data)
    signal_points = []
    for point in data:
        signal_points.append(point['fields'])
    knns = []

    if request.method == 'GET': # this is for testing purposes
        test_point = [{'BSSID': '78:96:82:3a:9d:c8', 'level': -42}, {'BSSID': '28:ff:3e:03:76:dc', 'level': -62}, {'BSSID': '62:ff:3e:03:76:dd', 'level': -65}, {'BSSID': 'f4:23:9c:20:9a:06', 'level': -75},
                      {'BSSID': '0c:b9:12:03:c4:20', 'level': -82}, {'BSSID': '08:26:97:e4:4f:51', 'level': -83}, {'BSSID': '50:78:b3:80:c4:bd', 'level': -86}, {'BSSID': '5a:d4:58:f2:8e:64', 'level': -87},
                      {'BSSID': '78:96:82:2f:ef:4e', 'level': -88}, {'BSSID': '62:96:82:2f:ef:4f', 'level': -89}, {'BSSID': '34:58:40:e6:60:c0', 'level': -92}, {'BSSID': '50:81:40:15:41:e8', 'level': -95}]
        Localizer = Localization()
        knns = Localizer.knn(signal_points, test_point, 4)

    elif request.method == 'POST':
        byte_data = request.body  # this is class byte
        string_data = byte_data.decode('UTF-8')  # convert to string
        list_data = json.loads(string_data)  # convert to python list
        # print(list_data)

        test_point = list_data['networks']
        Localizer = Localization()
        knns = Localizer.knn(signal_points, test_point, 4)

    print("\nTesting found knns: ", knns)
    return HttpResponse(json.dumps(knns))


@csrf_exempt
def rooms(request, floor_plan_id):  # api path: <int:floor_plan_id>/rooms/
    if request.method == 'GET':
        # print(floor_plan_id)
        floor_plan = get_object_or_404(FloorPlan, pk=floor_plan_id)
        # rooms = get_object_or_404(Room, FloorPlan=floor_plan_id)
        try:
            # TODO: Get rooms for a specific floor plan and return them as json
            rooms_list = Room.objects.values()
        except (KeyError, Room.DoesNotExist):
            return render(request, 'wifirooms/rooms.html', {
                'floor_plan': floor_plan,
                'error_message': "No rooms for this floor_plan.",
            })
        else:
            # jsonStr = json.dumps(list(rooms_list))
            # print(jsonStr)
            return render(request, 'wifirooms/rooms.html', {
                # 'rooms_list': jsonStr,
                'floor_plan_id': floor_plan_id,
                'floor_plan_img': floor_plan.imagePath,
            })
    elif request.method == 'POST':
        # add rooms to current floor_plan_id
        byte_data = request.body                 # this is class byte
        string_data = byte_data.decode('UTF-8')  # convert to string
        list_data = json.loads(string_data)      # convert to python list
        # find the specific floor_plan
        floor_plan = get_object_or_404(FloorPlan, pk=floor_plan_id)
        # delete all previous rooms for that floor_plan
        Room.objects.filter(FloorPlan=floor_plan).delete()
        # add the new rooms
        for room in list_data:
            # print(room)
            newRoom = Room()
            newRoom.FloorPlan = floor_plan
            newRoom.name = room['name']
            newRoom.x = room['x']
            newRoom.y = room['y']
            newRoom.width = room['width']
            newRoom.height = room['height']
            newRoom.save()

        # TODO: check how to return json in HttpResponse
        return HttpResponse('Saved Rooms')


class FloorPlanViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = FloorPlan.objects.all()
    serializer_class = FloorPlanSerializer
    # permission_classes = [permissions.IsAuthenticated]


class RoomViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    # permission_classes = [permissions.IsAuthenticated]


class SignalPointViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = SignalPoint.objects.all()
    serializer_class = SignalPointSerializer
    # permission_classes = [permissions.IsAuthenticated]