import json
import os
from datetime import datetime

import certifi
import django
import paho.mqtt.client as mqtt
from pymongo import MongoClient
from pytz import timezone
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'button.settings')
django.setup()

# Signal

from api.models import Plantation, PlanPart

DB_NAME = 'djangoConnectTest'
COLLECTION = 'sen_gather'
SERVER_URL = ('mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName'
              '=Cluster0')
MQTT_TOPIC = [('btn/init', 1)]

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("connected OK")
    else:
        print("Bad connection Returned code=", rc)


def on_disconnect(client, userdata, flags, rc=0):
    print(str(rc))

def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed: " + str(mid) + " " + str(granted_qos))

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload)
        topic = msg.topic
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
        client.publish('btn/init', '{"result": "err", "msg": "Invalid JSON"}', qos=1)
        return
    try:
        req_type = data['type']
    except KeyError:
        return
    print(f"Received message '{data}' on topic '{topic}' with QoS {msg.qos}")
    if req_type == 'reg_con':
        try:
            container_sn = data['sn']
        except KeyError:
            client.publish('btn/init', '{"result": "err", "msg": "sn is not exist"}', qos=1)
            return
        try:
            plantation = Plantation.objects.get(c_code=container_sn)
        except Plantation.DoesNotExist:
            client.publish('btn/init', '{"result": "fail", "msg": "No such container"}', qos=1)
            return
        if plantation.reg_flag == 'Y':
            client.publish('btn/init', '{"result": "fail", "msg": "Container is already registered"}', qos=1)
            client.publish(f'{topic}',
                           '{"result": "fail", "msg": "Container is already registered"}', qos=1)
            return
        plantation.reg_flag = 'Y'
        plantation.save()
        client.publish("btn/init", f'{{"result": "ok", "sn": "{container_sn}"}}', qos=1)
        client.publish(topic, '{"result": "ok", "msg": "Container is registered"}', qos=1)
        return
    # btn/con/{conatiner_name}
    if req_type == 'reg_sen':
        try:
            name = data['name']
        except:
            client.publish('btn/init', '{"result": "err", "msg": "sensor name is not exist"}', qos=1)
            return
        try:
            planPart = PlanPart.objects.get(p_name=name)
        except PlanPart.DoesNotExist:
            client.publish('btn/init', '{"result": "err", "msg": "sensor name is not exist"}', qos=1)
            return
        if planPart.reg_flag == 'Y':
            client.publish(topic, '{"result": "fail", "msg": "Sensor {name} is already registered"}', qos=1)
            client.publish(f'topic', '{"result": "fail", "msg": "Sensor {name} is already registered"}', qos=1)
            return
        planPart.reg_flag = 'Y'
        planPart.save()
        client.publish(topic, '{"result": "ok", "name": "{name}", "senid": "{planPart.id}"}', qos=1)
    if req_type == 'gtr':
        try:
            planPart = PlanPart.objects.get(p_name=data['name'])
        except PlanPart.DoesNotExist:
            client.publish(topic, '{"result": "err", "msg": "sensor name is not exist"}', qos=1)
            return
        if planPart.reg_flag == 'N':
            client.publish(topic, '{"result": "fail", "msg": "Sensor {name} is not registered"}', qos=1)
            return
        mongo = MongoClient(SERVER_URL, tlsCAFile=certifi.where())
        db = mongo[DB_NAME]
        collection = db[COLLECTION]
        raw_bom = planPart.part
        try:
            con_id = Plantation.objects.get(c_code=topic.split('/')[-1]).bom_id
        except Plantation.DoesNotExist:
            client.publish(topic, '{"result": "err", "msg": "this container not exist"}', qos=1)
            return
        res = collection.insert_one({
            "c_date": datetime.now(timezone('Asia/Seoul')),
            "con_id": con_id,
            "senid": raw_bom.id,
            "type": "gta",
            "value": data['value']
        })
        if res.acknowledged:
            client.publish(topic, '{"result": "ok", "msg": "gathering is proceed"}', qos=2)
            return
        else:
            client.publish(topic, '{"result": "err", "msg": "gathering is failed"}', qos=2)
            return


def on_publish(client, userdata, mid):
    print("In on_pub callback mid= ", mid)

if __name__ == "__main__":
    container_list = Plantation.objects.filter()
    for container in container_list:
        MQTT_TOPIC.append(('btn/con/' + str(container.c_code), 1))
    client = mqtt.Client()
    print(MQTT_TOPIC)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.on_publish = on_publish
    client.connect('118.44.218.236', 11883)
    client.subscribe(MQTT_TOPIC)
    client.loop_forever()


