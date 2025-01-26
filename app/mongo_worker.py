import pymongo

class MongoWorker():
    def __init__(self):
        self.client = pymongo.MongoClient(host="127.0.0.1", port=27017)
        self.db = self.client["data"]
        self.collection = self.db["game_data"]

    def get_mongodb_info(self):
        print(self.client.list_database_names())
        print(self.db.list_collection_names())

if __name__ == "__main__":
    mongo = MongoWorker()
    mongo.get_mongodb_info()
