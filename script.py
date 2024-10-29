import os 
import threading
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "button.settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from api.models import Plantation

from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz 
from bson.codec_options import CodecOptions
GATHER = 'sen_gather'
SENSOR = "sen_status"
SERVER_URL = "mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


def get_data():
    conatiners = Plantation.objects.all()
    options = CodecOptions(tz_aware = True, tzinfo = pytz.timezone('Asia/Seoul'))

    client = MongoClient(SERVER_URL)
    for conatiner in conatiners:
        DB_NAME = conatiner.c_code
        try:
            db = client[DB_NAME]
            collection = db.get_collection(GATHER, codec_options=options)

            # 현재 서울 시간 가져오기
            seoul_tz = pytz.timezone('Asia/Seoul')
            seoul_time = datetime.now(seoul_tz).replace(second=0, microsecond=0)

            # 10분 전 시간 계산
            time_10_minutes_ago = seoul_time - timedelta(minutes=10)


            # MongoDB에서 UTC 타임으로 조회
            query = {'c_date': {'$gte': time_10_minutes_ago}}

            # 쿼리 실행
            results = collection.find(query)
            gather_data = {

            }
            if results:
                avg = 0
                pre_sensor_data = []
                for result in results:
                    if result["senid"] not in gather_data:
                        gather_data[result["senid"]] = {
                            'sum': 0,
                            'count': 0
                        }
                    gather_data[result["senid"]]['sum'] += result["value"]
                    gather_data[result["senid"]]['count'] += 1
                for key in gather_data:
                    avg = gather_data[key]['sum'] / gather_data[key]['count']
                    pre_sensor_data.append({
                    "c_date": datetime.now(pytz.timezone('Asia/Seoul')) - timedelta(minutes=1),
                    "con_id": conatiner.id,
                    "senid": key,
                    "type": "gta",
                    "value": avg  # 데이터가 없는 경우를 처리
                })
                collection.insert_many(pre_sensor_data)
                print("Data inserted")
                collection.delete_many(query)
            else:
                print("No data found")
        except Exception as e:
            print(f"Error: {e}")
        try: 
            collection = db.get_collection(SENSOR, codec_options=options)
            query = {'c_date': {'$gte': time_10_minutes_ago}}
            results = collection
            collection.delete_many(query)
        except Exception as e:
            print(f"Error: {e}")
if __name__ == '__main__':
    class CycleThread:
        def __init__(self, cycle_timeout=0):
            self.cycle_timeout = cycle_timeout
            self.isActive = False   
        def run_cycle(self, start_end, execute_rest=None):
            start, end = start_end
            if self.cycle_timeout:
                self.cycle_timeout.cancel()

            self.set_active(not self.isActive)  # 상태 토글
            send_time = end if self.isActive else start

            if not self.isActive:
                get_data()

            print(f"Running cycle: {self.isActive}, Time: {send_time}")
            
            # 주기를 반복하는 타이머 시작
            self.cycle_timeout = threading.Timer(send_time * 60, lambda: self.run_cycle([start, end], execute_rest))
            self.cycle_timeout.start()

        def set_active(self, active):
            self.isActive = active

    cycle_thread = CycleThread()
    cycle_thread.run_cycle([0, 10])

    get_data()