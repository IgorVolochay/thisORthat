import uvicorn
import asyncio

from schemas.api_schemas import *
from mongo_worker import MongoWorker

from fastapi import FastAPI, Depends, Response, status


app = FastAPI()

@app.get("/check_user", status_code=200)
async def check_user(user_id: NonNegativeInt,
                     mongo: MongoWorker = Depends(MongoWorker)) -> BaseResponse:
    result = mongo.check_user(user_id)
    return BaseResponse(result=result)

@app.get("/get_user", status_code=200)
async def get_user(user_id: NonNegativeInt,
                   response: Response,
                   mongo: MongoWorker = Depends(MongoWorker)) -> BaseResponse:
    if mongo.check_user(user_id):
        result = mongo.get_user(user_id)
        return BaseResponse(result=result)
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return BaseResponse(result="User doesn't exist", error=True)

@app.post("/add_user", status_code=201)
async def add_user(new_user: AddUserBody,
                   response: Response,
                   mongo: MongoWorker = Depends(MongoWorker)) -> BaseResponse:
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


async def main():
    config = uvicorn.Config("main:app", port=5000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())