"""API-эндпоинты для бронирования киберзоны МИРЭА."""
from __future__ import annotations

import logging

from aiohttp import web
from sqlalchemy import select

from backend.api.common import require_user
from backend.database import async_session
from backend.database.models import User
from backend.services.crypto import get_crypto
from backend.services.mirea_esports import EsportsTokens, MireaEsports

logger = logging.getLogger(__name__)


def _get_esports_tokens(user: User) -> EsportsTokens | None:
    """Расшифровать esports-сессию пользователя."""
    if not user.esports_session:
        return None
    crypto = get_crypto()
    data = crypto.decrypt_session(user.esports_session)
    if not data:
        return None
    access = data.get("access_token")
    refresh = data.get("refresh_token")
    if access and refresh:
        return EsportsTokens(access_token=access, refresh_token=refresh)
    return None


async def _save_esports_tokens(user_id: int, tokens: EsportsTokens) -> None:
    """Сохранить esports JWT в БД (зашифрованно)."""
    crypto = get_crypto()
    encrypted = crypto.encrypt_session({
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
    })
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.esports_session = encrypted
            await session.commit()


async def _clear_esports_tokens(user_id: int) -> None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.esports_session = None
            await session.commit()


async def _get_token_or_refresh(user: User) -> str | None:
    """Получить access_token, при необходимости обновить через refresh."""
    tokens = _get_esports_tokens(user)
    if not tokens:
        return None
    return tokens.access_token


async def _try_refresh_and_retry(
    user: User,
    user_id: int,
    result: dict | None,
) -> tuple[str | None, bool]:
    """Если result содержит _unauthorized, пробуем refresh. Возвращает (new_token, refreshed)."""
    if not result or not result.get("_unauthorized"):
        return None, False

    tokens = _get_esports_tokens(user)
    if not tokens:
        return None, False

    esports = MireaEsports()
    try:
        new_tokens = await esports.refresh_tokens(tokens.refresh_token)
    finally:
        await esports.close()

    if not new_tokens:
        await _clear_esports_tokens(user_id)
        return None, False

    await _save_esports_tokens(user_id, new_tokens)
    return new_tokens.access_token, True


# ── Handlers ─────────────────────────────────────────────────────────


async def handle_esports_status(request: web.Request) -> web.Response:
    """Проверить, есть ли esports-сессия."""
    user, session = await require_user(request)
    await session.close()

    has_session = bool(_get_esports_tokens(user))
    return web.json_response({"success": True, "authorized": has_session})


async def handle_esports_login(request: web.Request) -> web.Response:
    """Авторизация в киберзоне через МИРЭА-аккаунт."""
    user, session = await require_user(request)
    await session.close()

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "message": "Invalid JSON"}, status=400)

    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    if not email or not password:
        return web.json_response({"success": False, "message": "Email и пароль обязательны"}, status=400)

    esports = MireaEsports()
    try:
        result = await esports.login(email, password)
    finally:
        await esports.close()

    if result.success and result.tokens:
        await _save_esports_tokens(user.id, result.tokens)
        return web.json_response({"success": True, "message": result.message})

    return web.json_response({"success": False, "message": result.message})


async def handle_esports_logout(request: web.Request) -> web.Response:
    """Выйти из киберзоны."""
    user, session = await require_user(request)
    await session.close()

    await _clear_esports_tokens(user.id)
    return web.json_response({"success": True, "message": "Сессия киберзоны удалена"})


async def handle_esports_config(request: web.Request) -> web.Response:
    """Получить категории устройств для бронирования."""
    user, session = await require_user(request)
    await session.close()

    token = await _get_token_or_refresh(user)
    if not token:
        return web.json_response({"success": False, "message": "Не авторизован в киберзоне"}, status=401)

    esports = MireaEsports()
    try:
        data = await esports.get_configuration(token)
        if data and data.get("_unauthorized"):
            new_token, refreshed = await _try_refresh_and_retry(user, user.id, data)
            if refreshed and new_token:
                data = await esports.get_configuration(new_token)
            else:
                return web.json_response({"success": False, "message": "Сессия киберзоны истекла"}, status=401)
    finally:
        await esports.close()

    if not data or data.get("_unauthorized"):
        return web.json_response({"success": False, "message": "Не удалось получить данные"})

    return web.json_response({"success": True, "data": data})


