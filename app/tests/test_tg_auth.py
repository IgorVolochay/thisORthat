"""
Tests for Telegram initData HMAC-SHA256 validation (tg_auth module).

These tests directly exercise the ``validate_init_data`` function with
synthetic initData, covering happy-path and all failure modes.
"""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException

from tg_auth import validate_init_data

import os
BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "test:mock_token_for_testing_12345")


def _build_init_data(
    bot_token: str,
    user: dict,
    auth_date: int | None = None,
    tamper_hash: bool = False,
    omit_hash: bool = False,
    omit_user: bool = False,
) -> str:
    """Helper that constructs a valid (or intentionally broken) initData string."""
    if auth_date is None:
        auth_date = int(time.time())

    params: dict[str, str] = {
        "auth_date": str(auth_date),
    }
    if not omit_user:
        params["user"] = json.dumps(user)

    # Build data-check-string (sorted, \n-separated).
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))

    # secret_key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    computed_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if tamper_hash:
        computed_hash = "a" * 64  # obviously wrong

    if not omit_hash:
        params["hash"] = computed_hash

    return urlencode(params)


VALID_USER = {
    "id": 123456789,
    "first_name": "Igor",
    "last_name": "Volochay",
    "username": "IgorVolochay",
    "photo_url": "https://t.me/photo.jpg",
}


# ── Happy path ──────────────────────────────────────────────────────────


def test_valid_init_data():
    raw = _build_init_data(BOT_TOKEN, VALID_USER)
    result = validate_init_data(raw, BOT_TOKEN)
    assert result["user_id"] == 123456789
    assert result["username"] == "IgorVolochay"
    assert result["first_name"] == "Igor"
    assert result["last_name"] == "Volochay"
    assert result["photo_url"] == "https://t.me/photo.jpg"


# ── Failure modes ───────────────────────────────────────────────────────


def test_empty_init_data():
    with pytest.raises(HTTPException) as exc:
        validate_init_data("", BOT_TOKEN)
    assert exc.value.status_code == 403


def test_missing_hash():
    raw = _build_init_data(BOT_TOKEN, VALID_USER, omit_hash=True)
    with pytest.raises(HTTPException) as exc:
        validate_init_data(raw, BOT_TOKEN)
    assert exc.value.status_code == 403
    assert "hash" in str(exc.value.detail).lower()


def test_tampered_hash():
    raw = _build_init_data(BOT_TOKEN, VALID_USER, tamper_hash=True)
    with pytest.raises(HTTPException) as exc:
        validate_init_data(raw, BOT_TOKEN)
    assert exc.value.status_code == 403
    assert "signature" in str(exc.value.detail).lower()


def test_expired_auth_date():
    old_date = int(time.time()) - 7200  # 2 hours ago
    raw = _build_init_data(BOT_TOKEN, VALID_USER, auth_date=old_date)
    with pytest.raises(HTTPException) as exc:
        validate_init_data(raw, BOT_TOKEN, max_age=3600)
    assert exc.value.status_code == 403
    assert "expired" in str(exc.value.detail).lower()


def test_missing_user():
    raw = _build_init_data(BOT_TOKEN, VALID_USER, omit_user=True)
    with pytest.raises(HTTPException) as exc:
        validate_init_data(raw, BOT_TOKEN)
    assert exc.value.status_code == 403
    assert "user" in str(exc.value.detail).lower()


def test_missing_user_id():
    user_no_id = {"first_name": "Igor", "username": "test"}
    raw = _build_init_data(BOT_TOKEN, user_no_id)
    with pytest.raises(HTTPException) as exc:
        validate_init_data(raw, BOT_TOKEN)
    assert exc.value.status_code == 403
    assert "user.id" in str(exc.value.detail).lower()


def test_wrong_bot_token():
    raw = _build_init_data(BOT_TOKEN, VALID_USER)
    with pytest.raises(HTTPException) as exc:
        validate_init_data(raw, "wrong:token")
    assert exc.value.status_code == 403


def test_fresh_auth_date_passes():
    """auth_date exactly 5 seconds ago should be fine with default max_age."""
    recent = int(time.time()) - 5
    raw = _build_init_data(BOT_TOKEN, VALID_USER, auth_date=recent)
    result = validate_init_data(raw, BOT_TOKEN)
    assert result["user_id"] == 123456789
