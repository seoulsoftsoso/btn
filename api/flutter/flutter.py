import pytz
from dateutil.parser import isoparse
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta


from django.http import JsonResponse
from api.models import BomMaster, ItemMaster, OrderProduct, OrderMaster
from pymongo import MongoClient, ASCENDING, DESCENDING
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.views.decorators.csrf import csrf_exempt

from button.ws.mongo_updates import start_listening_to_changes_flutter


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


        order_products = OrderProduct.objects.filter(order__client=user_id)
        bom_masters = BomMaster.objects.filter(id__in=order_products.values_list('bom', flat=True), delete_flag='N')

        container_bom_masters = bom_masters.filter(level=0)

        cont = {}
        for container in container_bom_masters:
            con_inf = {}
            con_name = container.part_code
            con_id = container.id
            con_inf['con_name'] = con_name
            cont[con_id] = con_inf

        initial_data = {
            'con_id_senid_map': cont
        }
        print(initial_data)
        return JsonResponse(initial_data, encoder=DjangoJSONEncoder)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt  # You can use this if you're not using CSRF tokens
def container_sen_map(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        conId = data.get('conId')
        start_listening_to_changes_flutter(conId)

        if not user_id:
            return JsonResponse({'error': 'User ID not provided'}, status=400)

        if not conId:
            return JsonResponse({'error': 'conID not provided'}, status=400)

        # uri = "mongodb://localhost:27017/"
        uri = "mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(uri)
        db = client['djangoConnectTest']
        dbSensorGather = db['sen_gather']
        dbSensorStatus = db['sen_status']

        container_bom_masters = BomMaster.objects.filter(level=0, id=conId)
        controller_bom_masters = BomMaster.objects.filter(level=1, parent=conId, delete_flag='N')
        controller_bom_ids = controller_bom_masters.values_list('id', flat=True)
        sensor_bom_masters = BomMaster.objects.filter(parent__in=controller_bom_ids, level=2, delete_flag='N')
        gtr_bom_masters = sensor_bom_masters.filter(item__item_type='L')
        sta_bom_masters = sensor_bom_masters.filter(item__item_type='C')
        unique_gtr_items = list(gtr_bom_masters.values_list('item__item_name', flat=True).distinct())
        unique_sta_items = list(sta_bom_masters.values_list('part_code', flat=True).distinct())

        cont = {}
        con_inf = {}
        con_name = container_bom_masters.part_code
        con_id = container_bom_masters.id

        lv2_gtr_ids = list(gtr_bom_masters.values_list('id', flat=True))
        lv2_sta_ids = list(sta_bom_masters.values_list('id', flat=True))

        gtr_sensor_data = list(
            dbSensorGather.find({'con_id': con_id, 'senid': {'$in': lv2_gtr_ids}}, sort=[('c_date', DESCENDING)]).limit(lv2_gtr_ids.count()))

        sta_sensor_data = list(
            dbSensorStatus.find({'con_id': con_id, 'senid': {'$in': lv2_sta_ids}}, sort=[('c_date', DESCENDING)]).limit(lv2_sta_ids.count()))

        #
        # gtr_sensor_data = list(dbSensorGather.find(
        #     {'con_id': con_id, 'senid': {'$in': list(lv2_gtr_ids)}},
        #     sort=[('c_date', DESCENDING)]
        # ).limit(lv2_gtr_ids.count()))
        # sta_sensor_data = list(dbSensorGather.find(
        #     {'con_id': con_id, 'senid': {'$in': list(lv2_sta_ids)}},
        #     sort=[('c_date', DESCENDING)]
        # ).limit(lv2_sta_ids.count()))

        gtr_sen = {
            sensor.id: {
                'sen_name': sensor.item.item_name,
                'value': next((x['value'] for x in gtr_sensor_data if x['senid'] == sensor.id), 0)
            }
            for sensor in gtr_bom_masters.filter(parent__in=controller_bom_ids, item__item_type='L')
        }

        sta_sen = {
            sensor.id: {
                'sen_name': sensor.part_code,
                'status': next((x['status'] for x in sta_sensor_data if x['senid'] == sensor.id), '-')
            }
            for sensor in sta_bom_masters.filter(parent__in=controller_bom_ids, item__item_type='C')
        }

        con_inf['con_name'] = con_name
        con_inf['gtr'] = gtr_sen
        con_inf['sta'] = sta_sen
        cont[con_id] = con_inf

        initial_data = {
            'con_id_senid_map': cont,
            'unique_gtr_sen_name': unique_gtr_items,
            'unique_sta_sen_name': unique_sta_items,
        }
        print(initial_data)
        client.close()

        return JsonResponse(initial_data, encoder=DjangoJSONEncoder)

    return JsonResponse({'error': 'Invalid request method'}, status=400)




@csrf_exempt  # You can use this if you're not using CSRF tokens
def sen_list(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        conId = data.get('conId')

        if not conId:
            return JsonResponse({'error': 'conID not provided'}, status=400)

        # uri = "mongodb://localhost:27017/"
        uri = "mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(uri)
        db = client['djangoConnectTest']
        dbSensorGather = db['sen_gather']
        dbSensorGather.create_index([('con_id', 1), ('senid', 1), ('c_date', -1)])

        controller_bom_masters = BomMaster.objects.filter(level=1, parent=conId, delete_flag='N')
        controller_bom_ids = controller_bom_masters.values_list('id', flat=True)
        sensor_bom_masters = BomMaster.objects.filter(parent__in=controller_bom_ids, level=2, delete_flag='N')
        gtr_bom_masters = sensor_bom_masters.filter(item__item_type='L')
        sen_Ids = list(gtr_bom_masters.values_list('id', flat=True))
        unique_gtr_items = list(gtr_bom_masters.values_list('item__item_name', flat=True).distinct())

        initial_data = {
            'senIds': sen_Ids,
            'uniqueGtrItems': unique_gtr_items,
        }
        print(initial_data)
        client.close()

        return JsonResponse(initial_data, encoder=DjangoJSONEncoder)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def fetch_graph_data(request):
    seoul_timezone = pytz.timezone('Asia/Seoul')
    utc_timezone = pytz.utc

    if request.method == 'POST':
        data = json.loads(request.body)
        start_date = isoparse(data['startDate'])
        end_date = isoparse(data['endDate'])
        con_id = int(data['conId'])
        day_index = int(data['dayIndex'])
        sen_Ids = [int(sen_id) for sen_id in data['senIds']]
        print(start_date)
        print(end_date)
        print(con_id)
        print(sen_Ids)

        client = MongoClient('mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
        db = client['djangoConnectTest']
        collection = db['sen_gather']

        group_by = {
            'year': {'$year': '$c_date'},
            'month': {'$month': '$c_date'},
            'day': {'$dayOfMonth': '$c_date'}
        }
        if day_index == 0:
            group_by['hour'] = {'$hour': '$c_date'}

        pipeline = [
            {
                '$match': {
                    'c_date': {'$gte': start_date, '$lt': end_date},
                    'con_id': con_id,
                    'senid': {'$in': sen_Ids}
                }
            },
            {
                '$group': {
                    '_id': group_by,
                    'avgValue': {'$avg': '$value'}
                }
            },
            {
                '$sort': {
                    '_id.year': 1,
                    '_id.month': 1,
                    '_id.day': 1,
                }
            }
        ]

        # Add hour sorting if day_index is 0 (hourly data)
        if day_index == 0:
            pipeline[-1]['$sort']['_id.hour'] = 1

        results = list(collection.aggregate(pipeline))
        formatted_results = []
        for res in results:
            if day_index == 0:
                utc_datetime = datetime(
                    res['_id']['year'],
                    res['_id']['month'],
                    res['_id']['day'],
                    res['_id']['hour']
                ).replace(tzinfo=utc_timezone)
            else:
                utc_datetime = datetime(
                    res['_id']['year'],
                    res['_id']['month'],
                    res['_id']['day']
                ).replace(tzinfo=utc_timezone)
            seoul_datetime = utc_datetime.astimezone(seoul_timezone)
            formatted_results.append({
                'date': seoul_datetime.strftime('%Y-%m-%dT%H:%M:%S%z'),
                'value': res['avgValue']
            })

        print(formatted_results)
        client.close()
        return JsonResponse(formatted_results, safe=False)

    return JsonResponse({'error': 'Invalid request'}, status=400)