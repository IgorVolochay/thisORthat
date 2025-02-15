import os

import pymongo

from schemas import *

from datetime import datetime
from dotenv import load_dotenv


class MongoWorker:
    def __init__(self):
        load_dotenv()
        self.client = pymongo.MongoClient(host = os.getenv('MONGO_HOST'),
                                          port = int(os.getenv('MONGO_PORT')),
                                          username = os.getenv('MONGO_USER'),
                                          password = os.getenv('MONGO_PASS'))
        self.db = self.client["data"]
        self.users_data = self.db["users_data"]
        self.game_data = self.db["game_data"]

    def get_mongodb_info(self) -> None:
        print(self.client.list_database_names())
        print(self.db.list_collection_names())

    def check_user(self, user_id: int) -> bool:
        if self.users_data.find_one({"user_id": user_id}):
            return True
        else:
            return False

    def add_user(self, user_id: int, username: str, first_name: str, last_name: str, photo_path: str) -> User:
        new_user = User(user_id=user_id,
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                        photo_path=photo_path,
                        registration_date=datetime.now().isoformat())
        try:
            res = self.users_data.insert_one(new_user.model_dump())
            return new_user
        except Exception as exception:
            print(exception)
            return new_user

    def get_user(self, user_id: int) -> User:
        return User.model_validate(self.users_data.find_one({"user_id": user_id}))


if __name__ == "__main__":
    mongo = MongoWorker()
    mongo.get_mongodb_info()
    print(mongo.check_user(123))
    # print(mongo.add_user(123, "VolochayIgor", "Igor", "Volochay", os.path.join("/path/to", "photo.jpg")))
    print(mongo.get_user(123))
