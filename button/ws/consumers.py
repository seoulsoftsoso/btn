import asyncio
import json
import threading

from channels.generic.websocket import AsyncWebsocketConsumer

from button.ws.flutter.sensors_updates import listen_to_changes_flutter
from button.ws.flutter.term_data_updates import listen_to_changes_flutter_term


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
    def __init__(self):
        super().__init__()
        self.mongo_thread = None  # MongoDB 리슨 스레드 참조 저장
        self.mongo_listening = False  # MongoDB 리슨 중인지 여부
        self.stream = None  # MongoDB 스트림 참조

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
            if self.conId:
                self.mongo_listening = True  # MongoDB 리슨 중으로 표시
                self.mongo_thread = threading.Thread(
                    target=self.start_listening_to_changes_flutter,
                    args=(self.conId,),
                    daemon=True
                )
                self.mongo_thread.start()

    async def disconnect(self, close_code):
        print('disconnected')
        self.mongo_listening = False  # MongoDB 리슨을 중단하도록 설정

        # MongoDB 스트림 종료
        if self.stream:
            self.stream.close()  # MongoDB 스트림 종료

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

    def start_listening_to_changes_flutter(self, conId):
        # MongoDB 리슨 스레드에서 실행되는 함수
        listen_to_changes_flutter(conId, self)


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
            threading.Thread(target=listen_to_changes_flutter_term, args=(self.conId,), daemon=True).start()

    async def disconnect(self, close_code):
        print('disconnected')
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        print('receidddved')
        data = json.loads(text_data)
        print(data)
        await asyncio.sleep(5)  # 5초 지연
        threading.Thread(target=listen_to_changes_flutter_term, args=(self.conId,), daemon=True).start()

    async def send_update(self, event):
        data = event['data']
        await self.send(text_data=json.dumps(data))
