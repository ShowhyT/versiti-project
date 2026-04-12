import logging
import time
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Deque

from aiohttp import web

from backend.services.jwt_auth import verify_jwt

logger = logging.getLogger(__name__)


def _get_client_ip(request: web.Request) -> str:
    real_ip = (request.headers.get("X-Real-IP") or "").strip()
    if real_ip:
        return real_ip
    xff = (request.headers.get("X-Forwarded-For") or "").strip()
    if xff:
        return xff.split(",", 1)[0].strip()
    return request.remote or "unknown"


def _extract_jwt_user_id(request: web.Request) -> int | None:
    auth_header = (request.headers.get("Authorization") or "").strip()
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    payload = verify_jwt(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    try:
        return int(user_id)
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True)
class RateLimitRule:
    method: str
    path: str
    limit: int
    window_s: int


class SlidingWindowRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, Deque[float]] = {}
        self._calls = 0

    def allow(self, key: str, limit: int, window_s: int) -> tuple[bool, int | None]:
        now = time.monotonic()
        dq = self._hits.get(key)
        if dq is None:
            dq = deque()
            self._hits[key] = dq

        cutoff = now - float(window_s)
        while dq and dq[0] < cutoff:
            dq.popleft()

        if len(dq) >= limit:
            retry_after = int(max(1.0, window_s - (now - dq[0])))
            return False, retry_after

        dq.append(now)

        self._calls += 1
        if self._calls % 1000 == 0:
            self._gc(cutoff)

        return True, None

    def _gc(self, cutoff: float) -> None:
        to_del: list[str] = []
        for key, dq in self._hits.items():
            while dq and dq[0] < cutoff:
                dq.popleft()
            if not dq:
                to_del.append(key)
        for key in to_del:
            self._hits.pop(key, None)


@dataclass(frozen=True)
class _PrefixRateLimitRule:
    """Rate-limit rule matching by method + path prefix (for parameterized routes)."""
    method: str
    prefix: str
    suffix: str  # e.g. "/comments", "/reactions" — matched at end of path
    limit: int
    window_s: int


# Rate limit rules for university endpoints (social endpoints are rate-limited in Rust)
RATE_LIMIT_RULES: list[RateLimitRule] = [
    RateLimitRule("POST", "/api/auth/register-start", limit=5, window_s=60),
    RateLimitRule("POST", "/api/auth/register-2fa", limit=10, window_s=60),
    RateLimitRule("POST", "/api/auth/register-complete", limit=5, window_s=60),
    RateLimitRule("POST", "/api/auth/mirea-connect", limit=8, window_s=60),
    RateLimitRule("POST", "/api/auth/mirea-2fa", limit=10, window_s=60),
    RateLimitRule("POST", "/api/attendance/mark", limit=15, window_s=60),
    RateLimitRule("POST", "/api/esports/login", limit=8, window_s=60),
    RateLimitRule("POST", "/api/esports/book", limit=20, window_s=300),
    RateLimitRule("POST", "/api/esports/cancel", limit=20, window_s=300),
    RateLimitRule("POST", "/api/auth/mirea-disconnect", limit=3, window_s=60),
    RateLimitRule("POST", "/api/profile/check-connection", limit=10, window_s=60),
    RateLimitRule("POST", "/api/translate", limit=20, window_s=60),
RateLimitRule("GET", "/api/schedule", limit=30, window_s=60),
    RateLimitRule("POST", "/api/ai/chat", limit=15, window_s=60),
    RateLimitRule("POST", "/api/ai/action", limit=20, window_s=60),
]

_PREFIX_RULES: list[_PrefixRateLimitRule] = []


_rl = SlidingWindowRateLimiter()


@web.middleware
async def request_id_middleware(request: web.Request, handler):
    request_id = uuid.uuid4().hex[:12]
    request["request_id"] = request_id
    start = time.monotonic()
    response = await handler(request)
    if isinstance(response, web.StreamResponse):
        response.headers["X-Request-ID"] = request_id
    duration_ms = round((time.monotonic() - start) * 1000, 1)
    status = getattr(response, "status", 0)
    logger.info(
        "%s %s → %s (%.1fms)",
        request.method,
        request.path,
        status,
        duration_ms,
        extra={"request_id": request_id},
    )
    return response


@web.middleware
async def json_error_middleware(request: web.Request, handler):
    try:
        return await handler(request)
    except web.HTTPException as e:
        if request.path.startswith("/api"):
            payload = {"success": False, "message": e.reason}
            req_id = request.get("request_id")
            if req_id:
                payload["request_id"] = req_id
            return web.json_response(payload, status=e.status)
        raise
    except Exception:
        req_id = request.get("request_id")
        logger.exception(
            "Unhandled API error",
            extra={
                "request_id": req_id,
                "method": request.method,
                "path": request.path,
            },
        )
        payload = {"success": False, "message": "Internal server error"}
        if req_id:
            payload["request_id"] = req_id
        return web.json_response(payload, status=500)


@web.middleware
async def rate_limit_middleware(request: web.Request, handler):
    method = request.method.upper()
    path = request.path

    rule = next((r for r in RATE_LIMIT_RULES if r.method == method and r.path == path), None)

    # Check prefix-based rules for parameterized paths
    if rule is None:
        for pr in _PREFIX_RULES:
            if pr.method == method and path.startswith(pr.prefix) and path.endswith(pr.suffix):
                rule = RateLimitRule(pr.method, path, pr.limit, pr.window_s)
                break

    if rule is None:
        return await handler(request)

    user_id = _extract_jwt_user_id(request)
    client_ip = _get_client_ip(request)

    key = f"{rule.method}:{rule.path}:{user_id or client_ip}"
    allowed, retry_after = _rl.allow(key, rule.limit, rule.window_s)
    if allowed:
        return await handler(request)

    payload = {
        "success": False,
        "message": "Too many requests",
    }
    req_id = request.get("request_id")
    if req_id:
        payload["request_id"] = req_id

    resp = web.json_response(payload, status=429)
    if retry_after:
        resp.headers["Retry-After"] = str(retry_after)
    return resp
