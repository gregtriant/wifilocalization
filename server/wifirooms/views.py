from django.core import serializers
from django.shortcuts import render, get_object_or_404
from .models import FloorPlan, Room
from django.http import JsonResponse, HttpResponseServerError, HttpResponse
import json


def index(request):
    floor_plans = FloorPlan.objects.order_by('-pub_date')
    context = {'floor_plans': floor_plans}
    return render(request, 'wifirooms/index.html', context)
    # return HttpResponse("Hello, world. You're at the polls index.")


def rooms(request, floor_plan_id):
    if request.method == 'GET':
        # print(floor_plan_id)
        floor_plan = get_object_or_404(FloorPlan, pk=floor_plan_id)
        # rooms = get_object_or_404(Room, FloorPlan=floor_plan_id)
        try:
            rooms_list = Room.objects.values()
        except (KeyError, Room.DoesNotExist):
            return render(request, 'wifirooms/rooms.html', {
                'floor_plan': floor_plan,
                'error_message': "No rooms for this floor_plan.",
            })
        else:
            jsonStr = json.dumps(list(rooms_list))
            # print(jsonStr)
            return render(request, 'wifirooms/rooms.html', {
                'rooms_list': jsonStr,
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
        return HttpResponse('Got data')
