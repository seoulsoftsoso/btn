import json
import threading
from datetime import datetime

from channels.generic.websocket import AsyncWebsocketConsumer

from api.bom.bom_restframework import CYCLE_RES
from button.ws.mongo_updates import start_listening_to_changes_flutter


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
        print('send?')
        data = event['data']
        await self.send(text_data=json.dumps(data))


class CycleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "cycle_updates"
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

    async def send_cycle_status(self):
        cycle_info = self.get_cycle_status()
        await self.send(text_data=json.dumps(cycle_info))

    def get_cycle_status(self):
        cycle_info_list = []
        for cycle in CYCLE_RES:
            time_after = (datetime.now() - cycle["currentTime"]).total_seconds() / 60
            status = 'on' if cycle["current"] == 'exec' else 'off'
            cycle_info_list.append({
                'senid': cycle['key'],  # 각 센서의 ID
                'status': status,  # 현재 주기 상태
                'exec_time': cycle['exec_time'],  # 실행 시간
                'rest_time': cycle['rest_time'],  # 휴식 시간
                'time_after': time_after  # 경과 시간
            })
        return {'cycles': cycle_info_list}