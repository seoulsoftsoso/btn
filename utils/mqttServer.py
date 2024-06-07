from datetime import datetime

import certifi
import paho.mqtt.client as mqtt
from pymongo import MongoClient
from pytz import timezone

DB_NAME = 'djangoConnectTest'
COLLECTION = 'sen_gather'
SERVER_URL = ('mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName'
              '=Cluster0')

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
    data = str(msg.payload.decode("utf-8"))
    if data == 'hello':
        print('mqttServer: hello')
        mongo = MongoClient(SERVER_URL, tlsCAFile=certifi.where())
        db = mongo[DB_NAME]
        collection = db[COLLECTION]
        res = collection.insert_one({
            "c_date": datetime.now(timezone('Asia/Seoul')),
            "con_id": 35,
            "senid": 41,
            "type": "gta",
            "value": 90
        })
        if res.acknowledged:
            client.publish('test', 'ack')
        else:
            client.publish('test', 'nack')
        mongo.close()
    else:
        print('mqttServer: ' + data)

def on_publish(client, userdata, mid):
    print("In on_pub callback mid= ", mid)

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.on_publish = on_publish
    client.connect('127.0.0.1', 1883)
    client.subscribe('test', 1)
    client.publish('test', 'hello')
    client.loop_forever()


