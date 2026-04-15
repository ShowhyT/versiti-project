from __future__ import annotations

from aiohttp import web

from backend.api.acs import handle_get_acs_events
from backend.api.attendance import handle_mark_attendance
from backend.api.auth import (
    handle_login,
    handle_2fa,
    handle_mirea_connect,
    handle_mirea_disconnect,
)
from backend.api.friends import (
    handle_get_friends,
    handle_search_users,
    handle_send_friend_request,
    handle_respond_friend_request,
    handle_remove_friend,
    handle_toggle_favorite,
)
from backend.api.esports import (
    handle_esports_book,
    handle_esports_bookings,
    handle_esports_cancel,
    handle_esports_config,
    handle_esports_login,
    handle_esports_logout,
    handle_esports_slots,
    handle_esports_status,
)
from backend.api.attendance_detail import handle_get_attendance_detail
from backend.api.grades import handle_get_grades
from backend.api.health import handle_health, handle_health_details
from backend.api.profile import handle_get_profile, handle_update_profile, handle_logout, handle_profile_connection_check
from backend.api.schedule import (
    handle_get_pulse_schedule,
    handle_get_schedule,
    handle_search_classrooms,
    handle_search_groups,
    handle_search_teachers,
)


def setup_routes(app: web.Application):
    """University-specific routes (MIREA). Social endpoints served by Rust."""

    app.router.add_get("/api/health", handle_health)
    app.router.add_get("/api/health/details", handle_health_details)
    app.router.add_post("/api/attendance/mark", handle_mark_attendance)

    app.router.add_get("/api/profile", handle_get_profile)
    app.router.add_patch("/api/profile", handle_update_profile)
    app.router.add_post("/api/profile/check-connection", handle_profile_connection_check)
    app.router.add_post("/api/auth/logout", handle_logout)

    app.router.add_post("/api/auth/login", handle_login)
    app.router.add_post("/api/auth/2fa", handle_2fa)
    app.router.add_post("/api/auth/mirea-connect", handle_mirea_connect)
    app.router.add_post("/api/auth/mirea-disconnect", handle_mirea_disconnect)

    app.router.add_get("/api/friends", handle_get_friends)
    app.router.add_get("/api/friends/search", handle_search_users)
    app.router.add_post("/api/friends/request", handle_send_friend_request)
    app.router.add_post("/api/friends/respond", handle_respond_friend_request)
    app.router.add_post("/api/friends/remove", handle_remove_friend)
    app.router.add_post("/api/friends/favorite", handle_toggle_favorite)

    app.router.add_get("/api/grades", handle_get_grades)
    app.router.add_get("/api/attendance/detail", handle_get_attendance_detail)

    app.router.add_get("/api/schedule", handle_get_schedule)
    app.router.add_get("/api/schedule/pulse", handle_get_pulse_schedule)
    app.router.add_get("/api/groups/search", handle_search_groups)
    app.router.add_get("/api/teachers/search", handle_search_teachers)
    app.router.add_get("/api/classrooms/search", handle_search_classrooms)

    app.router.add_get("/api/acs/events", handle_get_acs_events)

    app.router.add_get("/api/esports/status", handle_esports_status)
    app.router.add_post("/api/esports/login", handle_esports_login)
    app.router.add_post("/api/esports/logout", handle_esports_logout)
    app.router.add_get("/api/esports/config", handle_esports_config)
    app.router.add_get("/api/esports/slots", handle_esports_slots)
    app.router.add_post("/api/esports/book", handle_esports_book)
    app.router.add_get("/api/esports/bookings", handle_esports_bookings)
    app.router.add_post("/api/esports/cancel", handle_esports_cancel)
