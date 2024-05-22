import json
from asgiref.sync import async_to_sync
from channels.exceptions import StopConsumer
from channels.generic.websocket import WebsocketConsumer
from pymongo import MongoClient


class DashboardConsumer(WebsocketConsumer):
    def connect(self):

        # 웹소켓 연결 시 실행되는 함수
        self.accept()

        # MongoDB 연결
        uri = "mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(uri)
        db = client['djangoConnectTest']
        dbSensorGather = db['sen_gather']
        dbSensorStatus = db['sen_status']
        # pipeline = [{'$match': {'operationType': 'insert'}}]  # 예시: 삽입된 문서에 대한 변경만 감지
        with db.watch() as stream:
            for change in stream:
                unique_gtr_senids = dbSensorGather.distinct('senid')
                unique_sta_senids = dbSensorStatus.distinct('senid')
                unique_gtr_con_ids = dbSensorGather.distinct('con_id')
                unique_sta_con_ids = dbSensorStatus.distinct('con_id')

                con_id_senid_map = {}
                for con_id in unique_gtr_con_ids:
                    senids = dbSensorGather.distinct('senid', {'con_id': con_id})
                    senid_grt_value_map = {}
                    for senid in senids:
                        newest_value = dbSensorGather.find_one({'con_id': con_id, 'senid': senid},
                                                               sort=[('c_date', -1)])
                        if newest_value:
                            senid_grt_value_map[senid] = newest_value['value']
                    con_id_senid_map[con_id] = senid_grt_value_map

                for con_id in unique_sta_con_ids:
                    senids = dbSensorStatus.distinct('senid', {'con_id': con_id})
                    senid_sta_value_map = {}
                    for senid in senids:
                        newest_value = dbSensorStatus.find_one({'con_id': con_id, 'senid': senid},
                                                               sort=[('c_date', -1)])
                        if newest_value:
                            senid_sta_value_map[senid] = newest_value['status']
                    con_id_senid_map.setdefault(con_id, {}).update(senid_sta_value_map)
                self.send_initial_data(unique_gtr_senids, unique_sta_senids, con_id_senid_map)

    def websocket_disconnect(self, close_code):
        print('dd')
        # Leave room group

        raise StopConsumer()

    def disconnect(self, close_code):
        print('dd')
        # Leave room group

        raise StopConsumer()
    def receive(self, text_data):
        # 클라이언트로부터 메시지를 받으면 실행되는 함수
        text_data_json = json.loads(text_data)
        # 여기서는 받은 메시지를 처리하거나 필요에 따라 데이터베이스를 업데이트할 수 있습니다.
        # 필요에 따라 데이터베이스를 업데이트한 후 새로운 데이터를 클라이언트에게 전송할 수 있습니다.

    def get_con_id_senid_map(self, unique_gtr_con_ids, unique_sta_con_ids):
        # 데이터베이스에서 con_id와 senid 매핑된 정보 가져오는 함수
        con_id_senid_map = {}
        for con_id in unique_gtr_con_ids:
            senids = self.dbSensorGather.distinct('senid', {'con_id': con_id})
            senid_grt_value_map = {}
            for senid in senids:
                newest_value = self.dbSensorGather.find_one({'con_id': con_id, 'senid': senid}, sort=[('c_date', -1)])
                if newest_value:
                    senid_grt_value_map[senid] = newest_value['value']
            con_id_senid_map[con_id] = senid_grt_value_map

        for con_id in unique_sta_con_ids:
            senids = self.dbSensorStatus.distinct('senid', {'con_id': con_id})
            senid_sta_value_map = {}
            for senid in senids:
                newest_value = self.dbSensorStatus.find_one({'con_id': con_id, 'senid': senid}, sort=[('c_date', -1)])
                if newest_value:
                    senid_sta_value_map[senid] = newest_value['status']
            con_id_senid_map.setdefault(con_id, {}).update(senid_sta_value_map)

        return con_id_senid_map

    def send_initial_data(self, unique_gtr_senids, unique_sta_senids, con_id_senid_map):
        # 클라이언트에게 초기 데이터를 전송하는 함수
        data = {
            'unique_gtr_senids': unique_gtr_senids,
            'unique_sta_senids': unique_sta_senids,
            'con_id_senid_map': con_id_senid_map
        }
        print(data)
        self.send(text_data=json.dumps(data))
