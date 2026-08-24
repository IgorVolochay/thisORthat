"""
conftest.py — fixtures for resetting rate-limiter state and IP-ban
between tests so functional tests do not hit 429 errors.
"""

import pytest
from guard import ip_ban_manager
from guard_core.handlers.ratelimit_handler import RateLimitManager


def _clear_middleware_suspicious_counts():
    """Search for SecurityMiddleware in middleware stack and clear suspicious_request_counts."""
    from guard.middleware import SecurityMiddleware
    from main import app
    current = app
    visited = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if isinstance(current, SecurityMiddleware):
            current.suspicious_request_counts.clear()
            break
        current = getattr(current, 'app', None)


def _reset_all():
    """Full reset of rate-limiter, IP-ban, and suspicious counts."""
    # Rate limit timestamps
    rl: RateLimitManager | None = RateLimitManager._instance
    if rl is not None:
        rl.request_timestamps.clear()

    # IP bans
    ip_ban_manager.banned_ips.clear()
    ip_ban_manager.banned_networks.clear()

    # Suspicious request counts
    _clear_middleware_suspicious_counts()


@pytest.fixture(autouse=True)
def reset_guard_state():
    """
    Synchronous fixture (autouse) that resets guard middleware
    state before and after each test.
    """
    _reset_all()
    yield
    _reset_all()
