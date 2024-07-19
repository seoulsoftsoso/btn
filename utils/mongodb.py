from random import random

from pymongo import MongoClient
from datetime import datetime
from pytz import timezone
import certifi


DB_NAME = 'djangoConnectTest'
COLLECTION = 'sen_gather'
SERVER_URL = ('mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName'
              '=Cluster0')

mongo = MongoClient(SERVER_URL, tlsCAFile=certifi.where())
db = mongo[DB_NAME]
collection = db[COLLECTION]

if __name__ == "__main__":

    res = collection.insert_one(
        {
            "c_date": datetime.now(timezone('Asia/Seoul')),
            "con_id": 2,
            "senid": 4,
            "type": "gtr",
            "value": int(random() * 30)
        }
    )

    print(res.inserted_id)