from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from aiohttp import web
from sqlalchemy import select, update

from backend.database import async_session
from backend.database.models import User
from backend.services.jwt_auth import verify_jwt


BUILD_INFO_FILE = Path(__file__).resolve().parents[2] / "build_info.json"


def iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def redact_qr_data_for_log(qr_data: str) -> str:
    value = (qr_data or "").strip()
    if not value:
        return ""
    if value.startswith("http"):
        try:
            parsed = urlparse(value)
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?token=<redacted>"
        except Exception:
            return "<redacted_url>"
    return "<redacted_token>"


def load_build_info() -> dict:
    """
    Read deployment metadata (if present).

    Priority:
    1) env APP_VERSION / GIT_SHA
    2) build_info.json generated during deploy
    """
    info: dict[str, str] = {}

    env_version = (os.getenv("APP_VERSION") or os.getenv("GIT_SHA") or "").strip()
    if env_version:
        info["version"] = env_version

    try:
        raw = BUILD_INFO_FILE.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            for key in ("version", "git_sha", "branch", "deployed_at_utc"):
                value = parsed.get(key)
                if isinstance(value, str) and value.strip():
                    if key == "version" and info.get("version"):
                        continue
                    info[key] = value.strip()
            if "version" not in info:
                fallback_sha = parsed.get("git_sha")
                if isinstance(fallback_sha, str) and fallback_sha.strip():
                    info["version"] = fallback_sha.strip()
    except Exception:
        pass

    return info


async def persist_session_if_current(
    session,
    *,
    user_id: int,
    previous_session: str | None,
    updated_session: str | None,
) -> bool:
    """
    Optimistic compare-and-set update for mirea_session.
    Prevents stale concurrent requests from overwriting a newer session blob.
    """
    if not updated_session or updated_session == previous_session:
        return False

    stmt = update(User).where(User.id == user_id)
    if previous_session is None:
        stmt = stmt.where(User.mirea_session.is_(None))
    else:
        stmt = stmt.where(User.mirea_session == previous_session)
    stmt = stmt.values(mirea_session=updated_session)

    result = await session.execute(stmt)
    changed = int(getattr(result, "rowcount", 0) or 0)
    return changed > 0


async def get_current_user(request: web.Request) -> tuple[User | None, async_session | None]:
    """Extract JWT from Authorization header, return (User, session) or (None, None)."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, None

    token = auth_header[7:]
    payload = verify_jwt(token)
    if not payload:
        return None, None

    user_id = payload.get("sub")
    if not user_id:
        return None, None

    token_iat = payload.get("iat", 0)

    session = async_session()
    try:
        result = await session.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            await session.close()
            return None, None

        # Reject tokens issued before password change or session revocation.
        # Use int() to truncate microseconds — iat is also truncated to seconds.
        if user.password_changed_at and int(user.password_changed_at.timestamp()) > token_iat:
            await session.close()
            return None, None
        if user.sessions_revoked_at and int(user.sessions_revoked_at.timestamp()) > token_iat:
            await session.close()
            return None, None

        return user, session
    except Exception:
        await session.close()
        return None, None


async def require_user(request: web.Request) -> tuple[User, async_session]:
    """Get authenticated user or raise 401. Banned users get 403."""
    user, session = await get_current_user(request)
    if not user or not session:
        raise web.HTTPUnauthorized(
            text='{"error": "Unauthorized"}',
            content_type="application/json",
        )
    if getattr(user, "is_banned", False):
        await session.close()
        raise web.HTTPForbidden(
            text='{"error": "Account is banned"}',
            content_type="application/json",
        )
    return user, session


async def require_admin(request: web.Request) -> tuple[User, async_session]:
    """Get authenticated admin user or raise 403."""
    user, session = await require_user(request)
    if not getattr(user, "is_admin", False):
        await session.close()
        raise web.HTTPForbidden(
            text='{"error": "Admin access required"}',
            content_type="application/json",
        )
    return user, session



