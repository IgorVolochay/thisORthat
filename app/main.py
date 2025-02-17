import uvicorn
import asyncio

from schemas.api_schemas import *
from mongo_worker import MongoWorker

from typing import Annotated

from fastapi import FastAPI, Depends, UploadFile, File


app = FastAPI()

@app.get("/check_user")
async def check_user(user_id: int,
                     mongo: MongoWorker = Depends(MongoWorker)) -> BaseResponse:
    result = mongo.check_user(user_id)
    return BaseResponse(result=result)

@app.get("/get_user")
async def get_user(user_id: int,
                   mongo: MongoWorker = Depends(MongoWorker)) -> BaseResponse:
    result = mongo.get_user(user_id)
    return BaseResponse(result=result)

@app.post("/add_user")
async def add_user(user_id: int,
                   username: str,
                   first_name: str,
                   last_name: str,
                   photo_url: str,
                   mongo: MongoWorker = Depends(MongoWorker)) -> BaseResponse:
    result = mongo.add_user(user_id, username, first_name, last_name, photo_url)
    return BaseResponse(result=result)


async def main():
    config = uvicorn.Config("main:app", port=5000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())