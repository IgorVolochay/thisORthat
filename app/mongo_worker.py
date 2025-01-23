import pymongo

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient["data"]
collections = db["game_data"]
print(myclient.list_database_names())
print(db.list_collection_names())