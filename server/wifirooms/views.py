from django.core import serializers
from django.shortcuts import render, get_object_or_404
from .models import FloorPlan, Room, SignalPoint, Route
from django.http import JsonResponse, HttpResponseServerError, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, permissions
from .serializers import FloorPlanSerializer, RoomSerializer, SignalPointSerializer, RouteSerializer
from .wifi_localization import Localization
from django.core import serializers

from .wifi_globals import connectedWS
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


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
def fingerprinting(request, floor_plan_id):  # api path: <int:floor_plan_id>/fingerprinting/
    if request.method == 'POST':
        # add rooms to current floor_plan_id
        byte_data = request.body                 # this is class byte
        string_data = byte_data.decode('UTF-8')  # convert to string
        # print(string_data)
        data = json.loads(string_data)      # convert to python list
        # print(data["finalRoutes"])
        if data["message"] == "SAVE_ROUTES":
            routes = data["finalRoutes"]
            # find the specific floor_plan
            floor_plan = get_object_or_404(FloorPlan, pk=floor_plan_id)
            # delete all previous rooms for that floor_plan
            Route.objects.filter(FloorPlan=floor_plan).delete()
            # add the new rooms
            for route in routes:
                newRoute = Route()
                newRoute.FloorPlan = floor_plan
                newRoute.points = json.dumps(route)
                newRoute.save()
            print("Saved routes for floor_plan: ", floor_plan_id)
            return HttpResponse('Saved Routes')

        elif data["message"] == "NEW_ROBOT_LOCATION":
            print("NEW_ROBOT_LOCATION")
            # here we are in Fingerprinting mode and we are sending the current Route and Current Point

            data = {
                "route": data["route"],
                "point": data["point"]
            }
            print(data)

            # send the point to all Connected Browsers
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)("browsers", {
                "type": "robot.location",
                "data": data
            })
            response = {
                "message": "Informing clinets of robot location..."
            }
            return HttpResponse(json.dumps(response))

        elif data["message"] == "NEW_POINT":
            print("NEW_POINT")
            # new point send from the mobile phone on the robot.
            print(data["route"], data["point"])
            # print(data["wifis"])
            print(data["floor_plan_id"])
            floor_plan = FloorPlan.objects.get(pk=data["floor_plan_id"])
            routes = serializers.serialize("json", Route.objects.filter(FloorPlan_id=data["floor_plan_id"]))
            routes = json.loads(routes)
            selected_route = routes[data["route"]] # we select route from index send (assuming the routes are always retrieved with the same order)
            route_points = json.loads(selected_route["fields"]["points"])
            print(route_points[data["point"]])
            SignalPoint.objects.create(FloorPlan=floor_plan, x=route_points[data["point"]]["x"], y=route_points[data["point"]]["y"], networks=json.dumps(data["wifis"]))

            response = {
                "message": "New point being added..."
            }
            return HttpResponse(json.dumps(response))


@csrf_exempt
def rooms(request, floor_plan_id):  # api path: <int:floor_plan_id>/rooms/
    if request.method == 'GET':
        # print(floor_plan_id)
        floor_plan = get_object_or_404(FloorPlan, pk=floor_plan_id)
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

        return HttpResponse('Saved Rooms')


class FloorPlanViewSet(viewsets.ModelViewSet):
    queryset = FloorPlan.objects.all()
    serializer_class = FloorPlanSerializer
    # permission_classes = [permissions.IsAuthenticated]


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    # permission_classes = [permissions.IsAuthenticated]


class SignalPointViewSet(viewsets.ModelViewSet):
    queryset = SignalPoint.objects.all()
    serializer_class = SignalPointSerializer
    # permission_classes = [permissions.IsAuthenticated]


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    # permission_classes = [permissions.IsAuthenticated]
