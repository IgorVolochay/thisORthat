import random
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from schemas.base_schemas import *
from schemas.api_schemas import *

EXIST_USER = random.randint(100000000, 1000000000)
EXIST_AUTHOR = random.randint(100000000, 1000000000)
NO_ACTIVE_CARDS_STATUS = False
ACTIVE_CARDS_LESS_THAN_TEN = False

# ------------- /add_user ---------------

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

# ---------- /get_random_cards ----------

@pytest.mark.asyncio
async def test_get_random_cards_valid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        params = {"user_id": EXIST_USER}
        response = await client.get("/get_random_cards", params=params)
        print(f"\nINPUT: endpoint=/get_random_cards\nOUTPUT: status={response.status_code} | json={response.json()}")
        if response.status_code == 404 and BaseResponse.model_validate(response.json()).result == "No active cards":
            global NO_ACTIVE_CARDS_STATUS
            NO_ACTIVE_CARDS_STATUS = True
            pytest.skip(reason="No active cards in MongoDB")
        else:
            assert response.status_code == 200
            result = response.json().get("result")
            assert isinstance(result, list)
            if len(result) == 10:
                for card in result:
                    assert "choice_A" in card
                    assert "choice_B" in card
                    assert "author_id" in card
                    assert "card_id" in card
            else:
                global ACTIVE_CARDS_LESS_THAN_TEN
                ACTIVE_CARDS_LESS_THAN_TEN = True
                pytest.skip(reason="The number of active cards is less than 10 in MongoDB")

@pytest.mark.asyncio
async def test_get_random_cards_randomness():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        params = {"user_id": EXIST_USER}
        response1 = await client.get("/get_random_cards", params=params)
        response2 = await client.get("/get_random_cards", params=params)
        result1 = response1.json().get("result")
        result2 = response2.json().get("result")
        print(f"\nINPUT: endpoint=/get_random_cards (двойной вызов)\nOUTPUT 1: {result1}\nOUTPUT 2: {result2}")
        if len(result1) == 10 and len(result2) == 10:
            assert result1 != result2

@pytest.mark.asyncio
async def test_get_random_cards_parallel_requests():
    if NO_ACTIVE_CARDS_STATUS:
        pytest.skip(reason="No active cards in MongoDB")
    elif ACTIVE_CARDS_LESS_THAN_TEN:
        pytest.skip(reason="The number of active cards is less than 10 in MongoDB")
    else:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            params = {"user_id": EXIST_USER}
            tasks = [client.get("/get_random_cards", params=params) for _ in range(5)]
            responses = await asyncio.gather(*tasks)
            for resp in responses:
                print(f"\nParallel call: status={resp.status_code} | json={resp.json()}")
                assert resp.status_code == 200
                result = resp.json().get("result")
                assert isinstance(result, list)
                assert len(result) == 10