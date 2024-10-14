from pymongo import MongoClient, DESCENDING
import threading
import asyncio
from channels.layers import get_channel_layer
from django.apps import apps
from django.core.cache import cache

def listen_to_changes(request):
    uri = "mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri)
    db = client['djangoConnectTest']
    dbSensorGather = db['sen_gather']
    OrderProduct = apps.get_model('api', 'OrderProduct')
    BomMaster = apps.get_model('api', 'BomMaster')
    Plantation = apps.get_model('api', 'Plantation')
    Relay = apps.get_model('api', 'Relay')
    pipeline = [{'$match': {'operationType': 'insert'}}]

    # dbSensorGather.create_index([('con_id', 1), ('senid', 1), ('c_date', -1)])
    # dbSensorStatus.create_index([('con_id', 1), ('senid', 1), ('c_date', -1)])

    order_products = OrderProduct.objects.filter(order__client_id=request.user.id)
    bom_masters = BomMaster.objects.filter(id__in=order_products.values_list('bom', flat=True), delete_flag='N')

    container_bom_masters = bom_masters.filter(level=0)
    controller_bom_masters = BomMaster.objects.filter(level=1, delete_flag='N', order__client=request.user.id)
    controller_bom_ids = controller_bom_masters.values_list('id', flat=True)
    sensor_bom_masters = BomMaster.objects.filter(parent__in=controller_bom_ids, level=2, delete_flag='N')
    gtr_bom_masters = sensor_bom_masters.filter(item__item_type='L', delete_flag='N')
    sta_bom_masters = sensor_bom_masters.filter(item__item_type='C', delete_flag='N')
     

    unique_gtr_items = list(set(gtr_bom_masters.values_list('item__item_name', flat=True)))
    unique_sta_items = list(set(sta_bom_masters.values_list('part_code', flat=True)))

    cont = {}
    for container in container_bom_masters:
        con_inf = {}
        con_name = container.part_code
        con_id = container.id
        plantation_id = Plantation.objects.get(bom_id=con_id).id

        controller_ids = controller_bom_masters.filter(parent=con_id).values_list('id', flat=True)
        lv2_gtr_ids = gtr_bom_masters.filter(parent__in=controller_ids).values_list('id', flat=True)
        lv2_sta_ids = sta_bom_masters.filter(parent__in=controller_ids).values_list('id', flat=True)
        gtr_sensor_data = list(dbSensorGather.find(
            {'con_id': con_id, 'senid': {'$in': list(lv2_gtr_ids)}},
            sort=[('c_date', DESCENDING)]
        ).limit(lv2_gtr_ids.count()))
        sta_sensor_data = []
        print(plantation_id)
        relay = Relay.objects.filter(container_id=plantation_id).values_list('sen')
        relay = list(relay)
        control_data = cache.get("{}_{}".format(container, "sensor"), [])
        for idx,key in enumerate(relay):
            sta_sensor_data.append({
                'senid': key[0],
                'status': "on" if control_data[idx] == 1 else "off" if control_data else "-",
                'con_id': con_id
            })


        # gtr_sensor_data = list(dbSensorGather.find({'con_id': con_id, 'senid': {'$in': list(lv2_gtr_ids)}},
        #                                       sort=[('c_date', DESCENDING)]))
        # sta_sensor_data = list(dbSensorStatus.find({'con_id': con_id, 'senid': {'$in': list(lv2_sta_ids)}},
        #                                       sort=[('c_date', DESCENDING)]))
        # gtr_sensor_data = list(dbSensorGather.aggregate([
        #     {'$match': {'con_id': con_id, 'senid': {'$in': list(lv2_gtr_ids)}}},  # Filter matching documents
        #     {'$sort': {'c_date': DESCENDING}},  # Sort by 'c_date' in descending order
        #     {'$group': {
        #         '_id': '$senid',  # Group by 'senid'
        #         'most_recent': {'$first': '$$ROOT'}  # Take the first document in each group after sorting
        #     }}
        # ]))
        # sta_sensor_data = list(dbSensorStatus.aggregate([
        #     {'$match': {'con_id': con_id, 'senid': {'$in': list(lv2_sta_ids)}}},  # Filter matching documents
        #     {'$sort': {'c_date': DESCENDING}},  # Sort by 'c_date' in descending order
        #     {'$group': {
        #         '_id': '$senid',  # Group by 'senid'
        #         'most_recent': {'$first': '$$ROOT'}  # Take the first document in each group after sorting
        #     }}
        # ]))

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
    # 최초 업데이트 전송
    send_initial_data(unique_gtr_items, unique_sta_items, cont)

    # MongoDB 변경 사항을 감지하는 스트림
    with db.watch(pipeline) as stream:
        for change in stream:
            cont = {}
            for container in container_bom_masters:
                con_inf = {}
                con_name = container.part_code
                con_id = container.id
                plantation_id = Plantation.objects.get(bom_id=con_id).id

                controller_ids = controller_bom_masters.filter(parent=con_id).values_list('id', flat=True)
                lv2_gtr_ids = gtr_bom_masters.filter(parent__in=controller_ids).values_list('id', flat=True)
                gtr_sensor_data = list(dbSensorGather.find(
                    {'con_id': con_id, 'senid': {'$in': list(lv2_gtr_ids)}},
                    sort=[('c_date', DESCENDING)]
                ).limit(lv2_gtr_ids.count()))
                sta_sensor_data = []
                print(plantation_id)
                relay = Relay.objects.filter(container_id=plantation_id).values_list('sen')
                relay = list(relay)
                control_data = cache.get("{}_{}".format(container, "sensor"), [])
                for idx,key in enumerate(relay):
                    sta_sensor_data.append({
                        'senid': key[0],
                        'status': "on" if control_data[idx] == 1 else "off" if control_data else "-",
                        'con_id': con_id
                    })

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


def send_initial_data(unique_gtr_items, unique_sta_items, cont):
    #         # 클라이언트에게 초기 데이터를 전송하는 함수
    data = {
        'unique_gtr_sen_name': unique_gtr_items,
        'unique_sta_sen_name': unique_sta_items,
        'con_id_senid_map': cont
    }
    asyncio.run(send_update_to_ws(data))


async def send_update_to_ws(document):
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        'web-table',
        {
            'type': 'send_update',
            'data': document
        }
    )


def start_listening_to_changes(request):
    threading.Thread(target=listen_to_changes, args=(request,), daemon=True).start()

