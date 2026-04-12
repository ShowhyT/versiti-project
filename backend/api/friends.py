from __future__ import annotations

import logging

from aiohttp import web
from sqlalchemy import select, or_, and_, func

from backend.api.common import require_user
from backend.database import async_session
from backend.database.models import User, Friend

logger = logging.getLogger(__name__)

MAX_FRIENDS = 30


async def handle_get_friends(request: web.Request) -> web.Response:
    """Get current user's friends list."""
    user, session = await require_user(request)
    try:
        # Friends where I sent request
        sent = await session.execute(
            select(Friend, User)
            .join(User, Friend.friend_id == User.id)
            .where(Friend.user_id == user.id)
        )
        # Friends where I received request
        received = await session.execute(
            select(Friend, User)
            .join(User, Friend.user_id == User.id)
            .where(Friend.friend_id == user.id)
        )

        friends = []
        pending_incoming = []
        pending_outgoing = []

        for fr, u in sent.all():
            item = {
                "id": fr.id,
                "user_id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "is_favorite": fr.is_favorite,
            }
            if fr.status == "accepted":
                friends.append(item)
            elif fr.status == "pending":
                pending_outgoing.append(item)

        for fr, u in received.all():
            item = {
                "id": fr.id,
                "user_id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "is_favorite": fr.is_favorite,
            }
            if fr.status == "accepted":
                friends.append(item)
            elif fr.status == "pending":
                pending_incoming.append(item)

        return web.json_response({
            "success": True,
            "friends": friends,
            "pending_incoming": pending_incoming,
            "pending_outgoing": pending_outgoing,
            "max_friends": MAX_FRIENDS,
        })
    finally:
        await session.close()


async def handle_search_users(request: web.Request) -> web.Response:
    """Search users by university email."""
    user, session = await require_user(request)
    try:
        q = (request.query.get("q") or "").strip().lower()
        if len(q) < 3:
            return web.json_response({"success": True, "users": []})

        result = await session.execute(
            select(User)
            .where(
                User.id != user.id,
                or_(
                    func.lower(User.email).contains(q),
                    func.lower(User.full_name).contains(q),
                ),
            )
            .limit(20)
        )
        users = [
            {
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
            }
            for u in result.scalars().all()
        ]
        return web.json_response({"success": True, "users": users})
    finally:
        await session.close()


async def handle_send_friend_request(request: web.Request) -> web.Response:
    """Send friend request by user email."""
    user, session = await require_user(request)
    try:
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"success": False, "message": "Invalid JSON"}, status=400)

        email = (data.get("email") or "").strip().lower()
        target_id = data.get("user_id")

        if not email and not target_id:
            return web.json_response({"success": False, "message": "Укажите email или user_id"}, status=400)

        # Find target user
        if target_id:
            result = await session.execute(select(User).where(User.id == int(target_id)))
        else:
            result = await session.execute(select(User).where(func.lower(User.email) == email))
        target = result.scalar_one_or_none()

        if not target:
            return web.json_response({"success": False, "message": "Пользователь не найден"})
        if target.id == user.id:
            return web.json_response({"success": False, "message": "Нельзя добавить себя"})

        # Check existing relationship
        existing = await session.execute(
            select(Friend).where(
                or_(
                    and_(Friend.user_id == user.id, Friend.friend_id == target.id),
                    and_(Friend.user_id == target.id, Friend.friend_id == user.id),
                )
            )
        )
        fr = existing.scalar_one_or_none()
        if fr:
            if fr.status == "accepted":
                return web.json_response({"success": False, "message": "Уже в друзьях"})
            if fr.status == "pending":
                return web.json_response({"success": False, "message": "Запрос уже отправлен"})

        # Check limit
        count_q = await session.execute(
            select(func.count(Friend.id)).where(
                or_(Friend.user_id == user.id, Friend.friend_id == user.id),
                Friend.status == "accepted",
            )
        )
        if count_q.scalar() >= MAX_FRIENDS:
            return web.json_response({"success": False, "message": f"Достигнут лимит друзей ({MAX_FRIENDS})"})

        friend = Friend(user_id=user.id, friend_id=target.id, status="pending")
        session.add(friend)
        await session.commit()

        return web.json_response({"success": True, "message": "Запрос отправлен"})
    except Exception as e:
        logger.error("send friend request error: %s", e, exc_info=True)
        return web.json_response({"success": False, "message": "Внутренняя ошибка"}, status=500)
    finally:
        await session.close()


async def handle_respond_friend_request(request: web.Request) -> web.Response:
    """Accept or reject friend request."""
    user, session = await require_user(request)
    try:
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"success": False, "message": "Invalid JSON"}, status=400)

        friend_request_id = data.get("id")
        action = (data.get("action") or "").strip()

        if not friend_request_id or action not in ("accept", "reject"):
            return web.json_response({"success": False, "message": "Укажите id и action (accept/reject)"}, status=400)

        result = await session.execute(
            select(Friend).where(
                Friend.id == int(friend_request_id),
                Friend.friend_id == user.id,
                Friend.status == "pending",
            )
        )
        fr = result.scalar_one_or_none()
        if not fr:
            return web.json_response({"success": False, "message": "Запрос не найден"})

        if action == "accept":
            fr.status = "accepted"
            await session.commit()
            return web.json_response({"success": True, "message": "Друг добавлен"})
        else:
            await session.delete(fr)
            await session.commit()
            return web.json_response({"success": True, "message": "Запрос отклонён"})
    except Exception as e:
        logger.error("respond friend request error: %s", e, exc_info=True)
        return web.json_response({"success": False, "message": "Внутренняя ошибка"}, status=500)
    finally:
        await session.close()


async def handle_remove_friend(request: web.Request) -> web.Response:
    """Remove friend."""
    user, session = await require_user(request)
    try:
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"success": False, "message": "Invalid JSON"}, status=400)

        friend_id = data.get("user_id")
        if not friend_id:
            return web.json_response({"success": False, "message": "Укажите user_id"}, status=400)

        result = await session.execute(
            select(Friend).where(
                or_(
                    and_(Friend.user_id == user.id, Friend.friend_id == int(friend_id)),
                    and_(Friend.user_id == int(friend_id), Friend.friend_id == user.id),
                ),
            )
        )
        fr = result.scalar_one_or_none()
        if fr:
            await session.delete(fr)
            await session.commit()

        return web.json_response({"success": True, "message": "Друг удалён"})
    except Exception as e:
        logger.error("remove friend error: %s", e, exc_info=True)
        return web.json_response({"success": False, "message": "Внутренняя ошибка"}, status=500)
    finally:
        await session.close()
