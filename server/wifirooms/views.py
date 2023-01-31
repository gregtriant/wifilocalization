import math

from django.shortcuts import render, get_object_or_404
from .models import FloorPlan, Room, SignalPoint, Route
from django.http import JsonResponse, HttpResponseServerError, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, permissions
from .serializers import FloorPlanSerializer, RoomSerializer, SignalPointSerializer, RouteSerializer
from .wifi_localization import Localization
from .wifi_radiomap import RadioMap
from django.core import serializers
import time
from .wifi_globals import connectedWS
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import numpy as np

floor_plans = FloorPlan.objects.all()
radio_maps = []
localizers = []

for floor_plan in floor_plans:
    routes = serializers.serialize("json", Route.objects.filter(FloorPlan_id=floor_plan.id))
    routes = json.loads(routes)
    # print(routes)
    if len(routes) == 0:
        print("--> Views.py... Can't make Radio map for FloorPlan:", floor_plan.name, " No routes found...\n")
        continue

    print(floor_plan.routes)
    print("--> Views.py... Making Radio map for FloorPlan:", floor_plan.name, "...")
    start = time.time()
    data = serializers.serialize("json", SignalPoint.objects.filter(FloorPlan_id=floor_plan.id))
    data = json.loads(data)
    points = []
    for point in data:
        points.append(point['fields'])
    data = serializers.serialize("json", Room.objects.filter(FloorPlan_id=floor_plan.id))
    data = json.loads(data)
    rooms = []
    for room in data:
        rooms.append(room['fields'])
    rm = None
    rm = RadioMap(points, rooms, limit_scans='all', take_average=True, make_new_df=True)
    rm.make_radio_map()
    end = time.time()
    rm_data = {
        "floor_plan_id": floor_plan.id,
        "radio_map": rm
    }
    radio_maps.append(rm_data)
    print("--> Views.py... Done! -- time:", end - start, "\n")

    print("--> Views.py... Making Localizers for FloorPlan:", floor_plan.name, "...")
    start = time.time()
    localizer = Localization(rm)
    end = time.time()
    localizer_data = {
        "floor_plan_id": floor_plan.id,
        "localizer": localizer
    }
    localizers.append(localizer_data)
    print("--> Views.py... Done! -- time:", end - start, "\n")
    del rm


@csrf_exempt
def index(request):
    floor_plans = FloorPlan.objects.order_by('-pub_date')
    context = {'floor_plans': floor_plans}
    return render(request, 'wifirooms/index.html', context)

@csrf_exempt
def results(request, floor_plan_id):
    return render(request, 'wifirooms/results.html')

@csrf_exempt
def radio_map(request, floor_plan_id):
    for rm in radio_maps:
        if rm["floor_plan_id"] == floor_plan_id:
            return HttpResponse(rm["radio_map"].df_dataset.to_json())

@csrf_exempt
def bssids(request, floor_plan_id):
    for rm in radio_maps:
        if rm["floor_plan_id"] == floor_plan_id:
            return HttpResponse(json.dumps(rm["radio_map"].unique_bssids_of_floor_plan_dict))

@csrf_exempt
def classification_algorithms(request):
    return HttpResponse(json.dumps(localizers[0]["localizer"].names_of_classifiers))

@csrf_exempt
def test_points(request, floor_plan_id): # returns the test points with the scans on each point
    test_pts = findTestPoints(floor_plan_id)
    return HttpResponse(json.dumps(test_pts))


def findTestPoints(floor_plan_id):
    test_pts = []
    for rm in radio_maps:
        if rm["floor_plan_id"] == floor_plan_id:
            for sp in rm["radio_map"].signal_points:
                scans = []
                x = sp.x
                y = sp.y
                r = sp.room
                for i, scan in enumerate(sp.scans):
                    if i > 79:
                        scans.append(scan)
                p = {
                    'x': x,
                    'y': y,
                    'room': r,
                    'scans': scans
                }
                test_pts.append(p)
            return test_pts

@csrf_exempt
def point_scans(request, floor_plan_id):
    point_scans = []
    for rm in radio_maps:
        if rm["floor_plan_id"] == floor_plan_id:
            for sp in rm["radio_map"].signal_points:
                point = {
                    'x': sp.x,
                    'y': sp.y,
                    'room': sp.room,
                    'scans': len(sp.scans)
                }
                point_scans.append(point)
            return HttpResponse(json.dumps(point_scans))

@csrf_exempt
def all_scans(request, floor_plan_id, point_index):
    for rm in radio_maps:
        if rm["floor_plan_id"] == floor_plan_id:
            for index, sp in enumerate(rm["radio_map"].signal_points):
                if index == point_index:
                    # print(index, sp.scans)
                    return HttpResponse(json.dumps(sp.scans))

