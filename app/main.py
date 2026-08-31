import os
import secrets

import uvicorn
import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Response, Header, HTTPException, status
from guard import SecurityMiddleware, SecurityConfig, SecurityDecorator

from typing import Optional

from schemas.api_schemas import BaseResponse, AddUserBody, AddCardBody, SelectChoice, ReactionCard, AddCommentBody
from schemas.base_schemas import Card
from mongo_worker import MongoWorker
from rabbit_worker import RabbitWorker
from tools.base_moderation import moderate_text
from logger import logger, setup_logging
from middleware import RequestLoggingMiddleware
from tg_auth import get_current_user_id, DEV_MODE


setup_logging()
load_dotenv()

app: FastAPI = FastAPI(
    title="This OR That",
    summary="OpenAPI schema for \"This OR That\" project!",
    version="0.1",
    contact={"GitHub": "https://github.com/IgorVolochay/thisORthat"},
    docs_url="/docs" if DEV_MODE else None,
    redoc_url="/redoc" if DEV_MODE else None,
    openapi_url="/openapi.json" if DEV_MODE else None,
)
config = SecurityConfig(
    enable_rate_limiting=True,
    rate_limit=10, # TODO: check rate limits in real usage
    rate_limit_window=3, # TODO: check rate limits in real usage
    enable_redis=False,
    enable_ip_banning=True,

    enable_penetration_detection=True,
    auto_ban_threshold=3, 
    auto_ban_duration=3600, 

    detection_compiler_timeout=2.0, 
    detection_max_content_length=10000, 
    detection_preserve_attack_patterns=True, 
    detection_semantic_threshold=0.7,

    detection_anomaly_threshold=3.0,
    detection_slow_pattern_threshold=0.1, 
    detection_monitor_history_size=1000, 
    detection_max_tracked_patterns=1000,  
)
guard_deco = SecurityDecorator(config)

_security_middleware = SecurityMiddleware(app.router, config=config)
app.add_middleware(SecurityMiddleware, config=config)
app.add_middleware(RequestLoggingMiddleware)
app.state.guard_decorator = guard_deco
app.state._security_middleware = _security_middleware
mongo_worker = MongoWorker()
_rabbit_worker: Optional[RabbitWorker] = None


def get_rabbit_worker() -> RabbitWorker:
    global _rabbit_worker
    if _rabbit_worker is None:
        _rabbit_worker = RabbitWorker()
    return _rabbit_worker

MODERATION_SECRET = os.getenv("MODERATION_SECRET", "change-me-in-production")


async def verify_moderation_secret(
    x_moderation_secret: str = Header(..., alias="X-Moderation-Secret"),
) -> str:
    if not secrets.compare_digest(x_moderation_secret, MODERATION_SECRET):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid moderation secret",
        )
    return x_moderation_secret


@app.on_event("startup")
async def startup_event():
    await mongo_worker.create_indexes()
    if DEV_MODE:
        logger.warning("⚠️ DEV_MODE is enabled — docs are exposed and Telegram initData auth is DISABLED")
    logger.info("Application started on :5000")


@app.get("/check_user", status_code=200)
async def check_user(
    user_id: int,
    mongo: MongoWorker = Depends(lambda: mongo_worker),) -> BaseResponse:
    result = await mongo.check_user(user_id)
    return BaseResponse(result=result)

@app.get("/get_user", status_code=200)
async def get_user(
    user_id: int,
    response: Response,
    mongo: MongoWorker = Depends(lambda: mongo_worker),) -> BaseResponse:
    if await mongo.check_user(user_id):
        result = await mongo.get_user(user_id)
        return BaseResponse(result=result)
    response.status_code = status.HTTP_404_NOT_FOUND
    return BaseResponse(result="User doesn't exist", error=True)