async def handle_esports_slots(request: web.Request) -> web.Response:
    """Получить свободные слоты."""
    user, session = await require_user(request)
    await session.close()

    date = request.query.get("date", "")
    duration = request.query.get("duration", "")
    start_time = request.query.get("start_time", "")
    category = request.query.get("category", "all")

    if not date or not duration or not start_time:
        return web.json_response(
            {"success": False, "message": "date, duration, start_time обязательны"}, status=400
        )

    try:
        duration_int = int(duration)
    except ValueError:
        return web.json_response({"success": False, "message": "duration должен быть числом"}, status=400)

    token = await _get_token_or_refresh(user)
    if not token:
        return web.json_response({"success": False, "message": "Не авторизован в киберзоне"}, status=401)

    esports = MireaEsports()
    try:
        data = await esports.get_slots(
            token, date=date, duration=duration_int, start_time=start_time, category=category
        )
        if data and data.get("_unauthorized"):
            new_token, refreshed = await _try_refresh_and_retry(user, user.id, data)
            if refreshed and new_token:
                data = await esports.get_slots(
                    new_token, date=date, duration=duration_int, start_time=start_time, category=category
                )
            else:
                return web.json_response({"success": False, "message": "Сессия киберзоны истекла"}, status=401)
    finally:
        await esports.close()

    if not data or data.get("_unauthorized"):
        return web.json_response({"success": False, "message": "Не удалось получить слоты"})

    return web.json_response({"success": True, "data": data})


async def handle_esports_book(request: web.Request) -> web.Response:
    """Создать бронирование."""
    user, session = await require_user(request)
    await session.close()

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"success": False, "message": "Invalid JSON"}, status=400)

    device_id = body.get("device_id")
    booking_datetime = body.get("booking_datetime", "")
    booking_duration = body.get("booking_duration")

    if not all([device_id, booking_datetime, booking_duration]):
        return web.json_response(
            {"success": False, "message": "device_id, booking_datetime, booking_duration обязательны"},
            status=400,
        )

    try:
        booking_duration_int = int(booking_duration)
    except (ValueError, TypeError):
        return web.json_response({"success": False, "message": "booking_duration должен быть числом"}, status=400)

    token = await _get_token_or_refresh(user)
    if not token:
        return web.json_response({"success": False, "message": "Не авторизован в киберзоне"}, status=401)

    esports = MireaEsports()
    try:
        data = await esports.create_booking(
            token,
            device_id=device_id,
            booking_datetime=booking_datetime,
            booking_duration=booking_duration_int,
        )
        if data and data.get("_unauthorized"):
            new_token, refreshed = await _try_refresh_and_retry(user, user.id, data)
            if refreshed and new_token:
                data = await esports.create_booking(
                    new_token,
                    device_id=device_id,
                    booking_datetime=booking_datetime,
                    booking_duration=booking_duration_int,
                )
            else:
                return web.json_response({"success": False, "message": "Сессия киберзоны истекла"}, status=401)
    finally:
        await esports.close()

    if not data or data.get("_unauthorized"):
        return web.json_response({"success": False, "message": "Не удалось создать бронирование"})

    if "detail" in data:
        return web.json_response({"success": False, "message": data["detail"]})

    return web.json_response({"success": True, "data": data})


async def handle_esports_bookings(request: web.Request) -> web.Response:
    """Мои бронирования."""
    user, session = await require_user(request)
    await session.close()

    token = await _get_token_or_refresh(user)
    if not token:
        return web.json_response({"success": False, "message": "Не авторизован в киберзоне"}, status=401)

    esports = MireaEsports()
    try:
        data = await esports.get_my_bookings(token)
        if data and data.get("_unauthorized"):
            new_token, refreshed = await _try_refresh_and_retry(user, user.id, data)
            if refreshed and new_token:
                data = await esports.get_my_bookings(new_token)
            else:
                return web.json_response({"success": False, "message": "Сессия киберзоны истекла"}, status=401)
    finally:
        await esports.close()

    if not data or data.get("_unauthorized"):
        return web.json_response({"success": False, "message": "Не удалось получить бронирования"})

    return web.json_response({"success": True, "data": data})


async def handle_esports_cancel(request: web.Request) -> web.Response:
    """Отменить бронирование."""
    user, session = await require_user(request)
    await session.close()

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"success": False, "message": "Invalid JSON"}, status=400)

    booking_id = body.get("booking_id")
    if not booking_id:
        return web.json_response({"success": False, "message": "booking_id обязателен"}, status=400)

    token = await _get_token_or_refresh(user)
    if not token:
        return web.json_response({"success": False, "message": "Не авторизован в киберзоне"}, status=401)

    esports = MireaEsports()
    try:
        data = await esports.cancel_booking(token, booking_id=booking_id)
        if data and data.get("_unauthorized"):
            new_token, refreshed = await _try_refresh_and_retry(user, user.id, data)
            if refreshed and new_token:
                data = await esports.cancel_booking(new_token, booking_id=booking_id)
            else:
                return web.json_response({"success": False, "message": "Сессия киберзоны истекла"}, status=401)
    finally:
        await esports.close()

    if not data or data.get("_unauthorized"):
        return web.json_response({"success": False, "message": "Не удалось отменить бронирование"})

    return web.json_response({"success": True, "data": data})