def room_stats(request, floor_plan_id):
    for rm in radio_maps:
        if rm["floor_plan_id"] == floor_plan_id:
            rm_stats_for_rooms = rm["radio_map"].stats_for_rooms
            stats = []
            for room_stat in rm_stats_for_rooms:
                # print(room_stat.makeRoomData())
                stats.append(room_stat.makeRoomData())
            return HttpResponse(json.dumps(stats))

def dbm_to_percent(dbm):
    quality = 0
    if dbm <= -100:
        quality = 0
    elif dbm >= -50:
        quality = 100
    else:
        quality = 2 * (dbm + 100)
    return quality


class Results:
    def __init__(self):
        self.dists = []
        self.avg_error_at_each_point = []
        self.correct_room_preds = 0
        self.total_room_preds = 0
        self.room_results = []


    def add_new_room(self, real_room):
        found = False
        for room_result in self.room_results:
            if room_result["name"] == real_room:
                found = True
                break
        if not found:
            new_room = {
                "name": real_room,
                "error_dists": [],
                "correct_room_preds":0,
                "total_room_preds": 0,
                "avg_dist_error": 0,
                "room_pred_acc": 0,
            }
            self.room_results.append(new_room)

    def calc_results(self, scans, localizer, algo, real_room, real_x, real_y):
        width = 600
        height = 581
        self.add_new_room(real_room)
        avg_error_dist = 0
        for scan in scans:  # 5 scans for each point
            pred_point = localizer.find_point(scan, algo)
            pred_room = localizer.find_room(scan, algo)[0]

            self.total_room_preds += 1
            for room_result in self.room_results:
                if room_result["name"] == real_room:
                    room_result["total_room_preds"] += 1

            if pred_room == real_room:
                self.correct_room_preds += 1
                for room_result in self.room_results:
                    if room_result["name"] == real_room:
                        room_result["correct_room_preds"] += 1


            error_dist = math.sqrt(((real_x * width - pred_point["x"] * width) * (real_x * width - pred_point["x"] * width)) + (
                        (real_y * height - pred_point["y"] * height) * (real_y * height - pred_point["y"] * height)))

            for room_result in self.room_results:
                if room_result["name"] == real_room:
                    room_result["error_dists"].append(error_dist) # avg_error_dist at each room

            avg_error_dist += error_dist # avg_error_dist_at each point
            self.dists.append(error_dist) # total_avg_error_dist

        avg_error_dist = avg_error_dist / len(scans)
        self.avg_error_at_each_point.append(avg_error_dist)

