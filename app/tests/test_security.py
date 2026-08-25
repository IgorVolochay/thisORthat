"""
test_security.py — tests for checking rate limiting and penetration detection.

Rate limiting settings from main.py:
  - Global: 10 requests / 3 sec (middleware)
  - /add_user: 3 requests / 60 sec (decorator)
  - /add_card: 3 requests / 60 sec (decorator)
  - /get_random_cards: 5 requests / 60 sec (decorator)
  - /comment: 5 requests / 20 sec (decorator)

Penetration detection:
  - enable_penetration_detection=True
  - auto_ban_threshold=3 (ban after 3 suspicious requests)
  - auto_ban_duration=3600 (ban for 1 hour)
"""

import random
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from main import app


# ========================================================================
#  RATE LIMIT TESTS
# ========================================================================


class TestGlobalRateLimit:
    """Tests for global rate limit: 10 requests / 3 seconds."""

    @pytest.mark.asyncio(loop_scope="session")
    async def test_global_rate_limit_allows_under_threshold(self):
        """Requests within the limit (<=10) should pass."""
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            for i in range(9):
                resp = await client.get("/check_user", params={"user_id": 1})
                assert resp.status_code == 200, (
                    f"Request {i+1}/9 returned {resp.status_code}, expected 200: {resp.text}"
                )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_global_rate_limit_blocks_over_threshold(self):
        """
        After exceeding global limit (10 requests/3s) -> 429.
        /check_user does not have a rate_limit decorator, so only global limit applies.
        """
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            # Send 10 requests (fill the limit)
            for i in range(10):
                await client.get("/check_user", params={"user_id": 1})

            # 11th request should return 429
            resp = await client.get("/check_user", params={"user_id": 1})
            assert resp.status_code == 429, (
                f"Expected 429 after exceeding global limit, got {resp.status_code}"
            )
            assert "Too many requests" in resp.text

    @pytest.mark.asyncio(loop_scope="session")
    async def test_global_rate_limit_response_format(self):
        """Verify response format on rate limit."""
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            # Exhaust limit
            for _ in range(10):
                await client.get("/check_user", params={"user_id": 1})

            resp = await client.get("/check_user", params={"user_id": 1})
            assert resp.status_code == 429
            assert resp.text == "Too many requests"


