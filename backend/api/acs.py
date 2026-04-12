from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiohttp import web

logger = logging.getLogger(__name__)

from backend.api.common import persist_session_if_current, require_user
from backend.config import settings
from backend.services.crypto import get_crypto
from backend.services.mirea_acs import MireaACS


async def handle_get_acs_events(request: web.Request) -> web.Response:
    """Получить события пропуска (ACS) за текущий день."""

    user, session = await require_user(request)
    try:
        if not settings.feature_acs_enabled:
            return web.json_response(
                {"success": False, "message": "Раздел пропусков временно отключён. Попробуйте позже."},
                status=503,
            )

        if not user.mirea_session:
            return web.json_response({"success": False, "message": "Требуется авторизация", "needs_auth": True})

        crypto = get_crypto()
        stored_session = user.mirea_session
        cookies, rotated_session = crypto.decrypt_session_for_db(stored_session)
        session_blob_for_update = stored_session
        if rotated_session and rotated_session != stored_session:
            try:
                rotated_saved = await persist_session_if_current(
                    session,
                    user_id=user.id,
                    previous_session=stored_session,
                    updated_session=rotated_session,
                )
                if rotated_saved:
                    session_blob_for_update = rotated_session
                    await session.commit()
            except Exception:
                try:
                    await session.rollback()
                except Exception:
                    pass

        if not cookies:
            logger.warning("acs session decryption failed user_id=%d", user.id)
            return web.json_response({"success": False, "message": "Ошибка сессии. Перелогинься."})

        cookies_before = dict(cookies)
        acs_service = MireaACS(cookies)
        acs_result = await acs_service.get_today_events()
        await acs_service.close()

        if not acs_result.success:
            logger.warning("acs fetch failed user_id=%d: %s", user.id, acs_result.message)
            return web.json_response({"success": False, "message": acs_result.message})

        try:
            if cookies != cookies_before:
                updated_session = crypto.encrypt_session(cookies)
                await persist_session_if_current(
                    session,
                    user_id=user.id,
                    previous_session=session_blob_for_update,
                    updated_session=updated_session,
                )
            user.last_mirea_sync_at = datetime.utcnow()
            await session.commit()
        except Exception:
            try:
                await session.rollback()
            except Exception:
                pass

        return web.json_response(
            {
                "success": True,
                "date": acs_result.date,
                "events": [
                    {
                        "ts": e.ts,
                        "time": e.time_label,
                        "enter_zone": e.enter_zone,
                        "exit_zone": e.exit_zone,
                        "duration_seconds": e.duration_seconds,
                        "duration": e.duration_label,
                    }
                    for e in acs_result.events
                ],
            }
        )
    finally:
        await session.close()
