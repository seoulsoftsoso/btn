import json
import threading

from channels.generic.websocket import AsyncWebsocketConsumer

from button.ws.flutter.sensors_updates import start_listening_to_changes_flutter
from button.ws.flutter.term_data_updates import start_listening_to_changes_flutter_term


class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'web-table'
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
        await self.send(text_data=json.dumps(data))


class AppConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print('connected')
        self.conId = self.scope['url_route']['kwargs'].get('conId')  # URL 경로에서 conId 가져오기
        self.group_name = f'group_{self.conId}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        if self.conId:  # conId가 있는지 확인
            threading.Thread(target=start_listening_to_changes_flutter, args=(self.conId,), daemon=True).start()

    async def disconnect(self, close_code):
        print('disconnected')
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        print('received')
        data = json.loads(text_data)
        print(data)
        # Handle received message if needed

    async def send_update(self, event):
        data = event['data']
        await self.send(text_data=json.dumps(data))


class FlutterTermConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print('connected')
        self.conId = self.scope['url_route']['kwargs'].get('conId')  # URL 경로에서 conId 가져오기
        self.group_name = f'term_{self.conId}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        if self.conId:  # conId가 있는지 확인
            threading.Thread(target=start_listening_to_changes_flutter_term, args=(self.conId,), daemon=True).start()
        await self.send('dh')

    async def disconnect(self, close_code):
        print('disconnected')
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        print('received')
        data = json.loads(text_data)
        print(data)
        # Handle received message if needed

    async def send_update(self, event):
        data = event['data']
        await self.send(text_data=json.dumps(data))
