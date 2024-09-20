from pymongo import MongoClient, DESCENDING
import threading
import asyncio
from channels.layers import get_channel_layer
from django.apps import apps
from rest_framework import status

from api.models import BomMaster, ItemMaster, OrderProduct, UserMaster, tempUniControl, SenControl, Relay, Plantation

def listen_to_changes_flutter_term(conId):
    # container_id를 기준으로 모든 Relay 객체를 가져옴
    plantation = Plantation.objects.filter(bom_id=conId)
    relay_ids = Relay.objects.filter(container_id__in=plantation).values_list('id', flat=True)
    sen_controls = SenControl.objects.filter(relay_id__in=relay_ids)
    print(sen_controls)
    # print(relays)
    print(conId)
    # Relay에 연결된 SenControl의 value 값을 추출하여 맵 형식으로 반환
    # result = {}
    # for relay in relays:
    #     controls = relay.sen_controls.all()
    #     for control in controls:
    #         result[control.part_code] = control.value  # key-value 형식으로 저장


#
#
# def send_initial_data_flutter(unique_gtr_items, unique_sta_items, cont, averages, conId):
#     #         # 클라이언트에게 초기 데이터를 전송하는 함수
#     data = {
#         'unique_gtr_sen_name': unique_gtr_items,
#         'unique_sta_sen_name': unique_sta_items,
#         'con_id_senid_map': cont,
#         'gtr_sen_average': averages
#     }
#     asyncio.run(send_update_to_ws_flutter(data, conId))
#
#
# async def send_update_to_ws_flutter(data, conId):
#     channel_layer = get_channel_layer()
#     group_name = f'group_{conId}'  # 동적으로 생성된 그룹 이름 사용
#
#     await channel_layer.group_send(
#         group_name,  # Send to the new group
#         {
#             'type': 'send_update',
#             'data': data
#         }
#     )


def start_listening_to_changes_flutter_term(conId):
    threading.Thread(target=listen_to_changes_flutter_term, args=(conId,), daemon=True).start()
