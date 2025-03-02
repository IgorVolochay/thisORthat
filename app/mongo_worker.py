import os

import pymongo

from schemas.base_schemas import *
from schemas.api_schemas import *
from typing import Optional

from datetime import datetime
from dotenv import load_dotenv


class MongoWorker:
    def __init__(self):
        load_dotenv()
        self.client = pymongo.MongoClient(host = os.getenv('MONGO_HOST'),
                                          port = int(os.getenv('MONGO_PORT')),
                                          username = os.getenv('MONGO_USER'),
                                          password = os.getenv('MONGO_PASS'),
                                          uuidRepresentation="standard")
        self.db = self.client["data"]
        self.users_data = self.db["users"]
        self.visited_data = self.db["visited"]
        self.counters = self.db["counters"]
        self.game_data = self.db["cards"]


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
    

    def get_and_update_counter(self, counter_name: str) -> int:
        counter = self.counters.find_one_and_update(
            {"counter_name": counter_name},
            {"$inc": {"counter": 1}},
            upsert=True,
            return_document=True)
        return counter["counter"]
    
    
    def get_visited_cards(self, user_id: int) -> BaseResponse:
        document = self.visited_data.find_one({"user_id": user_id})
        if not document:
            check_user = self.check_user(user_id)
            if check_user:
                return BaseResponse(result=Visited(user_id=user_id,
                                                   cards_visited=set()))
            else:
                return BaseResponse(result="User doesn't exist", error=True)
        else:
            return BaseResponse(result=Visited.model_validate(document))
        
    def filter_cards(self, random_cards: list[Card], cards_visited: set) -> tuple[list[Card], list[int]]:
        filtered_cards = [card for card in random_cards if card.card_id not in cards_visited]
        filtered_cards_id = [filtered_card.card_id for filtered_card in filtered_cards]
        
        return filtered_cards, filtered_cards_id
    
    def update_visited_cards(self, user_id: int, visited_card_id: int) -> Visited:
        update_visited = self.visited_data.find_one_and_update({"user_id": user_id},
                                                               {"$addToSet": {"cards_visited": visited_card_id}},
                                                               upsert=True,
                                                               return_document=True)
        return Visited.model_validate(update_visited)


    def add_card(self, choice_A: str, choice_B: str, author_id: int) -> Card:
        new_card = Card(card_id=self.get_and_update_counter(counter_name="card"),
                        choice_A=choice_A,
                        choice_B=choice_B,
                        author_id=author_id,
                        creation_date=datetime.now().isoformat())
        try:
            self.game_data.insert_one(new_card.model_dump())
            return new_card
        except Exception as exception:
            print(exception)
            return new_card
        
    def get_card(self, card_id: int) -> Optional[Card]:
        document = self.game_data.find_one({"card_id": card_id})
        if document:
            return Card.model_validate(document)
        else:
            return None

    def get_random_cards(self, amount: int, active_status: bool) -> Optional[list[Card]]:
        pipeline = [{"$match": {"active_status": active_status}}, 
                    {"$sample": {"size": amount}}]
        raw_items = list(self.game_data.aggregate(pipeline))

        if raw_items:
            validated_items = [Card.model_validate(item) for item in raw_items]
            return validated_items
        else:
            return None
        

    def select_choice(self, card_id: int, choice: str) -> BaseResponse:
        if choice == "A":
            count_choice = "count_choice_A"
        elif choice == "B":
            count_choice = "count_choice_B"
        else:
            return BaseResponse(result="Wrong choice", error=True)
        
        result = self.game_data.find_one_and_update({"card_id": card_id},
                                                    {"$inc": {"count_total": 1, count_choice: 1}})
        
        if not result:
            return BaseResponse(result="Card doesn't exist", error=True)
        else:
            return BaseResponse(result=result, error=False)
    
    def like_card(self, card_id: int, user_id: int) -> BaseResponse:
        update_card_info = self.game_data.find_one_and_update({"card_id": card_id}, 
                                                              {"$inc": {"count_likes": 1}})
        if not update_card_info:
            return BaseResponse(result="Card doesn't exist", error=True)
        else:
            add_card_to_user = self.users_data.update_one({'user_id': user_id},
                                                          {'$push': {'liked_card_ids': card_id}})
            if not add_card_to_user:
                return BaseResponse(result="User doesn't exist", error=True)
            else:
                return BaseResponse(result=True, error=False)
            
    def dislike_card(self, card_id: int, user_id: int) -> BaseResponse:
        update_card_info = self.game_data.find_one_and_update({"card_id": card_id}, 
                                                              {"$inc": {"count_dislikes": 1}})
        if not update_card_info:
            return BaseResponse(result="Card doesn't exist", error=True)
        else:
            add_card_to_user = self.users_data.update_one({'user_id': user_id},
                                                          {'$push': {'disliked_card_ids': card_id}})
            if not add_card_to_user:
                return BaseResponse(result="User doesn't exist", error=True)
            else:
                return BaseResponse(result=True, error=False)


if __name__ == "__main__":
    mongo = MongoWorker()
    #print(mongo.check_user(123))
    #print(mongo.add_user(123, "VolochayIgor", "Igor", "Volochay", "photo_0.jpg"))
    #print(mongo.get_user(123))
    #print(mongo.add_card("A", "B", 123))
    #print(mongo.get_random_cards(10, active_status=False))
    #print(mongo.update_counter("cards_counter"))
    #print(mongo.select_choice(1, "A"))
    #print(mongo.like_card(1, 455412573))
    #print(mongo.dislike_card(1, 455412573))
    print(mongo.update_visited_cards(123, 2))
    print(mongo.get_visited_cards(123).result.cards_visited)