@app.post("/add_user", status_code=201)
@guard_deco.rate_limit(requests=3, window=60)
async def add_user(
    new_user: AddUserBody,
    response: Response,
    auth_user_id: Optional[int] = Depends(get_current_user_id),
    mongo: MongoWorker = Depends(lambda: mongo_worker),) -> BaseResponse:
    user_id = auth_user_id if auth_user_id is not None else new_user.user_id
    if user_id is None:
        raise HTTPException(status_code=422, detail="user_id is required")
    if not await mongo.check_user(user_id):
        result = await mongo.add_user(
            user_id,
            new_user.username,
            new_user.first_name,
            new_user.last_name,
            new_user.photo_url,
        )
        return BaseResponse(result=result)
    response.status_code = status.HTTP_409_CONFLICT
    return BaseResponse(result="User already exist", error=True)


@app.get("/get_card", status_code=200)
async def get_card(
    card_id: int,
    response: Response,
    mongo: MongoWorker = Depends(lambda: mongo_worker),) -> BaseResponse:
    card = await mongo.get_card(card_id)
    if card:
        return BaseResponse(result=card)
    response.status_code = status.HTTP_404_NOT_FOUND
    return BaseResponse(result="There is no card with this card_id", error=True)

@app.get("/get_random_cards", status_code=200)
@guard_deco.rate_limit(requests=5, window=60)
async def get_random_cards(
    response: Response,
    user_id: Optional[int] = None,
    auth_user_id: Optional[int] = Depends(get_current_user_id),
    mongo: MongoWorker = Depends(lambda: mongo_worker),) -> BaseResponse:
    resolved_user_id = auth_user_id if auth_user_id is not None else user_id
    if resolved_user_id is None:
        raise HTTPException(status_code=422, detail="user_id is required")
    cards_visited = await mongo.get_visited_cards(resolved_user_id)

    if cards_visited.error:
        response.status_code = status.HTTP_404_NOT_FOUND
        return cards_visited
    exclude_ids = cards_visited.result.cards_visited or None
    random_cards = await mongo.get_random_cards(10, True, exclude_ids=exclude_ids)

    if not random_cards:
        response.status_code = status.HTTP_404_NOT_FOUND
        return BaseResponse(result="No active cards for this user", error=True)

    return BaseResponse(result=random_cards)

@app.post("/add_card", status_code=201)
@guard_deco.rate_limit(requests=3, window=60)
async def add_card(
    new_card: AddCardBody,
    response: Response,
    auth_user_id: Optional[int] = Depends(get_current_user_id),
    mongo: MongoWorker = Depends(lambda: mongo_worker),) -> BaseResponse:
    author_id = auth_user_id if auth_user_id is not None else new_card.author_id
    if author_id is None:
        raise HTTPException(status_code=422, detail="author_id is required")
    if moderate_text(new_card.choice_A) and moderate_text(new_card.choice_B):
        card = await mongo.add_card_by_api(new_card.choice_A, new_card.choice_B, author_id)
        try:
            await get_rabbit_worker().send_to_moderation(card)
        except Exception as exc:
            logger.error("Failed to send card {} to moderation queue: {}", card.card_id, exc)

        return BaseResponse(result=card)
    response.status_code = status.HTTP_400_BAD_REQUEST
    return BaseResponse(result="Card has not passed base moderation", error=True)

@app.patch("/card_accept", status_code=200, dependencies=[Depends(verify_moderation_secret)])
async def card_accept(
    card_id: int,
    response: Response,
    mongo: MongoWorker = Depends(lambda: mongo_worker),) -> BaseResponse:
    result = await mongo.accept_card(card_id)
    if result.error:
        response.status_code = status.HTTP_404_NOT_FOUND
    return result

@app.patch("/card_reject", status_code=200, dependencies=[Depends(verify_moderation_secret)])
async def card_reject(
    card_id: int,
    response: Response,
    mongo: MongoWorker = Depends(lambda: mongo_worker),) -> BaseResponse:
    result = await mongo.reject_card(card_id)
    if result.error:
        response.status_code = status.HTTP_404_NOT_FOUND
    return result

