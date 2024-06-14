import paho.mqtt.client as mqtt
from datetime import datetime
import json
import time

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

def on_disconnect(client, userdata, rc):
    print(f"Disconnected with result code {rc}")

def on_subscribe(client, userdata, mid, granted_qos):
    print(f"Subscribed to {mid} with QoS {granted_qos}")

def on_message(client, userdata, msg):
    print(f"Received message {msg.payload} on topic {msg.topic} with QoS {msg.qos}")

mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect
mqttc.on_subscribe = on_subscribe
mqttc.on_message = on_message
mqttc.connect("118.44.218.236", 11883)
mqttc.subscribe('btn/con/a-777')
mqttc.publish('btn/con/a-777', '{"type":"gtr", "value": 0, "name": "a-004"}')

interval = 10

try:
    while True:
        import random
        time.sleep(interval)
        ran = random.random() * 100
        mqttc.publish('btn/con/a-777', '{"type":"gtr", "value":' + str(ran) + ', "name": "a-004"}', qos=1)
        print(f"hello this mqtt test {interval}")

except KeyboardInterrupt:
    pass

mqttc.loop_forever()