@csrf_exempt
def localize_test_all(request, floor_plan_id):
    localizer = None
    for local in localizers:
        if local["floor_plan_id"] == floor_plan_id:
            localizer = local["localizer"]
            break
    print("Testing all algorithms!")
    start = time.time()
    test_pts = findTestPoints(floor_plan_id)
    # print(test_pts)

    response_data = []
    for i, algo in enumerate(localizer.names_of_classifiers): # 8-10 classifiers
        # send progress to client
        # if i != 0:
        #     break

        algo_data = {
            "algorithm": algo,
        }
        print('\n ------- ', algo_data, ' ------- ')

        # send the point to all Connected Browsers
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)("browsers", {
            "type": "test.progress",
            "data": algo_data
        })

        all_results = Results()
        robot_results = Results()
        human1_results = Results()
        human2_results = Results()

        for j, tp in enumerate(test_pts): # 129 points
            # if j > 10:
            #     break
            print("algo:", i, "/", len(localizer.names_of_classifiers)-1, "point:", j, "/", len(test_pts)-1)
            x = tp["x"]
            y = tp["y"]
            room = tp["room"]
            scans = tp["scans"]

            all_scans = scans[-14:]
            robot_scans = scans[-14:-9]
            human_scans = scans[-9:-4]
            rotating_human_scans = scans[-4:]

            # print(len(all_scans))
            # print(len(robot_scans))
            # print(len(human_scans))
            # print(len(rotating_human_scans))

            all_results.calc_results(all_scans, localizer, algo, room, x, y)
            robot_results.calc_results(robot_scans, localizer, algo, room, x, y)
            human1_results.calc_results(human_scans, localizer, algo, room, x, y)
            human2_results.calc_results(rotating_human_scans, localizer, algo, room, x, y)

        room_pred_accuracy = all_results.correct_room_preds/all_results.total_room_preds
        print("total room acc:", room_pred_accuracy)
        robot_room_pred_acc = robot_results.correct_room_preds/robot_results.total_room_preds
        print("Robot room acc:", robot_room_pred_acc)
        human1_room_pred_acc = human1_results.correct_room_preds/human1_results.total_room_preds
        print("Human room acc:", human1_room_pred_acc)
        human2_room_pred_acc = human2_results.correct_room_preds/human2_results.total_room_preds
        print("Rotating human room acc:", human2_room_pred_acc, '\n')

        mean_dist = np.mean(all_results.dists)
        mean_dist_in_meters = mean_dist / 60 # 30 pixels = 0.5m => 60 pixels = 1m
        # print("total mean dist:", mean_dist, 'px')
        print("total mean dist:", mean_dist_in_meters, 'm')

        robot_mean_dist = np.mean(robot_results.dists)
        robot_mean_dist_in_meters = robot_mean_dist / 60  # 30 pixels = 0.5m => 60 pixels = 1m
        # print("Robot mean dist:", robot_mean_dist, 'px')
        print("Robot mean dist:", robot_mean_dist_in_meters, 'm')

        human1_mean_dist = np.mean(human1_results.dists)
        human1_mean_dist_in_meters = human1_mean_dist / 60  # 30 pixels = 0.5m => 60 pixels = 1m
        # print("Human mean dist:", human1_mean_dist, 'px')
        print("Human mean dist:", human1_mean_dist_in_meters, 'm')

        human2_mean_dist = np.mean(human2_results.dists)
        human2_mean_dist_in_meters = human2_mean_dist / 60  # 30 pixels = 0.5m => 60 pixels = 1m
        # print("Rotating human mean dist:", human2_mean_dist, 'px')
        print("Rotating human mean dist:", human2_mean_dist_in_meters, 'm')

        algo_data["room_pred_accuracy"] = room_pred_accuracy
        algo_data["robot_room_pred_acc"] = robot_room_pred_acc
        algo_data["human1_room_pred_acc"] = human1_room_pred_acc
        algo_data["human2_room_pred_acc"] = human2_room_pred_acc

        algo_data["mean_dist"] = mean_dist
        algo_data["mean_dist_in_meters"] = mean_dist_in_meters
        algo_data["robot_mean_dist"] = robot_mean_dist
        algo_data["robot_mean_dist_in_meters"] = robot_mean_dist_in_meters
        algo_data["human1_mean_dist"] = human1_mean_dist
        algo_data["human1_mean_dist_in_meters"] = human1_mean_dist_in_meters
        algo_data["human2_mean_dist"] = human2_mean_dist
        algo_data["human2_mean_dist_in_meters"] = human2_mean_dist_in_meters

        algo_data["avg_dist_of_points"] =  [(x/60) for x in all_results.avg_error_at_each_point]
        # print(robot_avg_dist_of_points)
        # print(human1_avg_dist_of_points)
        # print(human2_avg_dist_of_points)
        # print(avg_dist_of_points)

        room_results = []
        for room_result in all_results.room_results:
            print("----", room_result["name"])
            mean_dist_room_error = np.mean(room_result["error_dists"])
            mean_dist_room_error_meters = mean_dist_room_error/60
            room_acc = room_result["correct_room_preds"] / room_result["total_room_preds"]
            print(mean_dist_room_error_meters)
            print(room_acc)
            room_data = {
                "name": room_result["name"],
                "mean_dist_error_in_meters": mean_dist_room_error_meters,
                "room_acc": room_acc
            }
            room_results.append(room_data)

        algo_data["room_results"] = room_results

        response_data.append(algo_data)

    with open('results_' + str(floor_plan_id) + '.json', 'w') as outfile:
        json.dump(json.dumps(response_data), outfile)

    end = time.time()
    print("Done - time:", end - start)
    return HttpResponse(json.dumps(response_data))


@csrf_exempt
def localization_results(request, floor_plan_id):
    limit = request.GET.get('limit')
    avg = request.GET.get('avg')
    filename = 'results_' + str(floor_plan_id)
    if limit == 'first':
        filename += '_first'
    elif limit == 'second':
        filename += '_second'
    elif limit == 'all':
        filename += '_all'

    if avg == 'false':
        filename += '_all'

    filename += '.json'
    with open(filename) as f:
        data = json.load(f)
        return HttpResponse(data)


@csrf_exempt
def localize_point(request, floor_plan_id):
    start = time.time()
    pred_point = {}
    localizer = None
    algorithm = ""
    for local in localizers:
        if local["floor_plan_id"] == floor_plan_id:
            localizer = local["localizer"]

    if request.method == 'POST':
        byte_data = request.body  # this is class byte
        string_data = byte_data.decode('UTF-8')  # convert to string
        list_data = json.loads(string_data)  # convert to python list
        # print(list_data)
        test_point = list_data['networks']
        algorithm = list_data['algorithm']
        pred_point = localizer.find_point(test_point, algorithm)

    end = time.time()
    print("Algo:", algorithm, "Found point_pred: ", pred_point, " - time:", end-start)
    return HttpResponse(json.dumps(pred_point))


