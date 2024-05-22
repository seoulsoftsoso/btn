from pymongo import MongoClient
uri = "mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri)
db = client['djangoConnectTest']
dbSensorGather = db['sen_gather']
dbSensorStatus = db['sen_status']


unique_senids = dbSensorGather.distinct('senid')