import json
from channels.generic.websocket import AsyncWebsocketConsumer
class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'your_group_name'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Handle received message if needed

    async def send_update(self, event):
        data = event['data']
        print(data)
        await self.send(text_data=json.dumps(data))
