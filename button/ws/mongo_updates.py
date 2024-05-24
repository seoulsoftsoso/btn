import pymongo
import threading
import asyncio
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def listen_to_changes():
    client = pymongo.MongoClient('mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    db = client['djangoConnectTest']
    dbSensorGather = db['sen_gather']
    dbSensorStatus = db['sen_status']
    pipeline = [{'$match': {'operationType': 'insert'}}]
    with db.watch(pipeline) as stream:
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
            send_initial_data(unique_gtr_senids, unique_sta_senids, con_id_senid_map)

            # document = change['fullDocument']
            # asyncio.run(send_update_to_ws(document))
def send_initial_data(unique_gtr_senids, unique_sta_senids, con_id_senid_map):
#         # 클라이언트에게 초기 데이터를 전송하는 함수
        data = {
            'unique_gtr_senids': unique_gtr_senids,
            'unique_sta_senids': unique_sta_senids,
            'con_id_senid_map': con_id_senid_map
        }
        print(data)
        asyncio.run(send_update_to_ws(data))
        # self.send(text_data=json.dumps(data))

async def send_update_to_ws(document):
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        'your_group_name',
        {
            'type': 'send_update',
            'data': document
        }
    )

threading.Thread(target=listen_to_changes, daemon=True).start()
