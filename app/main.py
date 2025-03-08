import uvicorn
import asyncio

from fastapi import FastAPI, Depends, Response, status

from schemas.api_schemas import *
from schemas.base_schemas import *
from mongo_worker import MongoWorker
from tools.base_moderation import moderate_text


app: FastAPI = FastAPI(title="This OR That",
                    summary="OpenAPI schema for \"This OR That\" project!",
                    version="0.1",
                    contact={"GitHub": "https://github.com/IgorVolochay/thisORthat"})
mongo_worker = MongoWorker()

@app.get("/check_user", status_code=200)
async def check_user(user_id: NonNegativeInt,
                     mongo: MongoWorker = Depends(lambda: mongo_worker)) -> BaseResponse:
    result = mongo.check_user(user_id)
    return BaseResponse(result=result)

@app.get("/get_user", status_code=200)
async def get_user(user_id: NonNegativeInt,
                   response: Response,
                   mongo: MongoWorker = Depends(lambda: mongo_worker)) -> BaseResponse:
    if mongo.check_user(user_id):
        result = mongo.get_user(user_id)
        return BaseResponse(result=result)
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return BaseResponse(result="User doesn't exist", error=True)

@app.post("/add_user", status_code=201)
async def add_user(new_user: AddUserBody,
                   response: Response,
                   mongo: MongoWorker = Depends(lambda: mongo_worker)) -> BaseResponse:
    if not mongo.check_user(new_user.user_id):
        result = mongo.add_user(new_user.user_id,
                                new_user.username,
                                new_user.first_name,
                                new_user.last_name,
                                new_user.photo_url)
        return BaseResponse(result=result)
    else:
        response.status_code = status.HTTP_409_CONFLICT
        return BaseResponse(result="User already exist", error=True)
    

@app.get("/get_card", status_code=200)
async def get_card(card_id: NonNegativeInt,
                   response: Response,
                   mongo: MongoWorker = Depends(lambda: mongo_worker)) -> BaseResponse:
    card = mongo.get_card(card_id)
    if card:
        return BaseResponse(result=card)
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return BaseResponse(result="There is no card with this card_id", error=True)
    
@app.get("/get_random_cards", status_code=200)
async def get_random_cards(user_id: NonNegativeInt,
                           response: Response,
                           mongo: MongoWorker = Depends(lambda: mongo_worker)) -> BaseResponse:
    cards_visited = mongo.get_visited_cards(user_id)

    if cards_visited.error:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return cards_visited
    elif not cards_visited.result.cards_visited:
        random_cards = mongo.get_random_cards(10, True)
        if random_cards:
            return BaseResponse(result=random_cards)
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return BaseResponse(result="No active cards", error=True)
    
    result: list[Card] = list()
    trys = 3
    while len(result) < 10 and trys != 0:
        random_cards = mongo.get_random_cards(10, True)
        if not random_cards:
            response.status_code = status.HTTP_404_NOT_FOUND
            return BaseResponse(result="No active cards", error=True)
        filtered_cards, filtered_cards_id = mongo.filter_cards(random_cards, cards_visited.result.cards_visited)
        trys -= 1
        if not filtered_cards:
            continue
        else:
            result.extend(filtered_cards)
            cards_visited.result.cards_visited.update(filtered_cards_id)

    if not result:
        response.status_code = status.HTTP_404_NOT_FOUND
        return BaseResponse(result="No active cards fo this user", error=True)
    else:
        return BaseResponse(result=result)
    
@app.post("/add_card", status_code=201)
async def add_card(new_card: AddCardBody,
                   response: Response,
                   mongo: MongoWorker = Depends(lambda: mongo_worker)) -> BaseResponse:
    if moderate_text(new_card.choice_A) and moderate_text(new_card.choice_B):
        card = mongo.add_card_by_api(new_card.choice_A,
                                     new_card.choice_B,
                                     new_card.author_id)
        return BaseResponse(result=card)
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(result="Card has not passed base moderation", error=True)
    

@app.patch("/select_choice", status_code=200)
async def select_choice(choice_data: SelectChoice,
                        response: Response,
                        mongo: MongoWorker = Depends(lambda: mongo_worker)) -> BaseResponse:
    check_visited = mongo.get_visited_cards(choice_data.user_id)
    if check_visited.error:
        response.status_code = status.HTTP_404_NOT_FOUND
        return check_visited
    elif not check_visited.error and choice_data.card_id in check_visited.result.cards_visited:
        response.status_code = status.HTTP_403_FORBIDDEN
        return BaseResponse(result="Card already visited!", error=True)
    else:
        select_choice_result = mongo.select_choice(choice_data.card_id, choice_data.choice)
        if select_choice_result.error:
            response.status_code = status.HTTP_404_NOT_FOUND
            return select_choice_result
        else:
            update_visited_result = mongo.update_visited_cards(choice_data.user_id, choice_data.card_id)
            return BaseResponse(result="Select choice complite!")
        
@app.patch("/like_card", status_code=200)
async def like_card(like_data: ReactionCard,
                    response: Response,
                    mongo: MongoWorker = Depends(lambda: mongo_worker)) -> BaseResponse:
    result = mongo.like_card(like_data.card_id, like_data.user_id)
    if not result.error and result.result:
        return BaseResponse(result="Added like to card")
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return result

@app.patch("/dislike_card", status_code=200)
async def dislike_card(dislike_data: ReactionCard,
                    response: Response,
                    mongo: MongoWorker = Depends(lambda: mongo_worker)) -> BaseResponse:
    result = mongo.dislike_card(dislike_data.card_id, dislike_data.user_id)
    if not result.error and result.result:
        return BaseResponse(result="Added dislike to card")
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return result
    
@app.post("/comment", status_code=201)
async def comment(comment_info: AddCommentBody,
                  response: Response,
                  mongo: MongoWorker = Depends(lambda: mongo_worker)) -> BaseResponse:
    if not moderate_text(comment_info.comment_text):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BaseResponse(result="Comment has not passed base moderation", error=True)
    
    result = mongo.add_comment(comment_info.author_id, comment_info.card_id, comment_info.comment_text)
    if result.error and result.result in ["User doesn't exist", "Card doesn't exist"]:
        response.status_code = status.HTTP_404_NOT_FOUND
        return result
    elif result.error:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return result
    else:
        return result
    

async def main():
    config = uvicorn.Config("main:app", port=5000, log_level="debug")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())