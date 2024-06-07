from pymongo import MongoClient
import paho.mqtt.client as mqtt
import certifi

def on_message(client, userdata, msg):
    print(str(msg.payload.decode("utf-8")))

def on_connect(client, userdata, flags, rc):
        try:
            print(f"Connected with result code {rc}")
        except Exception as e:
            print(f"Error connecting to MQTT: {e}")
class MqttServer:
    def __init__(self, mqtt_host='127.0.0.1', mqtt_port=1883, topic='test'):
        self.mongo_client = None
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.db_name = 'djangoConnectTest'
        self.collection = 'sen_gather'
        self.message = None
        self.server_url = ('mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName'
                           '=Cluster0')
        self.server_config = {
            'host': mqtt_host,
            'port': mqtt_port,
            'topic': topic
        }

    def mqtt_config(self):
        self.mqtt_client = self.mqtt_client.d
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = on_message

    def insert(self, data):
        try:
            client = MongoClient(self.server_url, tlsCAFile=certifi.where())
            db = client[self.db_name]
            collection = db[self.collection]
            x = collection.insert_one(data)
            if x.acknowledged:
                self.mqtt_client.publish(self.server_config['topic'], str(data))
        except Exception as e:
            print(f"Error inserting data: {e}")

    def on_mqtt_message(self, data):
        try:
            print(f"Received message: {data}")
            # self.insert(data)
            self.message = data
        except Exception as e:
            print(f"Error handling message: {e}")

    def init_mqtt(self):
        try:
            self.mqtt_client.on_connect = on_connect
            self.mqtt_client.on_message = on_message
            self.mqtt_client.connect(self.server_config['host'], self.server_config['port'])
            self.mqtt_client.loop_start()
        except Exception as e:
            print(f"Error initializing MQTT: {e}")

    def close(self):
        try:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            if self.mongo_client:
                self.mongo_client.close()
        except Exception as e:
            print(f"Error closing connections: {e}")


def on_disconnect(self, client, userdata, rc):
    print(rc)

def on_subscribe(client, userdata, mid, granted_pos):
    print(f'subscribed:{str(mid)}{str(granted_pos)}')


if __name__ == "__main__":
    mqtt_server = MqttServer('127.0.0.1', 1883, 'test')
    mqtt_subscribe = mqtt.Client()
    mqtt_subscribe.connect('127.0.0.1', 1883)
    mqtt_subscribe.on_message = on_message
    mqtt_subscribe.on_connect = on_connect
    mqtt_subscribe.on_disconnect = on_disconnect
    mqtt_subscribe.on_subscribe = on_subscribe
    mqtt_subscribe.subscribe('test', 1)

    mqtt_subscribe.loop_forever()

    mqtt_server.mqtt_config()
    mqtt_server.init_mqtt()

    mqtt_server.on_mqtt_message({
        "c_date": "test",
        "con_id": 35,
        "senid": 41,
        "type": "test",
        "value": 32
    })

    mqtt_server.close()
