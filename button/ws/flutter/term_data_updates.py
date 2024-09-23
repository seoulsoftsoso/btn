from pymongo import MongoClient, DESCENDING
import threading
import asyncio
from channels.layers import get_channel_layer
from django.apps import apps
from rest_framework import status
from django.core.exceptions import AppRegistryNotReady


try:
    from api.models import BomMaster, ItemMaster, OrderProduct, UserMaster, tempUniControl, SenControl, Relay, Plantation
except AppRegistryNotReady:
    # 앱이 준비되지 않았을 때 처리할 로직
    print("Django apps are not loaded yet.")

def listen_to_changes_flutter_term(conId):
    plantations = Plantation.objects.filter(bom_id=conId)
    relays = Relay.objects.filter(container_id__in=plantations)  # Relay 객체 전체를 가져옴
    result = {}
    # 각 relay_id에 대해 delete_flag가 'Y'인 가장 최신 레코드만 가져옴
    for relay in relays:
        latest_control = (
            SenControl.objects.filter(relay_id=relay.id, delete_flag='Y', mode='CYC')
            .last()  # 가장 최신 값을 가져옴
        )
        # 만약 해당 relay_id에 대한 최신 값이 있다면, 맵에 저장
        if latest_control:
            print(f"Latest SenControl ID for relay_id {relay.id}: {latest_control.id}")
            print(f"Part Code: {latest_control.part_code}")
            print(f"Sen ID: {relay.sen_id}")
            # relay의 sen_id를 키로, 최신 control의 value를 값으로 저장
            result[relay.sen_id] = latest_control.value
            print(f"Result for sen_id {relay.sen_id}: {result[relay.sen_id]}")
    send_initial_term_data_flutter(result, conId)


def send_initial_term_data_flutter(result, conid):
    data = {
        'term': result
    }
    asyncio.run(send_update_term_to_ws_flutter(data, conid))


async def send_update_term_to_ws_flutter(data, conid):
    channel_layer = get_channel_layer()
    group_name = f'term_{conid}'  # 동적으로 생성된 그룹 이름 사용
    await channel_layer.group_send(
        group_name,  # Send to the new group
        {
            'type': 'send_update',
            'data': data
        }
    )


def start_listening_to_changes_flutter_term(conid):
    threading.Thread(target=listen_to_changes_flutter_term, args=(conid,), daemon=True).start()
