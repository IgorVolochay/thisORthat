import os

import pymongo

from schemas.base_schemas import *
from typing import Optional

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


    def check_user(self, user_id: int) -> bool:
        if self.users_data.find_one({"user_id": user_id}):
            return True
        else:
            return False

    def add_user(self, user_id: int, username: str, first_name: str, last_name: str, photo_url: str) -> User:
        new_user = User(user_id=user_id,
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                        photo_url=photo_url,
                        registration_date=datetime.now().isoformat())
        try:
            self.users_data.insert_one(new_user.model_dump())
            return new_user
        except Exception as exception:
            return new_user

    def get_user(self, user_id: int) -> User:
        return User.model_validate(self.users_data.find_one({"user_id": user_id}))
    

    def add_card(self, choice_A: str, choice_B: str, author_id: int) -> Card:
        new_card = Card(choice_A=choice_A,
                        choice_B=choice_B,
                        author_id=author_id,
                        creation_date=datetime.now().isoformat())
        try:
            self.game_data.insert_one(new_card.model_dump(by_alias=True))
            return new_card
        except Exception as exception:
            return new_card
        
    def get_card(self, card_id: ObjectId) -> Optional[Card]:
        document = self.game_data.find_one({"_id": card_id})
        if document:
            return Card.model_validate(document)
        else:
            return None

    def get_random_cards(self, amount: int, active_status: bool) -> Optional[list[Card]]:
        pipeline = [{"$match": {"active_status": active_status}}, 
                    {"$sample": {"size": amount}}]
        raw_items = list(self.game_data.aggregate(pipeline))

        if not raw_items:
            validated_items = [Card.model_validate(item) for item in raw_items]
            return validated_items
        else:
            return None

if __name__ == "__main__":
    mongo = MongoWorker()
    #print(mongo.check_user(123))
    #print(mongo.add_user(123, "VolochayIgor", "Igor", "Volochay", "photo_0.jpg"))
    #print(mongo.get_user(123))
    print(mongo.add_card("A", "B", 123))
    print(mongo.get_random_cards(10, active_status=False))
