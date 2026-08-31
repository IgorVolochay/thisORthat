import os

import motor.motor_asyncio

from datetime import datetime
from dotenv import load_dotenv
from typing import Optional
from pymongo import ReturnDocument

from schemas.base_schemas import User, Visited, Card, Comment
from schemas.api_schemas import BaseResponse
from logger import logger


class MongoWorker:
    def __init__(self):
        load_dotenv()
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            host=os.getenv('MONGO_HOST'),
            port=int(os.getenv('MONGO_PORT', 27017)),
            username=os.getenv('MONGO_USER'),
            password=os.getenv('MONGO_PASS'),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            maxPoolSize=50,
            minPoolSize=5,
            maxIdleTimeMS=60000,
            waitQueueTimeoutMS=5000
        )
        logger.info("MongoDB connection established.")
        self.db = self.client["data"]
        self.users_data = self.db["users"]
        self.visited_data = self.db["visited"]
        self.counters = self.db["counters"]
        self.game_data = self.db["cards"]
        self.comments_data = self.db["comments"]

    async def create_indexes(self) -> None:
        """Creates indexes on application startup."""
        await self.users_data.create_index("user_id", unique=True)
        await self.game_data.create_index("card_id", unique=True)
        await self.game_data.create_index("active_status")
        await self.visited_data.create_index("user_id", unique=True)
        await self.comments_data.create_index("comment_id", unique=True)
        logger.info("MongoDB indexes created.")


    async def check_user(self, user_id: int) -> bool:
        document = await self.users_data.find_one({"user_id": user_id}, {"_id": 1})
        return document is not None

    async def add_user(
        self, user_id: int, username: str, first_name: str, last_name: str, photo_url: str) -> User:
        new_user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            photo_url=photo_url,
            registration_date=datetime.now().isoformat(),
        )
        await self.users_data.insert_one(new_user.model_dump())
        logger.debug("User added: user_id={}, username={}", user_id, username)
        return new_user

    async def get_user(self, user_id: int) -> User:
        document = await self.users_data.find_one({"user_id": user_id})
        return User.model_validate(document)


    async def get_and_update_counter(self, counter_name: str) -> int:
        """Atomically increments the counter and returns the new value."""
        counter = await self.counters.find_one_and_update(
            {"counter_name": counter_name},
            {"$inc": {"counter": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return counter["counter"]


    async def get_visited_cards(self, user_id: int) -> BaseResponse:
        document = await self.visited_data.find_one({"user_id": user_id})
        if not document:
            if await self.check_user(user_id):
                return BaseResponse(result=Visited(user_id=user_id, cards_visited=set()))
            return BaseResponse(result="User doesn't exist", error=True)
        return BaseResponse(result=Visited.model_validate(document))

    async def update_visited_cards(self, user_id: int, visited_card_id: int) -> Visited:
        updated = await self.visited_data.find_one_and_update(
            {"user_id": user_id},
            {"$addToSet": {"cards_visited": visited_card_id}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return Visited.model_validate(updated)

    async def try_mark_visited(self, user_id: int, card_id: int) -> bool:
        """
        Atomically marks a card as visited for the user.

        Returns True if the card was newly marked (was not visited before).
        Returns False if the card was already in the visited set.

        Uses a conditional update filter (cards_visited: {$ne: card_id}) so that
        only one concurrent request can "win" the mark — eliminating the TOCTOU
        race condition between checking and writing.
        """
        result = await self.visited_data.update_one(
            {"user_id": user_id, "cards_visited": {"$ne": card_id}},
            {"$addToSet": {"cards_visited": card_id}},
        )
        if result.modified_count == 1:
            return True

        # No document matched: either the visited doc doesn't exist yet,
        # or the card is already in the set.
        doc = await self.visited_data.find_one({"user_id": user_id}, {"cards_visited": 1})
        if doc is None:
            # First vote ever for this user — create the visited document.
            await self.visited_data.update_one(
                {"user_id": user_id},
                {"$addToSet": {"cards_visited": card_id}},
                upsert=True,
            )
            return True

        # Card is already present in the visited set.
        return False


    async def get_card(self, card_id: int) -> Optional[Card]:
        document = await self.game_data.find_one({"card_id": card_id})
        if document:
            return Card.model_validate(document)
        return None

    async def get_random_cards(self, amount: int,active_status: bool,exclude_ids: Optional[set[int]] = None,) -> Optional[list[Card]]:
        """Returns random cards, excluding already visited ones (in a single query)."""
        match_filter: dict = {"active_status": active_status}
        if exclude_ids:
            match_filter["card_id"] = {"$nin": list(exclude_ids)}

        pipeline = [
            {"$match": match_filter},
            {"$sample": {"size": amount}},
        ]
        raw_items = await self.game_data.aggregate(pipeline).to_list(length=amount)

        if raw_items:
            return [Card.model_validate(item) for item in raw_items]
        return None

    def filter_cards(self, random_cards: list[Card], cards_visited: set) -> tuple[list[Card], list[int]]:
        filtered_cards = [card for card in random_cards if card.card_id not in cards_visited]
        filtered_cards_id = [card.card_id for card in filtered_cards]
        return filtered_cards, filtered_cards_id

    async def add_card_by_api(self, choice_A: str, choice_B: str, author_id: int) -> Card:
        new_card = Card(
            card_id=await self.get_and_update_counter(counter_name="card"),
            choice_A=choice_A,
            choice_B=choice_B,
            author_id=author_id,
            creation_date=datetime.now().isoformat(),
        )
        await self.game_data.insert_one(new_card.model_dump())
        logger.debug("Card created by API: card_id={}, author_id={}", new_card.card_id, author_id)
        return new_card

    async def add_card_by_base_model(self, new_card: Card) -> Optional[Card]:
        new_card.card_id = await self.get_and_update_counter(counter_name="card")
        try:
            await self.game_data.insert_one(new_card.model_dump())
            return new_card
        except Exception as exc:
            logger.error("Failed to insert card: {}", exc)
            raise

    async def accept_card(self, card_id: int) -> BaseResponse:
        """Accepts a card: sets active_status=True and moderation_date=now."""
        result = await self.game_data.find_one_and_update(
            {"card_id": card_id},
            {"$set": {
                "active_status": True,
                "moderation_date": datetime.now().isoformat(),
            }},
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            logger.debug("Attempted to accept non-existent card: card_id={}", card_id)
            return BaseResponse(result="Card doesn't exist", error=True)
        logger.debug("Card accepted: card_id={}", card_id)
        return BaseResponse(result=Card.model_validate(result))

    async def reject_card(self, card_id: int) -> BaseResponse:
        """Rejects a card: deletes it from the database."""
        result = await self.game_data.delete_one({"card_id": card_id})
        if result.deleted_count == 0:
            logger.debug("Attempted to reject non-existent card: card_id={}", card_id)
            return BaseResponse(result="Card doesn't exist", error=True)
        logger.debug("Card rejected and deleted: card_id={}", card_id)
        return BaseResponse(result=f"Card {card_id} rejected and deleted")

    async def select_choice(self, card_id: int, choice: str) -> BaseResponse:
        if choice == "A":
            count_field = "count_choice_A"
        elif choice == "B":
            count_field = "count_choice_B"
        else:
            return BaseResponse(result="Wrong choice", error=True)

        result = await self.game_data.find_one_and_update(
            {"card_id": card_id},
            {"$inc": {"count_total": 1, count_field: 1}},
        )
        if not result:
            return BaseResponse(result="Card doesn't exist", error=True)
        return BaseResponse(result=True, error=False)


    async def like_card(self, card_id: int, user_id: int) -> BaseResponse:
        if not await self.check_user(user_id):
            return BaseResponse(result="User doesn't exist", error=True)

        # Atomically add card_id to liked_card_ids ONLY IF it is not already
        # present in liked_card_ids OR disliked_card_ids.
        # Using a conditional filter makes this a single, race-condition-free
        # test-and-set: if modified_count == 0, another request already won.
        user_update = await self.users_data.find_one_and_update(
            {
                "user_id": user_id,
                "liked_card_ids": {"$ne": card_id},
                "disliked_card_ids": {"$ne": card_id},
            },
            {"$addToSet": {"liked_card_ids": card_id}},
            projection={"_id": 1},
        )
        if not user_update:
            return BaseResponse(result="Card already liked or disliked", error=True)

        updated_card = await self.game_data.find_one_and_update(
            {"card_id": card_id},
            {"$inc": {"count_likes": 1}},
        )
        if not updated_card:
            # Card doesn't exist — roll back the user update (best effort).
            await self.users_data.update_one(
                {"user_id": user_id},
                {"$pull": {"liked_card_ids": card_id}},
            )
            return BaseResponse(result="Card doesn't exist", error=True)

        logger.debug("Card liked: card_id={}, user_id={}", card_id, user_id)
        return BaseResponse(result=True, error=False)

    async def dislike_card(self, card_id: int, user_id: int) -> BaseResponse:
        if not await self.check_user(user_id):
            return BaseResponse(result="User doesn't exist", error=True)

        # Same atomic test-and-set pattern as like_card.
        user_update = await self.users_data.find_one_and_update(
            {
                "user_id": user_id,
                "liked_card_ids": {"$ne": card_id},
                "disliked_card_ids": {"$ne": card_id},
            },
            {"$addToSet": {"disliked_card_ids": card_id}},
            projection={"_id": 1},
        )
        if not user_update:
            return BaseResponse(result="Card already liked or disliked", error=True)

        updated_card = await self.game_data.find_one_and_update(
            {"card_id": card_id},
            {"$inc": {"count_dislikes": 1}},
        )
        if not updated_card:
            # Card doesn't exist — roll back the user update (best effort).
            await self.users_data.update_one(
                {"user_id": user_id},
                {"$pull": {"disliked_card_ids": card_id}},
            )
            return BaseResponse(result="Card doesn't exist", error=True)

        logger.debug("Card disliked: card_id={}, user_id={}", card_id, user_id)
        return BaseResponse(result=True, error=False)


    async def add_comment(self, user_id: int, card_id: int, comment_text: str) -> BaseResponse:
        if not await self.check_user(user_id):
            return BaseResponse(result="User doesn't exist", error=True)
        if not await self.get_card(card_id):
            return BaseResponse(result="Card doesn't exist", error=True)

        new_comment = Comment(
            comment_id=await self.get_and_update_counter(counter_name="comment"),
            author_id=user_id,
            card_id=card_id,
            comment_text=comment_text,
            creation_date=datetime.now().isoformat(),
        )
        await self.comments_data.insert_one(new_comment.model_dump())

        updated_user = await self.users_data.find_one_and_update(
            {"user_id": user_id},
            {"$addToSet": {"comments_ids": new_comment.comment_id}},
            return_document=ReturnDocument.AFTER,
        )
        if not updated_user:
            return BaseResponse(result="Difficulty adding comment_id to user", error=True)

        logger.debug("Comment added: comment_id={}, card_id={}, author_id={}", new_comment.comment_id, card_id, user_id)
        return BaseResponse(result=new_comment)

    async def get_comments(self, card_id: int) -> BaseResponse:
        if not await self.get_card(card_id):
            return BaseResponse(result="Card doesn't exist", error=True)
        comments = await self.comments_data.find({"card_id": card_id}).sort("creation_date", -1).to_list(length=None)
        comments = [Comment.model_validate(comment) for comment in comments]
        return BaseResponse(result=comments)