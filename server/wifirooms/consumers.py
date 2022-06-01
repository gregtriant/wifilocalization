from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import random
from .wifi_scan import WifiScaner
from .models import FloorPlan, SignalPoint
from .wifi_localization import Localization
from .wifi_globals import connectedWS


class BrowserConsumer(AsyncWebsocketConsumer):
    groups = ["browsers"]
    id = -1

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
        # print(self.id)
        # connectedWS.append(self)
        # print("channel name: ", self.channel_name)
        await self.channel_layer.group_add("browsers", self.channel_name)
        # await self.channel_layer.group_send(
        #     "browsers",
        #     {
        #         "type": "new.connection",
        #         "data": self.channel_name,
        #     },
        # )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print("Socket data: ", text_data_json)
        if text_data_json['message'] == 'NEW_POINT':
            print("new point")
            # point = text_data_json["point"]
            # networks = text_data_json["wifiList"]
            # # scan wifi for this point
            # # networks = WifiScaner().scan()  # returns a dictionary with the local wifi networks
            # # print("Networks found: ", networks)
            # #
            # # # add point to the database
            # print("adding point to database")
            # floor_plan = await self.get_floor_plan(text_data_json["floor_plan_id"])
            # await self.post_signal_point(floor_plan, point["x"], point["y"], json.dumps(networks))
            # #
            # # # send response
            # data = {
            #     "message": "SCAN_FINISHED",
            #     "networks": networks
            # }
            # await self.send(json.dumps(data))

        elif text_data_json['message'] == 'TEST_POINT':
            print("test point")
            # point = text_data_json['point']
            # print(point)
            # print(point['x'])
            #
            # floor_plan = await self.get_floor_plan(1)
            # print(floor_plan)
            #
            # # signal_points = await self.get_signal_points()
            # # print(signal_points)
            # # await print(signal_points)
            #
            # # wifiList = text_data_json['wifiList']
            # # print(type(wifiList[0]))
            # # knns = self.Localizer.knn(signal_points, wifiList, 4)
            # # print(knns)

        elif text_data_json['message'] == 'GET_CONNECTED_WS':
            await self.channel_layer.group_send(
                "browsers",
                {
                    "type": "get.connected.ws",
                    "data": "sending connected WS",
                },
            )

    # events from Channel Layers
    async def new_connection(self, event):
        print("new connection", event["data"])

    async def get_connected_ws(self, event):
        data = {
            "message": "CONNECTED_WS",
            "data": event["data"]
        }
        await self.send(json.dumps(data))

    async def fingerprint_location(self, event):
        data = {
            "message": "FINGERPRINT_LOCATION",
            "data": event["data"]
        }
        await self.send(json.dumps(data))

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
        await self.channel_layer.group_discard("browsers", self.channel_name)
        # for ws in connectedWS:
        #     if ws.id == self.id:
        #         connectedWS.remove(ws)
        #         break
        pass
