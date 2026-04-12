from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiohttp import web

from backend.api.common import iso_utc, persist_session_if_current, require_user
from backend.services.crypto import get_crypto
from backend.services.mirea_acs import MireaACS

logger = logging.getLogger(__name__)


async def handle_get_profile(request: web.Request) -> web.Response:
    """Возвращает профиль текущего пользователя."""
    user, session = await require_user(request)
    try:
        return web.json_response({
            "success": True,
            "profile": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "mirea_login": user.mirea_login,
                "mirea_connected": bool(user.mirea_session),
                "last_mirea_sync_at": iso_utc(user.last_mirea_sync_at) if user.last_mirea_sync_at else None,
                "esports_connected": bool(user.esports_session),
                "created_at": iso_utc(user.created_at) if user.created_at else None,
                "settings": {
                    "mark_with_friends_default": user.mark_with_friends_default,
                    "auto_select_favorites": user.auto_select_favorites,
                    "haptics_enabled": user.haptics_enabled,
                    "theme_mode": user.theme_mode,
                },
            },
        })
    finally:
        await session.close()


async def handle_update_profile(request: web.Request) -> web.Response:
    """Обновляет настройки профиля."""
    user, session = await require_user(request)
    try:
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"success": False, "message": "Invalid JSON"}, status=400)

        if "full_name" in data:
            name = (data["full_name"] or "").strip()
            if name:
                user.full_name = name[:100]
        if "mark_with_friends_default" in data:
            user.mark_with_friends_default = bool(data["mark_with_friends_default"])
        if "auto_select_favorites" in data:
            user.auto_select_favorites = bool(data["auto_select_favorites"])
        if "theme_mode" in data:
            user.theme_mode = data["theme_mode"]

        await session.commit()
        return web.json_response({"success": True})
    except Exception as e:
        logger.error("update profile error: %s", e, exc_info=True)
        return web.json_response({"success": False, "message": "Внутренняя ошибка"}, status=500)
    finally:
        await session.close()


async def handle_logout(request: web.Request) -> web.Response:
    """Выход — ревокейт всех сессий."""
    user, session = await require_user(request)
    try:
        user.sessions_revoked_at = datetime.now(timezone.utc)
        await session.commit()
        return web.json_response({"success": True, "message": "Вы вышли из аккаунта"})
    finally:
        await session.close()


async def handle_profile_connection_check(request: web.Request) -> web.Response:
    """Явная проверка доступности сервисов МИРЭА для текущей сессии."""

    user, session = await require_user(request)
    try:
        if not user.mirea_session:
            return web.json_response(
                {"success": False, "message": "Требуется авторизация", "needs_auth": True},
            )

        crypto = get_crypto()
        stored_session = user.mirea_session
        cookies, rotated_session = crypto.decrypt_session_for_db(stored_session)
        session_blob_for_update = stored_session
        rotated_saved = False
        if rotated_session and rotated_session != stored_session:
            rotated_saved = await persist_session_if_current(
                session,
                user_id=user.id,
                previous_session=stored_session,
                updated_session=rotated_session,
            )
            if rotated_saved:
                session_blob_for_update = rotated_session

        if not cookies:
            return web.json_response({"success": False, "message": "Ошибка сессии. Перелогинься."})

        cookies_before = dict(cookies)
        acs_service = MireaACS(cookies)
        ok, message = await acs_service.check_connection()
        await acs_service.close()

        try:
            session_changed = bool(rotated_saved)
            if cookies != cookies_before:
                updated_session = crypto.encrypt_session(cookies)
                session_changed = await persist_session_if_current(
                    session,
                    user_id=user.id,
                    previous_session=session_blob_for_update,
                    updated_session=updated_session,
                )
            if ok:
                user.last_mirea_sync_at = datetime.utcnow()
            if ok or session_changed:
                await session.commit()
        except Exception:
            try:
                await session.rollback()
            except Exception:
                pass

        return web.json_response(
            {
                "success": bool(ok),
                "message": message,
                "checked_at": iso_utc(datetime.utcnow()),
                "last_sync_at": iso_utc(user.last_mirea_sync_at) if user.last_mirea_sync_at else None,
            }
        )
    finally:
        await session.close()
