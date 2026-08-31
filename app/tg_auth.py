"""
Telegram Mini App initData authentication module.

Validates initData from the Telegram WebApp using HMAC-SHA256
per the official specification:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

In DEV_MODE (default) authentication is skipped — user_id is taken
from the request body / query parameters as-is.
"""

import hashlib
import hmac
import json
import os
import time
from typing import Optional
from urllib.parse import parse_qs

from dotenv import load_dotenv
from fastapi import HTTPException, Request, status

from logger import logger

load_dotenv()

DEV_MODE: bool = os.getenv("DEV_MODE", "true").lower() == "true"
TG_BOT_TOKEN: str = os.getenv("TG_BOT_TOKEN", "")

# Maximum allowed age of initData in seconds (1 hour).
INIT_DATA_MAX_AGE: int = int(os.getenv("INIT_DATA_MAX_AGE", "3600"))


def validate_init_data(
    init_data_raw: str,
    bot_token: str,
    max_age: int = INIT_DATA_MAX_AGE,
) -> dict:
    """
    Validates Telegram Mini App initData and returns the parsed ``user`` dict.

    Algorithm (per Telegram docs):
      1. Parse the query-string into key→value pairs.
      2. Extract the ``hash`` value; build ``data-check-string`` from the
         remaining fields sorted by key, joined with ``\\n``.
      3. ``secret_key = HMAC-SHA256(bot_token, "WebAppData")``
      4. ``computed = HMAC-SHA256(data_check_string, secret_key)``
      5. Compare ``computed`` with ``hash`` using constant-time comparison.
      6. Optionally verify ``auth_date`` freshness.

    Returns a dict with keys: user_id, username, first_name, last_name, photo_url.

    Raises ``HTTPException(403)`` on any validation failure.
    """
    if not init_data_raw:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing initData",
        )

    parsed = parse_qs(init_data_raw, keep_blank_values=True)

    # parse_qs returns lists — flatten to single values.
    flat: dict[str, str] = {k: v[0] for k, v in parsed.items()}

    received_hash = flat.pop("hash", None)
    if not received_hash:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing hash in initData",
        )

    # Build data-check-string: sorted key=value pairs joined by \n.
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(flat.items())
    )

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

    if not hmac.compare_digest(computed_hash, received_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid initData signature",
        )

    # Verify auth_date freshness.
    auth_date_str = flat.get("auth_date")
    if auth_date_str:
        try:
            auth_date = int(auth_date_str)
            if time.time() - auth_date > max_age:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="initData expired",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid auth_date",
            )

    # Extract user data.
    user_raw = flat.get("user")
    if not user_raw:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing user in initData",
        )

    try:
        user = json.loads(user_raw)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user JSON in initData",
        )

    user_id = user.get("id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing user.id in initData",
        )

    return {
        "user_id": int(user_id),
        "username": user.get("username", ""),
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "photo_url": user.get("photo_url", ""),
    }


async def get_current_user_id(request: Request) -> Optional[int]:
    """
    FastAPI dependency that resolves the authenticated user_id.

    - **DEV_MODE=true**: returns ``None`` — endpoints use user_id from
      body/params as before (backward compatible).
    - **DEV_MODE=false**: reads ``X-Init-Data`` header, validates it
      via HMAC-SHA256, and returns the verified ``user_id``.
    """
    if DEV_MODE:
        return None

    init_data_raw = request.headers.get("X-Init-Data", "")
    if not init_data_raw:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="X-Init-Data header is required",
        )

    if not TG_BOT_TOKEN:
        logger.error("TG_BOT_TOKEN is not set but DEV_MODE is disabled")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server authentication misconfiguration",
        )

    user_data = validate_init_data(init_data_raw, TG_BOT_TOKEN)
    return user_data["user_id"]
