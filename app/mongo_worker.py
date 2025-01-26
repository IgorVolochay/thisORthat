import pymongo

from datetime import datetime


class MongoWorker():
    def __init__(self):
        self.client = pymongo.MongoClient(host="127.0.0.1", port=27017)
        self.db = self.client["data"]
        self.users_data = self.db["users_data"]
        self.game_data = self.db["game_data"]

    def get_mongodb_info(self) -> None:
        print(self.client.list_database_names())
        print(self.db.list_collection_names())

    def find_user(self, user_id:int) -> None:
        result = self.users_data.find_one({"user_id": user_id})
        return result

    def add_user(self, user_id:int, username:str, first_name:str, last_name:str, photo_path:str) -> bool:
        try:
            self.users_data.insert_one({"user_id": user_id,
                                        "username": username,
                                        "first_name": first_name,
                                        "last_name": last_name,
                                        "photo_path": photo_path,
                                        "activity": 0,
                                        "liked_post_ids": [],
                                        "disliked_post_ids": [],
                                        "comments_ids": [],
                                        "registration_date": datetime.now().isoformat()
                                        })
            return True
        except Exception as exception:
            print(exception)
            return False


if __name__ == "__main__":
    mongo = MongoWorker()
    mongo.get_mongodb_info()
    print(mongo.add_user(123, "VolochayIgor", "Igor", "Volochay", "path/to/img"))
    print(mongo.find_user(123))