@csrf_exempt
def localize_room(request, floor_plan_id):
    start = time.time()
    room_pred = ''
    localizer = None
    for local in localizers:
        if local["floor_plan_id"] == floor_plan_id:
            localizer = local["localizer"]

    if request.method == 'POST':
        byte_data = request.body  # this is class byte
        string_data = byte_data.decode('UTF-8')  # convert to string
        list_data = json.loads(string_data)  # convert to python list
        # print(list_data)

        test_point = list_data['networks']
        algorithm = list_data['algorithm']
        room = localizer.find_room(test_point, algorithm)
        room_pred = room[0]
    data = {
        "room_pred": room_pred
    }
    end = time.time()
    print("Found room_pred: ", data, " - time:", end - start)
    return HttpResponse(json.dumps(data))


@csrf_exempt
def localize_point_prob(request, floor_plan_id):
    start = time.time()
    pred_point = None
    classes = None
    localizer = None
    for local in localizers:
        if local["floor_plan_id"] == floor_plan_id:
            localizer = local["localizer"]

    if request.method == 'POST':
        byte_data = request.body  # this is class byte
        string_data = byte_data.decode('UTF-8')  # convert to string
        list_data = json.loads(string_data)  # convert to python list
        # print(list_data)
        test_point = list_data['networks']
        algorithm = list_data['algorithm']
        point = localizer.find_point(test_point, algorithm, probabilites=True)
        classes = point['classes'].tolist()
        pred_point = point['y_pred'][0].tolist()

    data = {
        'point_pred': pred_point,
        'classes': classes
    }

    end = time.time()
    print("Algo:", algorithm, "Found point_pred: ", json.dumps(data), " - time:", end-start)
    return HttpResponse(json.dumps(data))

@csrf_exempt
def localize_room_prob(request, floor_plan_id):
    start = time.time()
    room_pred = None
    classes = None
    localizer = None
    for local in localizers:
        if local["floor_plan_id"] == floor_plan_id:
            localizer = local["localizer"]

    if request.method == 'POST':
        byte_data = request.body  # this is class byte
        string_data = byte_data.decode('UTF-8')  # convert to string
        list_data = json.loads(string_data)  # convert to python list
        # print(list_data)
        test_point = list_data['networks']
        algorithm = list_data['algorithm']
        room = localizer.find_room(test_point, algorithm, probabilites=True)
        room_pred = room['y_pred'][0].tolist()
        classes = room['classes'].tolist()
    data = {
        "room_pred": room_pred,
        "classes": classes
    }
    end = time.time()
    print("Found room_pred: ", data, " - time:", end - start)
    return HttpResponse(json.dumps(data))

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
            point_x = route_points[data["point"]]["x"]
            point_y = route_points[data["point"]]["y"]
            SignalPoint.objects.create(FloorPlan=floor_plan, x=point_x, y=point_y, networks=json.dumps(data["wifis"]))

            for rm in radio_maps:
                if rm["floor_plan_id"] == floor_plan_id:
                    rm["radio_map"].add_scan_to_radio_map(point_x, point_y, json.dumps(data["wifis"]))
                    rm["radio_map"].make_radio_map()

            response = {
                "message": "New point added..."
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


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer

    def get_queryset(self):
        floor_plan_id = self.request.GET.get('floor_plan_id')
        # print("HELLOOOOO", floor_plan_id)
        if floor_plan_id is None:
            return Room.objects.all()

        floor_plan = get_object_or_404(FloorPlan, pk=floor_plan_id)
        return Room.objects.filter(FloorPlan=floor_plan)


class SignalPointViewSet(viewsets.ModelViewSet):
    serializer_class = SignalPointSerializer

    def get_queryset(self):
        floor_plan_id = self.request.GET.get('floor_plan_id')
        date = self.request.GET.get('date')

        if date is not None and floor_plan_id is not None:
            year = int(date.split('-')[0])
            month = int(date.split('-')[1])
            day = int(date.split('-')[2])
            floor_plan = get_object_or_404(FloorPlan, pk=floor_plan_id)
            return SignalPoint.objects.filter(FloorPlan=floor_plan, created_at__year=year,
                                              created_at__month=month, created_at__day=day)
        if floor_plan_id is None:
            return SignalPoint.objects.all()
        else:
            floor_plan = get_object_or_404(FloorPlan, pk=floor_plan_id)
            return SignalPoint.objects.filter(FloorPlan=floor_plan)


class RouteViewSet(viewsets.ModelViewSet):
    serializer_class = RouteSerializer

    def get_queryset(self):
        floor_plan_id = self.request.GET.get('floor_plan_id')
        # print("HELLOOOOO", floor_plan_id)
        if floor_plan_id is None:
            return Route.objects.all()

        floor_plan = get_object_or_404(FloorPlan, pk=floor_plan_id)
        return Route.objects.filter(FloorPlan=floor_plan)
