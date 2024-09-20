import threading
import asyncio
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from api.models import BomMaster, ItemMaster, OrderProduct, UserMaster, tempUniControl, SenControl, Relay, Plantation

def listen_to_changes_flutter_term(conId):
    # container_id를 기준으로 모든 Relay 객체를 가져옴
    plantations = Plantation.objects.filter(bom_id=conId)
    relays = Relay.objects.filter(container_id__in=plantations)  # Relay 객체 전체를 가져옴
    result = {}

    # 각 relay_id에 대해 delete_flag가 'Y'인 가장 최신 레코드만 가져옴
    for relay in relays:
        latest_control = (
            SenControl.objects.filter(relay_id=relay.id, delete_flag='N', mode='CYC')
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


def send_initial_term_data_flutter(result, conId):
    data = {
        'term': result
    }
    asyncio.run(send_update_term_to_ws_flutter(data, conId))


async def send_update_term_to_ws_flutter(data, conId):
    channel_layer = get_channel_layer()
    group_name = f'term_{conId}'  # 동적으로 생성된 그룹 이름 사용

    await channel_layer.group_send(
        group_name,  # Send to the new group
        {
            'type': 'send_update',
            'data': data
        }
    )


def start_listening_to_changes_flutter_term(conId):
    threading.Thread(target=listen_to_changes_flutter_term, args=(conId,), daemon=True).start()

