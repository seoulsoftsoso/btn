import pymongo
import threading
import asyncio
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.apps import apps

def listen_to_changes():
    OrderMaster = apps.get_model('api', 'OrderMaster')
    OrderProduct = apps.get_model('api', 'OrderProduct')
    BomMaster = apps.get_model('api', 'BomMaster')
    ItemMaster = apps.get_model('api', 'ItemMaster')

    om_op = OrderMaster.objects.filter(client=1)  # 1. 로그인 계정이 한 주문들.
    order_ids = om_op.values_list('id', flat=True)  # 2. 1에서 id만 리스트로 만듬.
    op_oi = OrderProduct.objects.filter(order__in=order_ids)  # 3. orderProduct에서 2의 리스트에 해당되는게 있는 row만 고름.
    bom_ids = op_oi.values_list('bom', flat=True)  # 4. 3에서의 bom_id만 리스트로 만듬.
    bom_masters = BomMaster.objects.filter(id__in=bom_ids)  # 5. 3을통해 드디어 로그인 계정과 관련된 BOMMaster를 골라냄.
    #######################
    bom_level_1_masters = bom_masters.filter(level=1)
    bom_level_1_ids = bom_level_1_masters.values_list('item', flat=True)  # 6. 5에서 level=1인 애들의 item_id를 리스트로 만듬.
    header_item_masters = ItemMaster.objects.filter(id__in=bom_level_1_ids,
                                                    item_type='A')  # 7. 6에서 해당되는것들이 타입A인지 itemMaster에서 골라냄. 컨트롤러! #지금 A가 안나뉘어짐!!!!
    header_items_ids = header_item_masters.values_list('id', flat=True)  # 8. 7에서 골라낸것들의 id만 리스트로 만듬. 컨트롤러!
    controller_bom_masters = bom_masters.filter(level=1, item__in=header_items_ids)
    controller_bom_ids = controller_bom_masters.values_list('id', flat=True)  # 9. 5중에서 타입A인것들만 추려내고 id를 리스트로 만듬
    controller_sensors_bom_masters = bom_masters.filter(
        parent__in=controller_bom_ids)  # 10. 봄마스터에서 parent_id가 9에서 구한것과 같은애들만 모음. 얘들은 이제 화면에 보여질 센서들.
    # 11~15는 센서가 제어인지 수집인지를 구하기위한 과정.
    bom_level_2_ids = controller_sensors_bom_masters.values_list('item', flat=True)  # 11. 센서들의 item_id를 리스트로 만듬
    gtr_items = ItemMaster.objects.filter(id__in=bom_level_2_ids,
                                          item_type='L')  # 12. 11에서 구한것들을 itemMaster에 비교하는데 그때의 타입이 수집인것만 분류함
    sta_items = ItemMaster.objects.filter(id__in=bom_level_2_ids,
                                          item_type='C')  # 13. 11에서 구한것들을 itemMaster에 비교하는데 그때의 타입이 제어인것만 분류함
    gtr_item_ids = gtr_items.values_list('id', flat=True)  # 14. 12에서 구한분류에서 id만 리스트로 만듬
    sta_item_ids = sta_items.values_list('id', flat=True)  # 15. 13에서 구한분류에서 id만 리스트로 만듬
    #####
    gtr_bom_masters = bom_masters.filter(item__in=gtr_item_ids)  # 16. 봄마스터에서 수집센서에 대한것만 분류
    sta_bom_masters = bom_masters.filter(item__in=sta_item_ids)  # 17. 봄마스터에서 제어 센서에 대한것만 분류

    unique_gtr_items = list(gtr_items.values_list('item_name', flat=True))
    unique_sta_items = list(sta_items.values_list('item_name', flat=True))

    bom_level_1_pid = controller_bom_masters.values_list('parent', flat=True)

    client = pymongo.MongoClient('mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    db = client['djangoConnectTest']
    dbSensorGather = db['sen_gather']
    dbSensorStatus = db['sen_status']
    pipeline = [{'$match': {'operationType': 'insert'}}]
    with db.watch(pipeline) as stream:
        for change in stream:
            cont = {}
            for con_id in bom_level_1_pid:
                con_inf = {}
                con_item = bom_masters.objects.get(id=con_id)
                con_item_id = con_item.item
                con_name = ItemMaster.objects.get(id=con_item_id).name

                lv1_ids = controller_bom_masters.filter(parent__in=con_id).values_list('id', flat=True)
                lv2_gtr = gtr_bom_masters.filter(parent__in=lv1_ids)
                lv2_sta = sta_bom_masters.filter(parent__in=lv1_ids)
                gtr_ids = lv2_gtr.values_list('id', flat=True)
                sta_ids = lv2_sta.values_list('id', flat=True)

                gtr_sen = {}
                for senid in gtr_ids:
                    sen_inf = {}
                    sen_name = ItemMaster.objects.get(id=senid).name
                    newest_value = dbSensorGather.find_one({'con_id': con_id, 'senid': senid}, sort=[('c_date', -1)])
                    sen_inf['sen_name'] = sen_name
                    sen_inf['value'] = newest_value['value']

                    gtr_sen[senid] = sen_inf

                sta_sen = {}
                for senid in sta_ids:
                    sen_inf = {}
                    sen_name = ItemMaster.objects.get(id=senid).name
                    newest_value = dbSensorStatus.find_one({'con_id': con_id, 'senid': senid}, sort=[('c_date', -1)])
                    sen_inf['sen_name'] = sen_name
                    sen_inf['status'] = newest_value['status']

                    sta_sen[senid] = sen_inf

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
def start_listening_to_changes():
    threading.Thread(target=listen_to_changes, daemon=True).start()

@receiver(post_migrate)
def start_thread(sender, **kwargs):
    start_listening_to_changes()

