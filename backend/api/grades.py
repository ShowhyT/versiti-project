from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from aiohttp import web

from backend.api.common import persist_session_if_current, require_user
from backend.config import settings
from backend.services.crypto import get_crypto
from backend.services.mirea_grades import MireaGrades
from backend.utils.rate_limiter import grades_limiter

logger = logging.getLogger(__name__)

# In-memory grades cache: user_id -> (expire_ts, json_dict)
_grades_cache: dict[int, tuple[float, dict]] = {}
_GRADES_CACHE_TTL = 300  # 5 minutes


async def handle_get_grades(request: web.Request) -> web.Response:
    """Получить оценки из БРС."""

    user, session = await require_user(request)
    try:
        if not settings.feature_grades_enabled:
            return web.json_response(
                {"success": False, "message": "БРС временно отключён. Попробуйте позже."},
                status=503,
            )

        is_allowed, retry_after = await grades_limiter.is_allowed(str(user.id))
        if not is_allowed:
            return web.json_response(
                {"success": False, "message": f"Слишком много запросов. Попробуй через {retry_after} сек."},
                status=429,
            )

        if not user.mirea_session:
            return web.json_response(
                {"success": False, "message": "Требуется авторизация", "needs_auth": True},
            )

        # Check cache (skip with ?refresh=1)
        force_refresh = request.rel_url.query.get("refresh") == "1"
        cached = _grades_cache.get(user.id)
        if cached and not force_refresh:
            expire_ts, cached_resp = cached
            if time.time() < expire_ts:
                logger.info("Grades cache hit for user=%s", user.id)
                return web.json_response(cached_resp)

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
            return web.json_response({"success": False, "message": "Ошибка сессии. Перелогинься."})

        has_token = "access_token" in cookies
        has_aspnet = ".AspNetCore.Cookies" in cookies
        has_pw = "__pw_state__" in cookies
        logger.info("Grades request: user=%s, token=%s, aspnet=%s, pw_state=%s", user.id, has_token, has_aspnet, has_pw)
        logger.info("Cookie keys: %s", list(cookies.keys()))

        cookies_before = dict(cookies)

        grades_service = MireaGrades(cookies)
        result = await grades_service.get_grades()
        await grades_service.close()

        logger.info("Grades result: success=%s, message=%s", result.success, result.message)

        needs_commit = False
        if result.success:
            user.last_mirea_sync_at = datetime.utcnow()
            needs_commit = True
        if cookies != cookies_before:
            updated_session = crypto.encrypt_session(cookies)
            session_saved = await persist_session_if_current(
                session,
                user_id=user.id,
                previous_session=session_blob_for_update,
                updated_session=updated_session,
            )
            if session_saved:
                needs_commit = True
                logger.info("Persisted updated MIREA session into user session")

        if needs_commit:
            try:
                await session.commit()
            except Exception:
                try:
                    await session.rollback()
                except Exception:
                    pass

        if result.success and result.subjects:
            resp_data = {
                "success": True,
                "subjects": [
                    {
                        "name": s.name,
                        "discipline_id": getattr(s, "discipline_id", None),
                        "current_control": s.current_control,
                        "semester_control": s.semester_control,
                        "attendance": s.attendance,
                        "attendance_max_possible": getattr(s, "attendance_max_possible", None),
                        "achievements": getattr(s, "achievements", 0.0),
                        "additional": getattr(s, "additional", 0.0),
                        "total": s.total,
                    }
                    for s in result.subjects
                ],
                "semester": result.semester,
            }
            _grades_cache[user.id] = (time.time() + _GRADES_CACHE_TTL, resp_data)
            return web.json_response(resp_data)

        return web.json_response({"success": False, "message": result.message})
    finally:
        await session.close()
