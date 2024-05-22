from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder

# 유저 정보 


def dashboard2(request):
    uri = "mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri)
    db = client['djangoConnectTest']
    dbSensorGather = db['sen_gather']
    dbSensorStatus = db['sen_status']

    unique_gtr_senids = dbSensorGather.distinct('senid')
    unique_sta_senids = dbSensorStatus.distinct('senid')
    unique_gtr_con_ids = dbSensorGather.distinct('con_id')
    unique_sta_con_ids = dbSensorStatus.distinct('con_id')
    unique_val_ids = dbSensorGather.distinct('value')

    # Create a dictionary to store con_id as key and associated senid list as value
    con_id_senid_map = {}
    for con_id in unique_gtr_con_ids:
        senids = dbSensorGather.distinct('senid', {'con_id': con_id})
        senid_grt_value_map = {}
        for senid in senids:
            newest_value = dbSensorGather.find_one({'con_id': con_id, 'senid': senid}, sort=[('c_date', -1)])
            if newest_value:
                senid_grt_value_map[senid] = newest_value['value']
        con_id_senid_map[con_id] = senid_grt_value_map

    for con_id in unique_sta_con_ids:
        senids = dbSensorStatus.distinct('senid', {'con_id': con_id})
        senid_sta_value_map = {}
        for senid in senids:
            newest_value = dbSensorStatus.find_one({'con_id': con_id, 'senid': senid}, sort=[('c_date', -1)])
            if newest_value:
                senid_sta_value_map[senid] =newest_value['status']
        con_id_senid_map.setdefault(con_id, {}).update(senid_sta_value_map)
    initial_data = {
        'unique_gtr_senids': unique_gtr_senids,
        'unique_sta_senids': unique_sta_senids,
        'con_id_senid_map': con_id_senid_map
    }

    initial_data_json = json.dumps(initial_data, cls=DjangoJSONEncoder)

    return render(request, "pages/dashboard2.html", {'initial_data_json': initial_data_json})

