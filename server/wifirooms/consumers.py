from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import random


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

    async def robot_location(self, event):
        data = {
            "message": "ROBOT_LOCATION",
            "data": event["data"]
        }
        await self.send(json.dumps(data))

    async def test_progress(self, event):
        data = {
            "message": "TEST_PROGRESS",
            "data": event["data"]
        }
        await self.send(json.dumps(data))
    # @database_sync_to_async
    # def get_signal_points(self):
    #     return SignalPoint.objects.all()
    #
    # @database_sync_to_async
    # def post_signal_point(self, floor_plan, x, y, networks):
    #     SignalPoint.objects.create(FloorPlan=floor_plan, x=x, y=y, networks=networks)
    #
    # @database_sync_to_async
    # def get_floor_plan(self, floor_plan_id):
    #     floor_plan = FloorPlan.objects.get(pk=floor_plan_id)
    #     return floor_plan

    async def disconnect(self, close_code):
        # Called when the socket closes
        print('WS connection closed.', self.id)
        await self.channel_layer.group_discard("browsers", self.channel_name)
        # for ws in connectedWS:
        #     if ws.id == self.id:
        #         connectedWS.remove(ws)
        #         break
        pass
