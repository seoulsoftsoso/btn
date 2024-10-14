# myapp/tasks.py
from pymongo import MongoClient
from datetime import datetime, timedelta

# MongoDB 클라이언트 연결
uri = "mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client['djangoConnectTest']
sen_gather_collection = db['sen_gather']


def aggregate_data():
    # 현재 시간을 기준으로 10분 전까지의 데이터를 그룹화 (필요에 따라 타임존 조정)
    current_time = datetime.utcnow().replace(second=0, microsecond=0)

    # 호출 시점이 00분, 10분, 20분일 때 직전 10분을 계산
    # 종료 시간을 현재 시간으로 설정하고, 시작 시간을 10분 전으로 설정
    end_time = current_time
    start_time = end_time - timedelta(minutes=10)


    c_date = start_time + timedelta(minutes=5)

    # 10분마다 그룹화하여 평균값 계산
    pipeline = [
        {
            '$match': {
                'c_date': {
                    '$gte': start_time,
                    '$lt': end_time
                }
            }
        },
        {
            '$group': {
                '_id': {
                    'senid': '$senid',  # senid별로 그룹화
                    'con_id': '$con_id',  # con_id별로 그룹화
                    'type': '$type'  # type별로 그룹화
                },
                'average_value': {'$avg': '$value'}  # 각 그룹의 value 평균 계산
            }
        }
    ]

    # Aggregation 실행
    results = list(sen_gather_collection.aggregate(pipeline))

    for result in results:
        senid = result['_id']['senid']
        con_id = result['_id']['con_id']
        type_value = result['_id']['type']
        average_value = result['average_value']

        # Aggregated 데이터를 같은 컬렉션에 저장 (c_date 및 senid 필드 추가)
        sen_gather_collection.insert_one({
            'senid': senid,
            'con_id': con_id,
            'type': type_value,
            'value': average_value,  # value를 평균값으로 대체
            'c_date': c_date  # 중앙 시간 설정
        })

        print(
            f"Aggregated data inserted for senid: {senid}, con_id: {con_id}, type: {type_value}, time range: {start_time} - {end_time}")

