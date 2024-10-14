from django.http import JsonResponse
from api.models import BomMaster, ItemMaster, OrderProduct, OrderMaster
import json
from pymongo import MongoClient, ASCENDING, DESCENDING
from dateutil.parser import isoparse
import pytz

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Subquery
import json
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta


def user_table_data(request):
    uri = "mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri)
    db = client['djangoConnectTest']
    dbSensorGather = db['sen_gather']
    dbSensorStatus = db['sen_status']
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

        controller_ids = controller_bom_masters.filter(parent=con_id).values_list('id', flat=True)
        lv2_gtr_ids = gtr_bom_masters.filter(parent__in=controller_ids).values_list('id', flat=True)
        lv2_sta_ids = sta_bom_masters.filter(parent__in=controller_ids).values_list('id', flat=True)
        gtr_sensor_data = list(dbSensorGather.find(
            {'con_id': con_id, 'senid': {'$in': list(lv2_gtr_ids)}},
            sort=[('c_date', DESCENDING)]
        ).limit(lv2_gtr_ids.count()))
        sta_sensor_data = list(dbSensorStatus.find(
            {'con_id': con_id, 'senid': {'$in': list(lv2_sta_ids)}},
            sort=[('c_date', DESCENDING)]
        ).limit(lv2_sta_ids.count()))

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

    initial_data = {
        'unique_gtr_sen_name': unique_gtr_items,
        'unique_sta_sen_name': unique_sta_items,
        'con_id_senid_map': cont
    }
    return JsonResponse(initial_data, encoder=DjangoJSONEncoder)

def fetch_data(request):
    seoul_timezone = pytz.timezone('Asia/Seoul')
    utc_timezone = pytz.utc

    if request.method == 'POST':
        data = json.loads(request.body)
        start_date = isoparse(data['startDate'])
        end_date = isoparse(data['endDate'])
        con_id = int(data['conId'])
        sen_Ids = [int(sen_id) for sen_id in data['senIds']]
        print(start_date)
        print(end_date)
        print(con_id)
        print(sen_Ids)

        client = MongoClient('mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
        db = client['djangoConnectTest']
        collection = db['sen_gather']

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
                    '_id': {
                        'year': {'$year': '$c_date'},
                        'month': {'$month': '$c_date'},
                        'day': {'$dayOfMonth': '$c_date'},
                        'hour': {'$hour': '$c_date'}
                    },
                    'avgValue': {'$avg': '$value'}
                }
            },
            {
                '$sort': {
                    '_id.year': 1, '_id.month': 1, '_id.day': 1, '_id.hour': 1
                }
            }
        ]
        results = list(collection.aggregate(pipeline))
        formatted_results = []
        for res in results:
            utc_datetime = datetime(
                res['_id']['year'],
                res['_id']['month'],
                res['_id']['day'],
                res['_id']['hour']
            ).replace(tzinfo=utc_timezone)
            seoul_datetime = utc_datetime.astimezone(seoul_timezone)
            formatted_results.append({
                'date': seoul_datetime.strftime('%Y-%m-%dT%H:%M:%S%z'),
                'value': res['avgValue']
            })

        print(formatted_results)
        client.close()
        return JsonResponse(formatted_results, safe=False)

    return JsonResponse({'error': 'Invalid request'}, status=400)from django.http import JsonResponse
from api.models import BomMaster, ItemMaster, OrderProduct, OrderMaster
import json
from pymongo import MongoClient, ASCENDING, DESCENDING
from dateutil.parser import isoparse
import pytz

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Subquery
import json
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta


def user_table_data(request):
    uri = "mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri)
    db = client['djangoConnectTest']
    dbSensorGather = db['sen_gather']
    dbSensorStatus = db['sen_status']
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

        controller_ids = controller_bom_masters.filter(parent=con_id).values_list('id', flat=True)
        lv2_gtr_ids = gtr_bom_masters.filter(parent__in=controller_ids).values_list('id', flat=True)
        lv2_sta_ids = sta_bom_masters.filter(parent__in=controller_ids).values_list('id', flat=True)
        gtr_sensor_data = list(dbSensorGather.find(
            {'con_id': con_id, 'senid': {'$in': list(lv2_gtr_ids)}},
            sort=[('c_date', DESCENDING)]
        ).limit(lv2_gtr_ids.count()))
        sta_sensor_data = list(dbSensorStatus.find(
            {'con_id': con_id, 'senid': {'$in': list(lv2_sta_ids)}},
            sort=[('c_date', DESCENDING)]
        ).limit(lv2_sta_ids.count()))

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

    initial_data = {
        'unique_gtr_sen_name': unique_gtr_items,
        'unique_sta_sen_name': unique_sta_items,
        'con_id_senid_map': cont
    }
    return JsonResponse(initial_data, encoder=DjangoJSONEncoder)

def fetch_data(request):
    seoul_timezone = pytz.timezone('Asia/Seoul')
    utc_timezone = pytz.utc

    if request.method == 'POST':
        data = json.loads(request.body)
        start_date = isoparse(data['startDate'])
        end_date = isoparse(data['endDate'])
        con_id = int(data['conId'])
        sen_Ids = [int(sen_id) for sen_id in data['senIds']]
        print(start_date)
        print(end_date)
        print(con_id)
        print(sen_Ids)

        client = MongoClient('mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
        db = client['djangoConnectTest']
        collection = db['sen_gather']

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
                    '_id': {
                        'year': {'$year': '$c_date'},
                        'month': {'$month': '$c_date'},
                        'day': {'$dayOfMonth': '$c_date'},
                        'hour': {'$hour': '$c_date'}
                    },
                    'avgValue': {'$avg': '$value'}
                }
            },
            {
                '$sort': {
                    '_id.year': 1, '_id.month': 1, '_id.day': 1, '_id.hour': 1
                }
            }
        ]
        results = list(collection.aggregate(pipeline))
        formatted_results = []
        for res in results:
            utc_datetime = datetime(
                res['_id']['year'],
                res['_id']['month'],
                res['_id']['day'],
                res['_id']['hour']
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