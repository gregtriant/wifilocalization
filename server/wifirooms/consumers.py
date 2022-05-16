from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import random
from .wifi_scan import WifiScaner
from .models import FloorPlan, SignalPoint
from .wifi_localization import Localization


class GraphConsumer(AsyncWebsocketConsumer):
    # groups = ["broadcast"]
    id = -1
    # Localizer = Localization()

    async def connect(self):
        # print('New WS connection.')
        await self.accept()
        # send response
        self.id = random.randint(0, 1000000)
        data = {
            "message": "CONNECTED",
            "id": self.id
        }
        print(data)
        await self.send(json.dumps(data))

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print(text_data_json)
        if text_data_json['message'] == 'NEW_POINT':
            point = text_data_json["point"]
            networks = text_data_json["wifiList"]
            # scan wifi for this point
            # networks = WifiScaner().scan()  # returns a dictionary with the local wifi networks
            # print("Networks found: ", networks)
            #
            # # add point to the database
            print("adding point to database")
            floor_plan = await self.get_floor_plan(text_data_json["floor_plan_id"])
            await self.post_signal_point(floor_plan, point["x"], point["y"], json.dumps(networks))
            #
            # # send response
            data = {
                "message": "SCAN_FINISHED",
                "networks": networks
            }
            await self.send(json.dumps(data))

        elif text_data_json['message'] == 'TEST_POINT':
            point = text_data_json['point']
            print(point)
            print(point['x'])

            floor_plan = await self.get_floor_plan(1)
            print(floor_plan)

            # signal_points = await self.get_signal_points()
            # print(signal_points)
            # await print(signal_points)

            # wifiList = text_data_json['wifiList']
            # print(type(wifiList[0]))
            # knns = self.Localizer.knn(signal_points, wifiList, 4)
            # print(knns)

    @database_sync_to_async
    def get_signal_points(self):
        return SignalPoint.objects.all()

    @database_sync_to_async
    def post_signal_point(self, floor_plan, x, y, networks):
        SignalPoint.objects.create(FloorPlan=floor_plan, x=x, y=y, networks=networks)

    @database_sync_to_async
    def get_floor_plan(self, floor_plan_id):
        floor_plan = FloorPlan.objects.get(pk=floor_plan_id)
        return floor_plan

    async def disconnect(self, close_code):
        # Called when the socket closes
        print('WS connection closed.', self.id)
        pass
