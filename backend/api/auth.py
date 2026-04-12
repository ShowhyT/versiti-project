from __future__ import annotations

import asyncio
import logging
import secrets
import time as time_module
from dataclasses import dataclass, field
from datetime import datetime, timezone

import jwt as pyjwt

from aiohttp import web
from sqlalchemy import select

from backend.api.common import require_user
from backend.database import async_session
from backend.database.models import User
from backend.services.crypto import get_crypto
from backend.services.jwt_auth import create_jwt
from backend.services.mirea_auth import AuthChallenge, MireaAuth

logger = logging.getLogger(__name__)

_PENDING_2FA_TTL_S = 5 * 60
_PENDING_2FA_MAX_ATTEMPTS = 5


@dataclass
class _Pending2FA:
    mirea_login: str
    created_at: float
    attempts: int
    cookies: dict
    action_url: str
    field_name: str
    hidden_fields: dict[str, str]
    referer: str | None = None
    pkce_verifier: str | None = None
    redirect_uri: str | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False, compare=False)


_PENDING_2FA: dict[str, _Pending2FA] = {}


def _purge_pending_2fa(now: float | None = None) -> None:
    now_ts = float(now if now is not None else time_module.time())
    expired = [
        key for key, item in list(_PENDING_2FA.items()) if now_ts - float(item.created_at) > _PENDING_2FA_TTL_S
    ]
    for key in expired:
        _PENDING_2FA.pop(key, None)


def _new_state() -> str:
    return secrets.token_urlsafe(32)


def _extract_from_token(cookies: dict) -> tuple[str, str]:
    """Extract display name and email from Keycloak access_token JWT."""
    access_token = (cookies.get("access_token") or "").strip()
    name = ""
    email = ""
    if not access_token:
        return name, email
    try:
        payload = pyjwt.decode(access_token, options={"verify_signature": False})
        name = (payload.get("name") or "").strip()
        if not name:
            given = (payload.get("given_name") or "").strip()
            family = (payload.get("family_name") or "").strip()
            if given or family:
                name = f"{family} {given}".strip()
        if not name:
            name = (payload.get("preferred_username") or "").strip()
        email = (payload.get("email") or "").strip()
    except Exception:
        pass
    return name, email


async def _get_or_create_user(mirea_login: str, cookies: dict) -> tuple[User, str]:
    """Find existing user by mirea_login or create new one. Returns (user, jwt_token)."""
    display_name, email = _extract_from_token(cookies)

    cookies["__token_refreshed_at"] = int(time_module.time())
    crypto = get_crypto()
    encrypted_session = crypto.encrypt_session(cookies)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.mirea_login == mirea_login))
        user = result.scalar_one_or_none()

        if user:
            # Update session and info
            user.mirea_session = encrypted_session
            user.last_mirea_sync_at = datetime.utcnow()
            if display_name and display_name != user.full_name:
                user.full_name = display_name
            if email:
                user.email = email
            await session.commit()
            await session.refresh(user)
            token = create_jwt(user.id)
            return user, token

        # Create new user
        user = User(
            full_name=display_name or mirea_login,
            mirea_session=encrypted_session,
            mirea_login=mirea_login,
            email=email or None,
            last_mirea_sync_at=datetime.utcnow(),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        token = create_jwt(user.id)
        return user, token


# ---------------------------------------------------------------------------
# POST /api/auth/login — single-step MIREA auth (auto-creates account)
# ---------------------------------------------------------------------------


async def handle_login(request: web.Request) -> web.Response:
    """Authenticate with MIREA credentials. Auto-creates account if first login."""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "message": "Invalid JSON"}, status=400)

    login = (data.get("login") or "").strip()
    password = data.get("password") or ""
    if not login or not password:
        return web.json_response({"success": False, "message": "Введите логин и пароль МИРЭА"}, status=400)

    auth = MireaAuth()
    try:
        result = await auth.login(login, password)
    except Exception as e:
        logger.error("login MIREA auth error: %s", e, exc_info=True)
        return web.json_response({"success": False, "message": "МИРЭА временно недоступна"}, status=500)
    finally:
        await auth.close()

    if not result.success:
        challenge_kind = getattr(result.challenge, "kind", None) if result.challenge else None
        if challenge_kind in ("otp", "email_code"):
            _purge_pending_2fa()
            state = _new_state()
            cookies = result.cookies or {}
            challenge = result.challenge
            _PENDING_2FA[state] = _Pending2FA(
                mirea_login=login,
                created_at=time_module.time(),
                attempts=0,
                cookies=cookies,
                action_url=challenge.action_url,
                field_name=challenge.field_name,
                hidden_fields=challenge.hidden_fields or {},
                referer=challenge.referer,
                pkce_verifier=getattr(challenge, "pkce_verifier", None),
                redirect_uri=getattr(challenge, "redirect_uri", None),
            )
            return web.json_response({
                "success": False,
                "needs_2fa": True,
                "state": state,
                "challenge_kind": challenge_kind,
                "message": result.message or "Требуется код подтверждения",
            })
        return web.json_response({"success": False, "message": result.message or "Неверный логин или пароль"})

    # Success — get or create user
    login_cookies = result.cookies or {}
    user, token = await _get_or_create_user(login, login_cookies)

    return web.json_response({
        "success": True,
        "token": token,
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "mirea_login": user.mirea_login,
        },
    })


