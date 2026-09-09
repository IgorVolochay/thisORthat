"""
conftest.py — fixtures for resetting rate-limiter state and IP-ban
between tests so functional tests do not hit 429 errors.
"""

import pytest
from guard import ip_ban_manager
from guard_core.handlers.ratelimit_handler import RateLimitManager


def _reset_all():
    """Full reset of rate-limiter, IP-ban, and suspicious counts."""
    # Rate limit timestamps
    rl: RateLimitManager | None = RateLimitManager._instance
    if rl is not None:
        rl.request_timestamps.clear()

    # IP bans
    ip_ban_manager.banned_ips.clear()
    ip_ban_manager.banned_networks.clear()

    # Suspicious request counts via direct reference stored in app.state
    # Because FastAPI's add_middleware creates a new instance internally,
    # navigating app.state or app.middleware_stack is unreliable.
    # We use gc to robustly find the active SecurityMiddleware instance(s) and clear them.
    try:
        import gc
        from guard.middleware import SecurityMiddleware
        for obj in gc.get_objects():
            if isinstance(obj, SecurityMiddleware):
                obj.suspicious_request_counts.clear()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def reset_guard_state():
    """
    Synchronous fixture (autouse) that resets guard middleware
    state before and after each test.
    """
    _reset_all()
    yield
    _reset_all()
