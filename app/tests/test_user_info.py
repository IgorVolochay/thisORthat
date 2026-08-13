import random

import pytest

from main import app
from schemas.api_schemas import *
from schemas.base_schemas import *

from httpx import AsyncClient, ASGITransport


EXIST_USER = random.randint(100000000, 1000000000) 
NON_EXIST_USER = random.randint(100000000, 1000000000)



# TEST ADD USERS UTILS #

@pytest.mark.asyncio
async def test_add_user_non_full_data():
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url='http://test') as client:
        end_point = "/add_user"
        data = {
            "user_id": EXIST_USER,
            "username": "TestUsername",
            }
        raw_response = await client.post(url=end_point,json=data)
        print(f"\nINPUT: endpiont={end_point} | params={data}\nOUTPUT: status={raw_response.status_code} | json={raw_response.json()}")

        assert raw_response.status_code == 422

@pytest.mark.asyncio
async def test_add_user_negative_int_id():
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url='http://test') as client:
        end_point = "/add_user"
        data = {
            "user_id": -1,
            "username": "TestUsername",
            "first_name": "FName",
            "last_name": "LName",
            "photo_url": "http://test.test/photo.jpg"
            }
        raw_response = await client.post(url=end_point,json=data)
        print(f"\nINPUT: endpiont={end_point} | params={data}\nOUTPUT: status={raw_response.status_code} | json={raw_response.json()}")

        assert raw_response.status_code == 422

@pytest.mark.asyncio
async def test_add_new_user():
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url='http://test') as client:
        end_point = "/add_user"
        data = {
            "user_id": EXIST_USER,
            "username": "TestUsername",
            "first_name": "FName",
            "last_name": "LName",
            "photo_url": "http://test.test/photo.jpg"
            }
        raw_response = await client.post(url=end_point,json=data)
        print(f"\nINPUT: endpiont={end_point} | params={data}\nOUTPUT: status={raw_response.status_code} | json={raw_response.json()}")

        assert raw_response.status_code == 201
        response = BaseResponse.model_validate(raw_response.json())
        assert response.error == False
        assert User.model_validate(response.result)

@pytest.mark.asyncio
async def test_add_already_exist_user():
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url='http://test') as client:
        end_point = "/add_user"
        data = {
            "user_id": EXIST_USER,
            "username": "TestUsername",
            "first_name": "FName",
            "last_name": "LName",
            "photo_url": "http://test.test/photo.jpg"
            }
        raw_response = await client.post(url=end_point,json=data)
        print(f"\nINPUT: endpiont={end_point} | params={data}\nOUTPUT: status={raw_response.status_code} | json={raw_response.json()}")

        assert raw_response.status_code == 409
        response = BaseResponse.model_validate(raw_response.json())
        assert response.error == True
        assert response.result == "User already exist"




# TEST CHECK USERS UTILS #

@pytest.mark.asyncio
async def test_check_non_exist_user():
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url='http://test') as client:
        end_point = "/check_user"
        params = {"user_id": NON_EXIST_USER}
        raw_response = await client.get(url=end_point, params=params)
        print(f"\nINPUT: endpiont={end_point} | params={params}\nOUTPUT: status={raw_response.status_code} | json={raw_response.json()}")

        assert raw_response.status_code == 200
        response = BaseResponse.model_validate(raw_response.json())
        assert response.error == False
        assert response.result == False

@pytest.mark.asyncio
async def test_check_exist_user():
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url='http://test') as client:
        end_point = "/check_user"
        params = {"user_id": EXIST_USER}
        raw_response = await client.get(url=end_point, params=params)
        print(f"\nINPUT: endpiont={end_point} | params={params}\nOUTPUT: status={raw_response.status_code} | json={raw_response.json()}")

        assert raw_response.status_code == 200
        response = BaseResponse.model_validate(raw_response.json())
        assert response.error == False
        assert response.result == True




# TEST GET USERS UTILS #

@pytest.mark.asyncio
async def test_get_non_exist_user():
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url='http://test') as client:
        end_point = "/get_user"
        params = {"user_id": NON_EXIST_USER}
        raw_response = await client.get(url=end_point, params=params)
        print(f"\nINPUT: endpiont={end_point} | params={params}\nOUTPUT: status={raw_response.status_code} | json={raw_response.json()}")

        assert raw_response.status_code == 404
        response = BaseResponse.model_validate(raw_response.json())
        assert response.error == True 
        assert response.result == "User doesn't exist"

@pytest.mark.asyncio
async def test_get_exist_user():
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url='http://test') as client:
        end_point = "/get_user"
        params = {"user_id": EXIST_USER}
        raw_response = await client.get(url=end_point, params=params)
        print(f"\nINPUT: endpiont={end_point} | params={params}\nOUTPUT: status={raw_response.status_code} | json={raw_response.json()}")

        assert raw_response.status_code == 200
        response = BaseResponse.model_validate(raw_response.json())
        assert response.error == False 
        assert User.model_validate(response.result)