# ---------------------------------------------------------------------------
# POST /api/auth/2fa — submit OTP code
# ---------------------------------------------------------------------------


async def handle_2fa(request: web.Request) -> web.Response:
    """Submit 2FA code to complete login."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    state = (data.get("state") or "").strip()
    code = (data.get("code") or "").strip()
    if not state or not code:
        return web.json_response({"success": False, "message": "Введите код подтверждения"}, status=400)

    _purge_pending_2fa()
    pending = _PENDING_2FA.get(state)
    if not pending:
        return web.json_response(
            {"success": False, "message": "Сессия истекла. Войдите заново."},
            status=400,
        )

    async with pending.lock:
        if pending.attempts >= _PENDING_2FA_MAX_ATTEMPTS:
            _PENDING_2FA.pop(state, None)
            return web.json_response(
                {"success": False, "message": "Слишком много попыток. Войдите заново."},
                status=400,
            )

        pending.attempts += 1

        challenge = AuthChallenge(
            kind="otp",
            action_url=pending.action_url,
            field_name=pending.field_name,
            hidden_fields=pending.hidden_fields or {},
            referer=pending.referer,
            pkce_verifier=pending.pkce_verifier,
            redirect_uri=pending.redirect_uri,
        )

        auth = MireaAuth()
        try:
            result = await auth.submit_otp(challenge, code, cookies=pending.cookies or {})
        finally:
            await auth.close()

        if not result.success:
            retry_kind = getattr(result.challenge, "kind", None) if result.challenge else None
            if retry_kind in ("otp", "email_code"):
                pending.cookies = result.cookies or pending.cookies
                pending.action_url = result.challenge.action_url
                pending.field_name = result.challenge.field_name
                pending.hidden_fields = result.challenge.hidden_fields or {}
                pending.referer = result.challenge.referer
                pending.pkce_verifier = getattr(result.challenge, "pkce_verifier", pending.pkce_verifier)
                pending.redirect_uri = getattr(result.challenge, "redirect_uri", pending.redirect_uri)

            resp: dict = {
                "success": False,
                "needs_2fa": True,
                "state": state,
                "message": result.message or "Неверный код",
            }
            if retry_kind:
                resp["challenge_kind"] = retry_kind
            return web.json_response(resp)

        mirea_login = pending.mirea_login
        otp_cookies = result.cookies or {}

    # Success
    user, token = await _get_or_create_user(mirea_login, otp_cookies)
    _PENDING_2FA.pop(state, None)

    return web.json_response({
        "success": True,
        "token": token,
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "mirea_login": user.mirea_login,
        },
    })


# ---------------------------------------------------------------------------
# MIREA connection (for re-linking from profile)
# ---------------------------------------------------------------------------


async def handle_mirea_connect(request: web.Request) -> web.Response:
    """Connect/reconnect MIREA account."""
    user, session = await require_user(request)
    try:
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"success": False, "message": "Invalid JSON"}, status=400)

        login = (data.get("login") or "").strip()
        password = data.get("password") or ""
        if not login or not password:
            return web.json_response({"success": False, "message": "Введите логин и пароль МИРЭА"}, status=400)

        auth = MireaAuth()
        try:
            result = await auth.login(login, password)
        finally:
            await auth.close()

        if not result.success:
            return web.json_response({"success": False, "message": result.message or "Ошибка авторизации"})

        login_cookies = result.cookies or {}
        display_name, email = _extract_from_token(login_cookies)
        login_cookies["__token_refreshed_at"] = int(time_module.time())
        crypto = get_crypto()
        encrypted_session = crypto.encrypt_session(login_cookies)

        user.mirea_session = encrypted_session
        user.mirea_login = login
        user.last_mirea_sync_at = datetime.utcnow()
        if email:
            user.email = email
        await session.commit()

        return web.json_response({"success": True, "message": "МИРЭА подключён"})
    except Exception as e:
        logger.error("MIREA connect error: %s", e, exc_info=True)
        return web.json_response({"success": False, "message": "Внутренняя ошибка"}, status=500)
    finally:
        await session.close()


async def handle_mirea_disconnect(request: web.Request) -> web.Response:
    """Disconnect MIREA account."""
    user, session = await require_user(request)
    try:
        user.mirea_session = None
        user.mirea_login = None
        await session.commit()
        return web.json_response({"success": True, "message": "МИРЭА отключён"})
    finally:
        await session.close()
