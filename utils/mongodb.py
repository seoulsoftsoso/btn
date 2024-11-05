from random import random

from pymongo import MongoClient
from datetime import datetime
from pytz import timezone
import certifi
import os
from dotenv import load_dotenv


load_dotenv()


mongo_url = os.getenv("MONGO_URL")

DB_NAME = 'djangoConnectTest'
COLLECTION = 'sen_gather'
SERVER_URL = (mongo_url)

mongo = MongoClient(SERVER_URL)
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