import ast
import time
import threading
from datetime import datetime, timedelta
import os 
import requests
from django.db import connection
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "button.settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from api.models import SenControl, Plantation, BomMaster

class Relay:
    def __init__(self):
        self.cycle_timeout = None
        self.my_timeout = None
        self.isActive = False
        self.lock = threading.Lock()  # 스레드 동기화용 Lock 추가

    def set_active(self, state):
        with self.lock:  # Lock을 사용하여 상태 전환 시 동기화
            self.isActive = state

    def cancel_timer(self, timer):
        if timer:
            timer.cancel()
    def start_timer(self, timeout, callback):
        self.cancel_timer(self.my_timeout)
        self.my_timeout = threading.Timer(timeout, callback)
        self.my_timeout.start()
    def calculate_remaining_time(self, target_time):
        """현재 시간과 목표 시간의 차이를 초 단위로 계산"""
        now = datetime.now()
        one_day = timedelta(days=1)
        if now < target_time:
            return (target_time - now).total_seconds()
        return (target_time - now + one_day).total_seconds()
    
    def run_cycle(self, start_end, execute_rest=None):
        start, end = start_end
        if self.cycle_timeout:
            self.cycle_timeout.cancel()

        self.set_active(not self.isActive)  # 상태 토글
        send_time = end if self.isActive else start

        print(f"Running cycle: {self.isActive}, Time: {send_time}")
        
        # 주기를 반복하는 타이머 시작
        self.cycle_timeout = threading.Timer(send_time, lambda: self.run_cycle([start, end], execute_rest))
        self.cycle_timeout.start()

    def run_schedule(self, start_time, end_time, execute_rest=None):
        today = datetime.now()

        if not start_time and not end_time:
            self.cancel_timer(self.my_timeout)
            self.cancel_timer(self.cycle_timeout)
            self.set_active(False)
            print("Schedule ended")
            return

        start_dt = datetime(today.year, today.month, today.day, *map(int, [start_time[:2], start_time[2:4], start_time[4:6]])) if start_time else today
        end_dt = datetime(today.year, today.month, today.day, *map(int, [end_time[:2], end_time[2:4], end_time[4:6]])) if end_time else today

        remaining_time = self.calculate_remaining_time(start_dt if not self.isActive else end_dt)
        print(f"Remaining time: {remaining_time}")

        # 타이머 시작
        self.set_active(not self.isActive)
        self.start_timer(remaining_time, lambda: self.run_schedule('', end_time if not self.isActive else '', execute_rest))

    def run_schedule_cycle(self, start_end, execute_rest):
        start_time, end_time = start_end
        today = datetime.now()

        # 예약 종료 시 처리
        if not start_time and not end_time:
            self.cancel_timer(self.my_timeout)
            self.cancel_timer(self.cycle_timeout)
            self.set_active(False)
            print("Schedule and cycle ended.")
            return

        # 시작 시간과 종료 시간 설정
        start_dt = datetime(today.year, today.month, today.day, *map(int, [start_time[:2], start_time[2:4], start_time[4:6]])) if start_time else today
        end_dt = datetime(today.year, today.month, today.day, *map(int, [end_time[:2], end_time[2:4], end_time[4:6]])) if end_time else today

        if not self.isActive:
            remaining_time = self.calculate_remaining_time(start_dt)
            print(f"Waiting to start cycle. Remaining time: {remaining_time}s")
            self.set_active(True)
            self.start_timer(remaining_time, lambda: self.run_schedule_cycle(['', end_time], execute_rest))
        else:
            remaining_time = self.calculate_remaining_time(end_dt)
            print(f"Cycle active. Waiting for end time. Remaining time: {remaining_time}s")

            # 주기적 실행 시작
            self.run_cycle(execute_rest)
            self.set_active(False)
            self.start_timer(remaining_time, lambda: self.run_schedule_cycle(['', ''], execute_rest))

class Relay_control:
    def __init__(self):
        self.relays = [Relay() for _ in range(15)]
        self.lock = threading.Lock()

    def start_relay(self, relay_idx, start, end):
        with self.lock:
            self.relays[relay_idx].run_cycle([start, end])

    def start_schedule(self, relay_idx, start_time, end_time):
        with self.lock:
            self.relays[relay_idx].run_schedule(start_time, end_time)

    def start_schedule_cycle(self, relay_idx, start_time, end_time, execute_time, rest_time):
        with self.lock:
            self.relays[relay_idx].run_schedule_cycle([start_time, end_time], [execute_time, rest_time])
    
    def control_power(self, relay_idx, power):
        with self.lock:
            self.relays[relay_idx].set_active(power)

Relays = []

try:
    plantaion = Plantation.objects.filter(test_flag="Y")

    for plant in plantaion:
        sensor_control = BomMaster.objects.filter(parent__parent_id=plant.bom.id)
        relay_on_conatiner = sensor_control.filter(item__item_type="C")
        gather_on_sensor = sensor_control.filter(item__item_type="L")
        Relays.append({
            "relay": Relay_control(),
            "container": plant.bom.part_code,
        })
    print(Relays)
    while True:
        for relay_dict in Relays:
            relay = relay_dict['relay']
            container = relay_dict['container']
            for control in SenControl.objects.filter(relay__container__c_code=container, delete_flag="N"):
                key = control.relay.key - 1
                val = ast.literal_eval(control.value)
                print(f"Relay {key} started")
                if control.mode == 'RSV_CYC':
                    print(str(val[0]) + "00", str(val[1]) + "00", val[2], val[3])
                    relay.start_schedule_cycle(key, str(val[0]) + "00", str(val[1]) + "00", val[2], val[3])
                elif control.mode == 'RSV':
                    relay.start_schedule(key, str(val[0]) + "00", str(val[1]) + "00")
                elif control.mode == "CYC":
                    if(val[0] == 0 and val[1] == 0):
                        relay.control_power(key, False)
                    else:
                        relay.start_relay(key,val[0], val[1])
                elif control.mode == "CTR_VAL":
                    relay.control_power(key, False if val == 0 else True)
                control.delete_flag = "Y"
                control.save()
                # Define the URL and payload for the POST request
            url = "http://118.44.218.236:6001/api/bom/sen_control/"
            active = [r.isActive for r in relay.relays]
            payload = {
                    "container": container,
                    "EC": 0,
                    "PH": 10,
                    "CO2": 100, 
                    "LUX": 1000,
                    "TEMP": 10.0, 
                    "HUMI": 00,
                    "TIME": "002020",
                    "RELAY": active
            }
            print(active)
            try:
                response = requests.post(url, json=payload)
                if response.status_code == 200:
                    print("Status successfully sent to server.")
                else:
                    print(f"Failed to send status. Server responded with status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"An error occurred while sending the request: {e}")
            print([r.isActive for r in relay.relays])
            time.sleep(5)
except KeyboardInterrupt:
    for relay in Relays:
        for r in relay.relays:
            r.cancel_timer(r.my_timeout)
            r.cancel_timer(r.cycle_timeout)
    print("Program exited.")