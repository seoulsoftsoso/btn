from pymongo import MongoClient, ASCENDING, DESCENDING
import threading
import asyncio
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.apps import apps

def listen_to_changes(request):
    uri = "mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri)
    db = client['djangoConnectTest']
    dbSensorGather = db['sen_gather']
    dbSensorStatus = db['sen_status']
    dbSensorGather.create_index([('con_id', 1), ('senid', 1), ('c_date', -1)])
    dbSensorStatus.create_index([('con_id', 1), ('senid', 1), ('c_date', -1)])
    pipeline = [{'$match': {'operationType': 'insert'}}]

    OrderMaster = apps.get_model('api', 'OrderMaster')
    OrderProduct = apps.get_model('api', 'OrderProduct')
    BomMaster = apps.get_model('api', 'BomMaster')
    ItemMaster = apps.get_model('api', 'ItemMaster')

    order_products = OrderProduct.objects.filter(order__client=request.user.id)
    bom_masters = BomMaster.objects.filter(id__in=order_products.values_list('bom', flat=True))

    container_bom_masters = bom_masters.filter(level=0)
    controller_bom_masters = bom_masters.filter(level=1, item__item_type='AC')
    controller_bom_ids = controller_bom_masters.values_list('id', flat=True)
    sensor_bom_masters = BomMaster.objects.filter(parent__in=controller_bom_ids, level=2)
    gtr_bom_masters = sensor_bom_masters.filter(item__item_type='L')
    sta_bom_masters = sensor_bom_masters.filter(item__item_type='C')

    unique_gtr_items = list(set(gtr_bom_masters.values_list('item__item_name', flat=True)))
    unique_sta_items = list(set(sta_bom_masters.values_list('part_code', flat=True)))


    with db.watch(pipeline) as stream:
        for change in stream:
            cont = {}
            for container in container_bom_masters:
                con_inf = {}
                con_name = container.part_code
                con_id = container.id

                controller_ids = controller_bom_masters.filter(parent=con_id).values_list('id', flat=True)
                lv2_gtr_ids = gtr_bom_masters.filter(parent__in=controller_ids).values_list('id', flat=True)
                lv2_sta_ids = sta_bom_masters.filter(parent__in=controller_ids).values_list('id', flat=True)
                gtr_sensor_data = list(dbSensorGather.find({'con_id': con_id, 'senid': {'$in': list(lv2_gtr_ids)}},
                                                           sort=[('c_date', DESCENDING)]))
                sta_sensor_data = list(dbSensorStatus.find({'con_id': con_id, 'senid': {'$in': list(lv2_sta_ids)}},
                                                           sort=[('c_date', DESCENDING)]))
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

            send_initial_data(unique_gtr_items, unique_sta_items, cont)

            # document = change['fullDocument']
            # asyncio.run(send_update_to_ws(document))
def send_initial_data(unique_gtr_items, unique_sta_items, cont):
#         # 클라이언트에게 초기 데이터를 전송하는 함수
        data = {
            'unique_gtr_sen_name': unique_gtr_items,
            'unique_sta_sen_name': unique_sta_items,
            'con_id_senid_map': cont
        }
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
def start_listening_to_changes(request):
    threading.Thread(target=listen_to_changes, args=(request,), daemon=True).start()
