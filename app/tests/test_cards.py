import random
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from schemas.base_schemas import *
from schemas.api_schemas import *


EXIST_AUTHOR = random.randint(100000000, 1000000000)
NON_EXIST_CARD_ID = 1000
NO_ACTIVE_CARDS_STATUS = False
ACTIVE_CARDS_LESS_THAN_TEN = False


# ---------- /add_card ----------

@pytest.mark.asyncio
async def test_add_card_valid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "choice_A": "Option A",
            "choice_B": "Option B",
            "author_id": EXIST_AUTHOR
        }
        response = await client.post("/add_card", json=payload)
        print(f"\nINPUT: endpoint=/add_card | payload={payload}\nOUTPUT: status={response.status_code} | json={response.json()}")
        assert response.status_code in (200, 201)
        base_resp = BaseResponse.model_validate(response.json())
        assert base_resp.error is False
        card = Card.model_validate(base_resp.result)
        assert card.choice_A == payload["choice_A"]
        assert card.choice_B == payload["choice_B"]
        assert card.author_id == payload["author_id"]

@pytest.mark.asyncio
async def test_add_card_missing_field():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            #choice_A
            "choice_B": "Option B",
            "author_id": EXIST_AUTHOR
        }
        response = await client.post("/add_card", json=payload)
        print(f"\nINPUT: endpoint=/add_card | payload (missing field)={payload}\nOUTPUT: status={response.status_code} | json={response.json()}")
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_add_card_wrong_type():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "choice_A": 123,
            "choice_B": "Option B",
            "author_id": EXIST_AUTHOR
        }
        response = await client.post("/add_card", json=payload)
        print(f"\nINPUT: endpoint=/add_card | payload (wrong type)={payload}\nOUTPUT: status={response.status_code} | json={response.json()}")
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_add_card_empty_strings():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "choice_A": "",
            "choice_B": "",
            "author_id": EXIST_AUTHOR
        }
        response = await client.post("/add_card", json=payload)
        print(f"\nINPUT: endpoint=/add_card | payload (empty strings)={payload}\nOUTPUT: status={response.status_code} | json={response.json()}")
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_add_card_long_strings():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        long_str = "A" * 5000  # long string
        payload = {
            "choice_A": long_str,
            "choice_B": long_str,
            "author_id": EXIST_AUTHOR
        }
        response = await client.post("/add_card", json=payload)
        print(f"\nINPUT: endpoint=/add_card | payload with long strings (length={len(long_str)})\nOUTPUT: status={response.status_code} | json={response.json()}")
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_add_card_negative_author_id():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "choice_A": "Option A",
            "choice_B": "Option B",
            "author_id": -10 # Negative id
        }
        response = await client.post("/add_card", json=payload)
        print(f"\nINPUT: endpoint=/add_card | payload (negative author_id)={payload}\nOUTPUT: status={response.status_code} | json={response.json()}")
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_add_card_malformed_json():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        malformed_json = '{"choice_A": "Option A", "choice_B": "Option B", "author_id": 123' # broken json
        response = await client.post(
            "/add_card",
            data=malformed_json,
            headers={"Content-Type": "application/json"}
        )
        print(f"\nINPUT: endpoint=/add_card | payload (malformed JSON)={malformed_json}\nOUTPUT: status={response.status_code} | json={response.json() if response.content else 'No JSON'}")
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_async_card_creation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tasks = []
        num_cards = 8
        for i in range(num_cards):
            payload = {
                "choice_A": f"Async Option A {i}",
                "choice_B": f"Async Option B {i}",
                "author_id": EXIST_AUTHOR
            }
            tasks.append(client.post("/add_card", json=payload))
        responses = await asyncio.gather(*tasks)
        
        card_ids = []
        for idx, response in enumerate(responses):
            print(f"\nAsync creation {idx}: status={response.status_code}, response={response.json()}")
            assert response.status_code in (200, 201)
            base_resp = BaseResponse.model_validate(response.json())
            assert base_resp.error is False
            card = Card.model_validate(base_resp.result)
            card_ids.append(card.card_id)
            assert card.choice_A == f"Async Option A {idx}"
            assert card.choice_B == f"Async Option B {idx}"
            assert card.author_id == EXIST_AUTHOR

        assert len(set(card_ids)) == num_cards


# ---------- /get_card ----------

@pytest.mark.asyncio
async def test_get_card_valid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "choice_A": "GetTest A",
            "choice_B": "GetTest B",
            "author_id": EXIST_AUTHOR
        }
        create_resp = await client.post("/add_card", json=payload)
        base_create = BaseResponse.model_validate(create_resp.json())
        card = Card.model_validate(base_create.result)
        card_id = card.card_id

        response = await client.get("/get_card", params={"card_id": card_id})
        print(f"\nINPUT: endpoint=/get_card | params={{'card_id': {card_id}}}\nOUTPUT: status={response.status_code} | json={response.json()}")
        assert response.status_code == 200
        base_resp = BaseResponse.model_validate(response.json())
        assert base_resp.error is False
        card_from_get = Card.model_validate(base_resp.result)
        assert card_from_get.card_id == card_id

@pytest.mark.asyncio
async def test_get_card_nonexistent():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/get_card", params={"card_id": NON_EXIST_CARD_ID})
        print(f"\nINPUT: endpoint=/get_card | params={{'card_id': {NON_EXIST_CARD_ID}}}\nOUTPUT: status={response.status_code} | json={response.json()}")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_card_missing_param():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/get_card")
        print(f"\nINPUT: endpoint=/get_card (missing card_id param)\nOUTPUT: status={response.status_code} | json={response.json() if response.content else 'No content'}")
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_card_wrong_type():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/get_card", params={"card_id": "abc"})
        print(f"\nINPUT: endpoint=/get_card | params={{'card_id': 'abc'}}\nOUTPUT: status={response.status_code} | json={response.json()}")
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_card_negative():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/get_card", params={"card_id": -10})
        print(f"\nINPUT: endpoint=/get_card | params={{'card_id': -10}}\nOUTPUT: status={response.status_code} | json={response.json()}")
        assert response.status_code == 422


# ---------- /get_random_cards ----------

@pytest.mark.asyncio
async def test_get_random_cards_valid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/get_random_cards")
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
        response1 = await client.get("/get_random_cards")
        response2 = await client.get("/get_random_cards")
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
            tasks = [client.get("/get_random_cards") for _ in range(5)]
            responses = await asyncio.gather(*tasks)
            for resp in responses:
                print(f"\nParallel call: status={resp.status_code} | json={resp.json()}")
                assert resp.status_code == 200
                result = resp.json().get("result")
                assert isinstance(result, list)
                assert len(result) == 10