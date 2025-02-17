import uvicorn
import asyncio

from schemas import *

from fastapi import FastAPI, Depends
from mongo_worker import MongoWorker


app = FastAPI()

@app.get("/check_user")
async def check_user(user_id: int, mongo: MongoWorker = Depends(MongoWorker)) -> BaseResponse:
    result = mongo.check_user(user_id)
    return BaseResponse(result=result)

@app.get("/get_user")
async def get_user(user_id: int, mongo: MongoWorker = Depends(MongoWorker)) -> BaseResponse:
    result = mongo.get_user(user_id)
    return BaseResponse(result=result)


async def main():
    config = uvicorn.Config("main:app", port=5000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())