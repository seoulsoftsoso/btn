import threading
import asyncio
from channels.layers import get_channel_layer
from django.apps import apps


def listen_to_changes_flutter_term(conId):
    Plantation = apps.get_model('api', 'Plantation')
    Relay = apps.get_model('api', 'Relay')
    SenControl = apps.get_model('api', 'SenControl')
    plantations = Plantation.objects.filter(bom_id=conId)
    relays = Relay.objects.filter(container_id__in=plantations)  # Relay 객체 전체를 가져옴
    result = {}
    # 각 relay_id에 대해 delete_flag가 'Y'인 가장 최신 레코드만 가져옴
    for relay in relays:
        latest_control = (
            SenControl.objects.filter(relay_id=relay.id, delete_flag='Y')
            .last()  # 가장 최신 값을 가져옴
        )
        if latest_control:
            if latest_control.mode == 'CYC':
                value = latest_control.value
                # 문자열이 "[0,0]"인 경우 패스
                if value == "[0, 0]":
                    print(f"Skipping relay_id {relay.id} because value is [0,0]")
                    continue
                print(f"Latest SenControl ID for relay_id {relay.id}: {latest_control.id}")
                print(f"Part Code: {latest_control.part_code}")
                print(f"Sen ID: {relay.sen_id}")

                # relay의 sen_id를 키로, 최신 control의 value를 값으로 저장
                result[relay.sen_id] = value
                print(f"Result for sen_id {relay.sen_id}: {result[relay.sen_id]}")
            elif latest_control.mode == 'RSV_CYC':
                value = latest_control.value

                result[relay.sen_id] = value
                print(f"Result for sen_id {relay.sen_id}: {result[relay.sen_id]}")
                print('RSV_CYC!!!!!')
                continue
            else:
                print('else!!!!!!!')
                continue
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
