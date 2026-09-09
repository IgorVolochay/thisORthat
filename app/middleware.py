"""
HTTP request/response logging middleware for FastAPI.

Normal requests (2xx/3xx):
    INFO  — method, path, query_params, status_code, duration_ms

Error responses (4xx):
    WARNING — all above + request_body (truncated to 1000 chars)

Server errors (5xx):
    ERROR — all above + request_body (truncated to 1000 chars)
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from logger import logger

_BODY_METHODS = frozenset({"POST", "PUT", "PATCH"})
_BODY_MAX_LEN = 1000


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()

        # Read body only for methods that carry a payload
        body: str | None = None
        if request.method in _BODY_METHODS:
            raw = await request.body()
            body = raw.decode(errors="replace")[:_BODY_MAX_LEN]

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        status = response.status_code

        client_ip = request.headers.get("X-Forwarded-For")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.headers.get("X-Real-IP") or (request.client.host if request.client else "unknown")

        base_fields = {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params) or None,
            "client_ip": client_ip,
            "status": status,
            "duration_ms": duration_ms,
        }

        if status >= 500:
            logger.bind(**base_fields, request_body=body).error(
                "{method} {path} → {status} ({duration_ms}ms)", **base_fields
            )
        elif status >= 400:
            logger.bind(**base_fields, request_body=body).warning(
                "{method} {path} → {status} ({duration_ms}ms)", **base_fields
            )
        else:
            logger.bind(**base_fields).info(
                "{method} {path} → {status} ({duration_ms}ms)", **base_fields
            )

        return response
