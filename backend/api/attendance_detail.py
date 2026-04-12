from __future__ import annotations

import logging

from aiohttp import web

from backend.api.common import persist_session_if_current, require_user
from backend.config import settings
from backend.services.crypto import get_crypto
from backend.services.mirea_grades import MireaGrades
from backend.utils.rate_limiter import attendance_detail_limiter

logger = logging.getLogger(__name__)


async def handle_get_attendance_detail(request: web.Request) -> web.Response:
    """Per-lesson attendance detail for a discipline."""

    user, session = await require_user(request)
    try:
        if not settings.feature_grades_enabled:
            return web.json_response(
                {"success": False, "message": "Временно недоступно."},
                status=503,
            )

        discipline_id = request.query.get("discipline_id", "").strip()
        semester = request.query.get("semester", "").strip() or None
        if not discipline_id:
            return web.json_response(
                {"success": False, "message": "discipline_id is required"}, status=400
            )

        is_allowed, retry_after = await attendance_detail_limiter.is_allowed(str(user.id))
        if not is_allowed:
            return web.json_response(
                {"success": False, "message": f"Слишком много запросов. Попробуй через {retry_after} сек."},
                status=429,
            )

        if not user.mirea_session:
            return web.json_response(
                {"success": False, "message": "Требуется авторизация", "needs_auth": True},
            )

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

        cookies_before = dict(cookies)

        grades_service = MireaGrades(cookies)
        detail = await grades_service.get_attendance_detail(
            discipline_id=discipline_id,
            visiting_log_id=semester,
        )
        await grades_service.close()

        if cookies != cookies_before:
            updated_session = crypto.encrypt_session(cookies)
            saved = await persist_session_if_current(
                session,
                user_id=user.id,
                previous_session=session_blob_for_update,
                updated_session=updated_session,
            )
            if saved:
                try:
                    await session.commit()
                except Exception:
                    try:
                        await session.rollback()
                    except Exception:
                        pass

        if detail.success:
            return web.json_response({
                "success": True,
                "summary": {
                    "total": detail.summary.total_lessons if detail.summary else 0,
                    "present": detail.summary.present if detail.summary else 0,
                    "excused": detail.summary.excused if detail.summary else 0,
                    "absent": detail.summary.absent if detail.summary else 0,
                },
                "entries": [
                    {
                        "lesson_start": e.lesson_start,
                        "attend_type": e.attend_type,
                    }
                    for e in (detail.entries or [])
                ],
            })

        return web.json_response({"success": False, "message": detail.message})
    finally:
        await session.close()
