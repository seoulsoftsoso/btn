from pymongo import MongoClient, DESCENDING
import threading
import asyncio
from channels.layers import get_channel_layer
from django.apps import apps

def listen_to_changes_flutter(conId):
    uri = "mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri)
    db = client['djangoConnectTest']
    dbSensorGather = db['sen_gather']
    dbSensorStatus = db['sen_status']
    pipeline = [{'$match': {'operationType': 'insert'}}]

    BomMaster = apps.get_model('api', 'BomMaster')
    container_bom_masters = BomMaster.objects.get(id=conId)
    controller_bom_masters = BomMaster.objects.filter(level=1, parent=conId, delete_flag='N')
    controller_bom_ids = controller_bom_masters.values_list('id', flat=True)
    sensor_bom_masters = BomMaster.objects.filter(parent__in=controller_bom_ids, level=2, delete_flag='N')
    gtr_bom_masters = sensor_bom_masters.filter(item__item_type='L')
    sta_bom_masters = sensor_bom_masters.filter(item__item_type='C')

    unique_gtr_items = list(gtr_bom_masters.values_list('item__item_name', flat=True).distinct())
    unique_sta_items = list(sta_bom_masters.values_list('part_code', flat=True).distinct())
    # last_processed_id = None
    # last_cluster_time = None

    with db.watch(pipeline) as stream:
        for change in stream:
            cont = {}
            con_inf = {}
            con_name = container_bom_masters.part_code
            con_id = container_bom_masters.id

            controller_ids = controller_bom_masters.filter(parent=con_id).values_list('id', flat=True)
            lv2_gtr_ids = gtr_bom_masters.filter(parent__in=controller_ids).values_list('id', flat=True)
            lv2_sta_ids = sta_bom_masters.filter(parent__in=controller_ids).values_list('id', flat=True)
            gtr_sensor_data = list(dbSensorGather.find({'con_id': con_id, 'senid': {'$in': list(lv2_gtr_ids)}},
                                                       sort=[('c_date', DESCENDING)]).limit(lv2_gtr_ids.count()))
            sta_sensor_data = list(dbSensorStatus.find({'con_id': con_id, 'senid': {'$in': list(lv2_sta_ids)}},
                                                       sort=[('c_date', DESCENDING)]).limit(lv2_sta_ids.count()))
            gtr_sen = {}
            for sensor in gtr_bom_masters.filter(parent__in=controller_ids, item__item_type='L'):
                sen_inf = {'sen_name': sensor.item.item_name}
                newest_value = next((x for x in gtr_sensor_data if x['senid'] == sensor.id), None)
                sen_inf['value'] = newest_value['value'] if newest_value else 0
                gtr_sen[sensor.id] = sen_inf

            sta_sen = {}
            for sensor in sta_bom_masters.filter(parent__in=controller_ids, item__item_type='C'):
                sen_inf = {'sen_name': sensor.part_code}
                newest_value = next((x for x in sta_sensor_data if x['senid'] == sensor.id), None)
                sen_inf['status'] = newest_value['status'] if newest_value else '-'
                sta_sen[sensor.id] = sen_inf

            con_inf['con_name'] = con_name
            con_inf['gtr'] = gtr_sen
            con_inf['sta'] = sta_sen
            cont[con_id] = con_inf

            averages = {}
            for item in unique_gtr_items:
                matching_gtr_sensors = [v['value'] for v in gtr_sen.values() if
                                        v['sen_name'] == item and v['value'] is not None]
                if matching_gtr_sensors:
                    average_value = sum(matching_gtr_sensors) / len(matching_gtr_sensors)
                else:
                    average_value = None
                averages[item] = average_value

            int_averages = {k: int(v) if v is not None else None for k, v in averages.items()}

            print("Average values for matching gtr_sensors:", averages)

            send_initial_data_flutter(unique_gtr_items, unique_sta_items, cont, int_averages, conId)

        # document = change['fullDocument']
        # asyncio.run(send_update_to_ws(document))


def send_initial_data_flutter(unique_gtr_items, unique_sta_items, cont, averages, conId):
    #         # 클라이언트에게 초기 데이터를 전송하는 함수
    data = {
        'unique_gtr_sen_name': unique_gtr_items,
        'unique_sta_sen_name': unique_sta_items,
        'con_id_senid_map': cont,
        'gtr_sen_average': averages
    }
    asyncio.run(send_update_to_ws_flutter(data, conId))


async def send_update_to_ws_flutter(data, conId):
    channel_layer = get_channel_layer()
    group_name = f'group_{conId}'  # 동적으로 생성된 그룹 이름 사용

    await channel_layer.group_send(
        group_name,  # Send to the new group
        {
            'type': 'send_update',
            'data': data
        }
    )


def start_listening_to_changes_flutter(conId):
    threading.Thread(target=listen_to_changes_flutter, args=(conId,), daemon=True).start()
