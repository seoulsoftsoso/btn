import json
from asgiref.sync import async_to_sync
from channels.exceptions import StopConsumer
from channels.generic.websocket import WebsocketConsumer
from pymongo import MongoClient
from api.models import BomMaster, ItemMaster, OrderProduct, OrderMaster


class DashboardConsumer(WebsocketConsumer):
    def connect(self):

        # 웹소켓 연결 시 실행되는 함수
        self.accept()

        om_op = OrderMaster.objects.filter(client=self.request.user.id)  # 1. 로그인 계정이 한 주문들.
        order_ids = om_op.values_list('id', flat=True)  # 2. 1에서 id만 리스트로 만듬.
        op_oi = OrderProduct.objects.filter(order__in=order_ids)  # 3. orderProduct에서 2의 리스트에 해당되는게 있는 row만 고름.
        bom_ids = op_oi.values_list('bom', flat=True)  # 4. 3에서의 bom_id만 리스트로 만듬.
        bom_masters = BomMaster.objects.filter(id__in=bom_ids)  # 5. 3을통해 드디어 로그인 계정과 관련된 BOMMaster를 골라냄.
        #######################
        bom_level_1_masters = bom_masters.filter(level=1)
        bom_level_1_ids = bom_level_1_masters.values_list('item', flat=True)  # 6. 5에서 level=1인 애들의 item_id를 리스트로 만듬.
        header_item_masters = ItemMaster.objects.filter(id__in=bom_level_1_ids,
                                                        type='A')  # 7. 6에서 해당되는것들이 타입A인지 itemMaster에서 골라냄.
        header_items_ids = header_item_masters.values_list('id', flat=True)  # 8. 7에서 골라낸것들의 id만 리스트로 만듬
        controller_bom_masters = bom_masters.filter(level=1, item__in=header_items_ids)
        controller_bom_ids = controller_bom_masters.values_list('id', flat=True)  # 9. 5중에서 타입A인것들만 추려내고 id를 리스트로 만듬
        controller_sensors_bom_masters = bom_masters.filter(
            parent__in=controller_bom_ids)  # 10. 봄마스터에서 parent_id가 9에서 구한것과 같은애들만 모음. 얘들은 이제 화면에 보여질 센서들.
        # 11~15는 센서가 제어인지 수집인지를 구하기위한 과정.
        bom_level_2_ids = controller_sensors_bom_masters.values_list('item', flat=True)  # 11. 센서들의 item_id를 리스트로 만듬
        gtr_items = ItemMaster.objects.filter(id__in=bom_level_2_ids,
                                              type='L')  # 12. 11에서 구한것들을 itemMaster에 비교하는데 그때의 타입이 수집인것만 분류함
        sta_items = ItemMaster.objects.filter(id__in=bom_level_2_ids,
                                              type='C')  # 13. 11에서 구한것들을 itemMaster에 비교하는데 그때의 타입이 제어인것만 분류함
        gtr_item_ids = gtr_items.values_list('id', flat=True)  # 14. 12에서 구한분류에서 id만 리스트로 만듬
        sta_item_ids = sta_items.values_list('id', flat=True)  # 15. 13에서 구한분류에서 id만 리스트로 만듬
        #####
        gtr_bom_masters = bom_masters.objects.filter(item__in=gtr_item_ids)  # 16. 봄마스터에서 수집센서에 대한것만 분류
        sta_bom_masters = bom_masters.objects.filter(item__in=sta_item_ids)  # 17. 봄마스터에서 제어 센서에 대한것만 분류

        unique_gtr_items = list(gtr_items.values_list('name', flat=True))
        unique_sta_items = list(sta_items.values_list('name', flat=True))

        print(bom_ids)
        print(request.user.id)
        # containers = bom_masters.objects.filter(level=0)
        bom_level_1_pid = controller_bom_masters.values_list('pid', flat=True)

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
