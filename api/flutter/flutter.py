from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
import json


from django.http import JsonResponse
from api.models import BomMaster, ItemMaster, OrderProduct, OrderMaster
from pymongo import MongoClient, ASCENDING, DESCENDING
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.views.decorators.csrf import csrf_exempt


def csrf(request):
    csrf_token = get_token(request)
    return JsonResponse({'csrf_token': csrf_token})

@csrf_exempt  # Exempt this view from CSRF protection for simplicity
def login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Authentication successful
            return JsonResponse({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    # Add other fields as necessary
                }
            })
        else:
            # Authentication failed
            return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@csrf_exempt  # You can use this if you're not using CSRF tokens
def container_map(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')

        if not user_id:
            return JsonResponse({'error': 'User ID not provided'}, status=400)

        uri = "mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(uri)
        db = client['djangoConnectTest']
        dbSensorGather = db['sen_gather']
        dbSensorStatus = db['sen_status']
        dbSensorGather.create_index([('con_id', 1), ('senid', 1), ('c_date', -1)])
        dbSensorStatus.create_index([('con_id', 1), ('senid', 1), ('c_date', -1)])

        order_products = OrderProduct.objects.filter(order__client=user_id)
        bom_masters = BomMaster.objects.filter(id__in=order_products.values_list('bom', flat=True))

        container_bom_masters = bom_masters.filter(level=0)
        controller_bom_masters = BomMaster.objects.filter(level=1, item__item_type='AC')
        controller_bom_ids = controller_bom_masters.values_list('id', flat=True)
        sensor_bom_masters = BomMaster.objects.filter(parent__in=controller_bom_ids, level=2)
        gtr_bom_masters = sensor_bom_masters.filter(item__item_type='L')
        sta_bom_masters = sensor_bom_masters.filter(item__item_type='C')

        unique_gtr_items = list(set(gtr_bom_masters.values_list('item__item_name', flat=True)))
        unique_sta_items = list(set(sta_bom_masters.values_list('part_code', flat=True)))

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

        initial_data = {
            'unique_gtr_sen_name': unique_gtr_items,
            'unique_sta_sen_name': unique_sta_items,
            'con_id_senid_map': cont
        }
        return JsonResponse(initial_data, encoder=DjangoJSONEncoder)

    return JsonResponse({'error': 'Invalid request method'}, status=400)