@app.patch("/select_choice", status_code=200)
async def select_choice(
    choice_data: SelectChoice,
    response: Response,
    auth_user_id: Optional[int] = Depends(get_current_user_id),
    mongo: MongoWorker = Depends(lambda: mongo_worker),) -> BaseResponse:
    user_id = auth_user_id if auth_user_id is not None else choice_data.user_id
    if user_id is None:
        raise HTTPException(status_code=422, detail="user_id is required")
    # Verify that the user exists before proceeding.
    if not await mongo.check_user(user_id):
        response.status_code = status.HTTP_404_NOT_FOUND
        return BaseResponse(result="User doesn't exist", error=True)

    # Atomically mark the card as visited.
    newly_visited = await mongo.try_mark_visited(user_id, choice_data.card_id)
    if not newly_visited:
        response.status_code = status.HTTP_403_FORBIDDEN
        return BaseResponse(result="Card already visited!", error=True)

    select_choice_result = await mongo.select_choice(choice_data.card_id, choice_data.choice)
    if select_choice_result.error:
        response.status_code = status.HTTP_404_NOT_FOUND
        return select_choice_result

    return BaseResponse(result="Select choice complete!")


@app.patch("/like_card", status_code=200)
async def like_card(
    like_data: ReactionCard,
    response: Response,
    auth_user_id: Optional[int] = Depends(get_current_user_id),
    mongo: MongoWorker = Depends(lambda: mongo_worker),) -> BaseResponse:
    user_id = auth_user_id if auth_user_id is not None else like_data.user_id
    if user_id is None:
        raise HTTPException(status_code=422, detail="user_id is required")
    result = await mongo.like_card(like_data.card_id, user_id)
    if not result.error and result.result:
        return BaseResponse(result="Added like to card")
    response.status_code = status.HTTP_404_NOT_FOUND
    return result

@app.patch("/dislike_card", status_code=200)
async def dislike_card(
    dislike_data: ReactionCard,
    response: Response,
    auth_user_id: Optional[int] = Depends(get_current_user_id),
    mongo: MongoWorker = Depends(lambda: mongo_worker),) -> BaseResponse:
    user_id = auth_user_id if auth_user_id is not None else dislike_data.user_id
    if user_id is None:
        raise HTTPException(status_code=422, detail="user_id is required")
    result = await mongo.dislike_card(dislike_data.card_id, user_id)
    if not result.error and result.result:
        return BaseResponse(result="Added dislike to card")
    response.status_code = status.HTTP_404_NOT_FOUND
    return result

@app.post("/comment", status_code=201)
@guard_deco.rate_limit(requests=5, window=20)
async def comment(
    comment_info: AddCommentBody,
    response: Response,
    auth_user_id: Optional[int] = Depends(get_current_user_id),
    mongo: MongoWorker = Depends(lambda: mongo_worker),) -> BaseResponse:
    author_id = auth_user_id if auth_user_id is not None else comment_info.author_id
    if author_id is None:
        raise HTTPException(status_code=422, detail="author_id is required")
    if not moderate_text(comment_info.comment_text):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(result="Comment has not passed base moderation", error=True)

    result = await mongo.add_comment(author_id, comment_info.card_id, comment_info.comment_text)
    if result.error and result.result in ["User doesn't exist", "Card doesn't exist"]:
        response.status_code = status.HTTP_404_NOT_FOUND
        return result
    if result.error:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return result
    return result

@app.get("/get_comments", status_code=200)
async def get_comments(
    card_id: int,
    response: Response,
    mongo: MongoWorker = Depends(lambda: mongo_worker),) -> BaseResponse:
    result = await mongo.get_comments(card_id)
    if result.error:
        response.status_code = status.HTTP_404_NOT_FOUND
        return result
    return result


async def main():
    config = uvicorn.Config("main:app", host="0.0.0.0", port=5000, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())