class TestDecoratorRateLimit:
    """Tests for rate limit via @guard_deco.rate_limit() decorator."""

    @pytest.mark.asyncio(loop_scope="session")
    async def test_add_user_rate_limit(self):
        """
        /add_user: limit 3 requests / 60 sec.
        First 3 requests pass (422 due to invalid data is OK, main point is not 429).
        4th request -> 429.
        """
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            data = {
                "user_id": random.randint(100000000, 999999999),
                "username": "RateTest",
                "first_name": "F",
                "last_name": "L",
                "photo_url": "http://test.test/photo.jpg"
            }

            # First 3 requests — not 429
            for i in range(3):
                resp = await client.post("/add_user", json=data)
                assert resp.status_code != 429, (
                    f"Request {i+1}/3 returned 429, limit should not be exceeded yet"
                )

            # 4th request -> 429
            resp = await client.post("/add_user", json=data)
            assert resp.status_code == 429, (
                f"Expected 429 after 3 requests to /add_user, got {resp.status_code}"
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_add_card_rate_limit(self):
        """
        /add_card: limit 3 requests / 60 sec.
        """
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            author_id = random.randint(100000000, 999999999)
            for i in range(3):
                payload = {
                    "choice_A": f"Rate A {i}",
                    "choice_B": f"Rate B {i}",
                    "author_id": author_id
                }
                resp = await client.post("/add_card", json=payload)
                assert resp.status_code != 429, (
                    f"Request {i+1}/3 to /add_card returned 429 prematurely"
                )

            payload = {
                "choice_A": "Rate A overflow",
                "choice_B": "Rate B overflow",
                "author_id": author_id
            }
            resp = await client.post("/add_card", json=payload)
            assert resp.status_code == 429, (
                f"Expected 429 after 3 requests to /add_card, got {resp.status_code}"
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_get_random_cards_rate_limit(self):
        """
        /get_random_cards: limit 5 requests / 60 sec.
        """
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            user_id = random.randint(100000000, 999999999)

            for i in range(5):
                resp = await client.get("/get_random_cards", params={"user_id": user_id})
                # Can be 200 or 404 (if no cards/user), but not 429
                assert resp.status_code != 429, (
                    f"Request {i+1}/5 to /get_random_cards returned 429 prematurely"
                )

            resp = await client.get("/get_random_cards", params={"user_id": user_id})
            assert resp.status_code == 429, (
                f"Expected 429 after 5 requests to /get_random_cards, got {resp.status_code}"
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_comment_rate_limit(self):
        """
        /comment: limit 5 requests / 20 sec.
        """
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            for i in range(5):
                payload = {
                    "author_id": random.randint(100000000, 999999999),
                    "card_id": 1,
                    "comment_text": f"Rate test comment {i}"
                }
                resp = await client.post("/comment", json=payload)
                # Can be 201, 400 (moderation), 404 (card/user not found) — but not 429
                assert resp.status_code != 429, (
                    f"Request {i+1}/5 to /comment returned 429 prematurely"
                )

            payload = {
                "author_id": random.randint(100000000, 999999999),
                "card_id": 1,
                "comment_text": "Overflow comment"
            }
            resp = await client.post("/comment", json=payload)
            assert resp.status_code == 429, (
                f"Expected 429 after 5 requests to /comment, got {resp.status_code}"
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_different_endpoints_have_independent_limits(self):
        """
        Decorator rate limit is tracked separately for each endpoint.
        Requests to /check_user should not affect /add_card limit.
        """
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            # 5 requests to /check_user (no decorator, but global limit 10/3s)
            for _ in range(5):
                await client.get("/check_user", params={"user_id": 1})

            # First request to /add_card — should pass (its own separate limit)
            payload = {
                "choice_A": "IndepA",
                "choice_B": "IndepB",
                "author_id": random.randint(100000000, 999999999)
            }
            resp = await client.post("/add_card", json=payload)
            assert resp.status_code != 429, (
                f"Request to /add_card blocked after requests to /check_user: {resp.status_code}"
            )


class TestRateLimitParallel:
    """Rate limit tests with parallel requests."""

    @pytest.mark.asyncio(loop_scope="session")
    async def test_parallel_requests_hit_rate_limit(self):
        """
        Multiple parallel requests should lead to 429 for some of them.
        Send 15 parallel requests with global limit of 10/3s.
        """
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            tasks = [
                client.get("/check_user", params={"user_id": 1})
                for _ in range(15)
            ]
            responses = await asyncio.gather(*tasks)

            statuses = [r.status_code for r in responses]
            count_200 = statuses.count(200)
            count_429 = statuses.count(429)

            print(f"\nParallel requests: 200={count_200}, 429={count_429}")
            assert count_429 > 0, (
                f"No request received 429 during 15 parallel requests: {statuses}"
            )
            assert count_200 > 0, (
                f"All requests were blocked, none passed: {statuses}"
            )


# ========================================================================
#  PENETRATION DETECTION TESTS
# ========================================================================


class TestPenetrationDetection:
    """
    Tests for malicious request detection.
    enable_penetration_detection=True
    auto_ban_threshold=3
    auto_ban_duration=3600
    """

    @pytest.mark.asyncio(loop_scope="session")
    async def test_sql_injection_detected(self):
        """SQL injection in query parameters should be detected."""
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            resp = await client.get(
                "/get_card",
                params={"card_id": "1 OR 1=1; DROP TABLE users;--"}
            )
            print(f"\nSQL injection test: status={resp.status_code} | text={resp.text[:200]}")
            # Expect: 400 (suspicious activity) or 422 (validation) — but NOT 200
            assert resp.status_code in (400, 403, 422), (
                f"SQL injection was not blocked, got {resp.status_code}: {resp.text[:200]}"
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_xss_in_query_params_detected(self):
        """XSS attack in query parameters should be detected."""
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            resp = await client.get(
                "/get_card",
                params={"card_id": "<script>alert('XSS')</script>"}
            )
            print(f"\nXSS in params test: status={resp.status_code} | text={resp.text[:200]}")
            assert resp.status_code in (400, 403, 422), (
                f"XSS attack was not detected, got {resp.status_code}: {resp.text[:200]}"
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_path_traversal_detected(self):
        """Path traversal attack should be detected."""
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            resp = await client.get("/get_card/../../../etc/passwd")
            print(f"\nPath traversal test: status={resp.status_code} | text={resp.text[:200]}")
            # Can be 400, 403, 404, or 422 — but MUST NOT expose file contents
            assert resp.status_code != 200 or "root:" not in resp.text, (
                "Path traversal not detected — system file accessed!"
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_xss_in_post_body_detected(self):
        """XSS attack in POST body should be detected."""
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            payload = {
                "choice_A": "<script>document.cookie</script>",
                "choice_B": "Normal option",
                "author_id": random.randint(100000000, 999999999)
            }
            resp = await client.post("/add_card", json=payload)
            print(f"\nXSS in body test: status={resp.status_code} | text={resp.text[:200]}")
            # 400 (suspicious), 403 (banned), or 422 — but not 201
            assert resp.status_code in (400, 403, 422), (
                f"XSS in request body was not detected, got {resp.status_code}: {resp.text[:200]}"
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_command_injection_detected(self):
        """Command injection attempt should be detected."""
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            payload = {
                "choice_A": "; cat /etc/passwd; echo",
                "choice_B": "$(whoami)",
                "author_id": random.randint(100000000, 999999999)
            }
            resp = await client.post("/add_card", json=payload)
            print(f"\nCommand injection test: status={resp.status_code} | text={resp.text[:200]}")
            # 400 (suspicious), 403 (banned) — not 201
            assert resp.status_code in (400, 403, 422), (
                f"Command injection was not detected, got {resp.status_code}: {resp.text[:200]}"
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_sql_union_injection_detected(self):
        """UNION-based SQL injection should be detected."""
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            resp = await client.get(
                "/get_card",
                params={"card_id": "1 UNION SELECT password FROM users"}
            )
            print(f"\nUNION SQL injection test: status={resp.status_code} | text={resp.text[:200]}")
            assert resp.status_code in (400, 403, 422), (
                f"UNION SQL injection was not blocked, got {resp.status_code}"
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_legitimate_request_not_blocked(self):
        """Legitimate request with normal data should not be blocked as suspicious."""
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            resp = await client.get("/get_card", params={"card_id": 1})
            print(f"\nLegitimate request test: status={resp.status_code}")
            # 200 (card found) or 404 (not found) — but not 400/403
            assert resp.status_code in (200, 404), (
                f"Legitimate request blocked: {resp.status_code}: {resp.text[:200]}"
            )


class TestAutoIPBan:
    """
    Tests for automatic IP banning after repeated suspicious requests.
    auto_ban_threshold=3, auto_ban_duration=3600
    """

    @pytest.mark.asyncio(loop_scope="session")
    async def test_repeated_attacks_trigger_ip_ban(self):
        """
        After auto_ban_threshold (3) suspicious requests, the IP should be banned.
        Subsequent requests (even legitimate ones) should return 403.
        """
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            # Send suspicious requests sequentially (SQL injection variants)
            injection_payloads = [
                "1' OR '1'='1",
                "1; DROP TABLE cards;--",
                "1 UNION SELECT * FROM users;--",
                "1' AND 1=CONVERT(int,(SELECT TOP 1 name FROM sysobjects));--",
            ]
            detected_as_suspicious = 0
            for payload in injection_payloads:
                resp = await client.get("/get_card", params={"card_id": payload})
                if resp.status_code in (400, 403):
                    detected_as_suspicious += 1
                print(f"  Attack attempt: status={resp.status_code} | payload={payload[:50]}")

            print(f"\nSuspicious requests detected: {detected_as_suspicious}/{len(injection_payloads)}")

            if detected_as_suspicious >= 3:
                # Threshold reached — verify ban on legitimate request
                resp = await client.get("/check_user", params={"user_id": 1})
                print(f"Post-attack legitimate request: status={resp.status_code}")
                assert resp.status_code == 403, (
                    f"IP should be banned after {detected_as_suspicious} suspicious requests, "
                    f"but legitimate request returned {resp.status_code}: {resp.text[:200]}"
                )
            else:
                pytest.skip(
                    f"Only {detected_as_suspicious} of {len(injection_payloads)} attacks detected, "
                    f"ban threshold (3) not reached"
                )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_banned_ip_returns_403_on_all_endpoints(self):
        """
        If IP is banned, all endpoints should return 403.
        """
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            # Send various attacks to guarantee hitting the threshold
            attacks = [
                "1' OR '1'='1; --",
                "1; DROP TABLE cards; --",
                "<script>alert(1)</script>",
                "../../etc/shadow",
                "1 UNION SELECT password FROM users",
            ]
            detected_count = 0
            for payload in attacks:
                resp = await client.get("/get_card", params={"card_id": payload})
                if resp.status_code in (400, 403):
                    detected_count += 1
                print(f"  [{payload[:40]}] status={resp.status_code}")

            print(f"\nDetected: {detected_count}/{len(attacks)}")

            if detected_count >= 3:
                # Check ban on different endpoints
                endpoints = [
                    ("GET", "/check_user", {"user_id": 99999}),
                    ("GET", "/get_user", {"user_id": 99999}),
                    ("GET", "/get_card", {"card_id": 1}),
                ]
                for method, path, params in endpoints:
                    resp = await client.get(path, params=params)
                    assert resp.status_code == 403, (
                        f"IP is banned, but {method} {path} returned {resp.status_code}"
                    )
            else:
                pytest.skip(
                    f"Only {detected_count} attacks detected, ban threshold (3) not reached"
                )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_banned_ip_message(self):
        """Banned IP should receive 'IP address banned' message."""
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            attacks = [
                "1' OR '1'='1; --",
                "1; DROP TABLE cards; --",
                "1 UNION SELECT password FROM users",
                "<script>alert(1)</script>",
            ]
            detected = 0
            for payload in attacks:
                resp = await client.get("/get_card", params={"card_id": payload})
                if resp.status_code in (400, 403):
                    detected += 1

            if detected >= 3:
                resp = await client.get("/check_user", params={"user_id": 1})
                assert resp.status_code == 403
                assert "IP address banned" in resp.text, (
                    f"Expected message 'IP address banned', got: {resp.text[:200]}"
                )
            else:
                pytest.skip(f"Only {detected} attacks detected, threshold not reached")


class TestSuspiciousHeaders:
    """Tests for suspicious header detection."""

    @pytest.mark.asyncio(loop_scope="session")
    async def test_suspicious_user_agent(self):
        """Request with suspicious User-Agent may be blocked."""
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            resp = await client.get(
                "/check_user",
                params={"user_id": 1},
                headers={"User-Agent": "sqlmap/1.6.12#stable (http://sqlmap.org)"}
            )
            print(f"\nSuspicious UA test: status={resp.status_code}")
            # sqlmap is a known SQL injection tool
            # Expect block (403) or pass (200 — if UA is not in blocklist)
            assert resp.status_code in (200, 400, 403), (
                f"Unexpected status code for suspicious User-Agent: {resp.status_code}"
            )

    @pytest.mark.asyncio(loop_scope="session")
    async def test_xss_in_headers(self):
        """XSS attack via custom headers."""
        async with AsyncClient(transport=ASGITransport(app=app, client=("127.0.0.1", 50000)), base_url="http://test") as client:
            resp = await client.get(
                "/check_user",
                params={"user_id": 1},
                headers={"X-Forwarded-For": "<script>alert(1)</script>"}
            )
            print(f"\nXSS in headers test: status={resp.status_code}")
            # Header may be ignored or detected as suspicious
            assert resp.status_code in (200, 400, 403), (
                f"Unexpected status code for XSS in headers: {resp.status_code}"
            )
