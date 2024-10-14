# button/scheduling/cron.py
from django_cron import CronJobBase, Schedule
from .mongo_task import aggregate_data
from datetime import datetime

class AggregateDataCronJob(CronJobBase):
    RUN_EVERY_MINS = 1  # 1분마다 실행하여 시간을 체크

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'myapp.aggregate_data_cron_job'  # 고유 식별자

    def do(self):
        # 현재 시간을 가져옴
        current_time = datetime.now()
        print(f"Data time check executed at: {current_time}")

        # 현재 시간이 정각 또는 10분 단위인지 확인 (분이 0, 10, 20, 30, 40, 50일 때)
        if current_time.minute % 10 == 0:
            aggregate_data()  # 데이터를 처리하는 함수 호출
            print(f"Data aggregation executed at: {current_time}")