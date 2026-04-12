from datetime import datetime
from sqlalchemy import Boolean, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    apple_sub: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)

    # Данные авторизации МИРЭА (зашифрованные)
    mirea_session: Mapped[str | None] = mapped_column(Text, nullable=True)
    mirea_login: Mapped[str | None] = mapped_column(String(255), nullable=True)
    share_mirea_login: Mapped[bool] = mapped_column(Boolean, default=False)
    # Время последней подтвержденной успешной синхронизации с сервисами МИРЭА.
    last_mirea_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Esports (киберзона) JWT-сессия (зашифрованная)
    esports_session: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Профиль
    avatar_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Роли
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    # Персональные настройки поведения в мини-приложении.
    mark_with_friends_default: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_select_favorites: Mapped[bool] = mapped_column(Boolean, default=True)
    haptics_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    light_theme_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    theme_mode: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    visible_tabs: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)

    # Конфиденциальность
    profile_visibility: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    messaging_privacy: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)

    # Premium
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_tier: Mapped[int] = mapped_column(Integer, default=0)  # 0=free, 1=plus, 2=max
    premium_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    display_username: Mapped[str | None] = mapped_column(String(255), nullable=True)

    password_changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    sessions_revoked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Friend(Base):
    """Связь друзей для совместной отметки (макс 20 человек)"""
    __tablename__ = "friends"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Кто отправил запрос
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # Кому отправлен запрос
    friend_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # Статус: pending, accepted, rejected
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # Избранный друг (автоматически включается при отметке)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Связи
    user: Mapped["User"] = relationship(foreign_keys=[user_id], backref="sent_friend_requests")
    friend: Mapped["User"] = relationship(foreign_keys=[friend_id], backref="received_friend_requests")


class AttendanceLog(Base):
    """Лог отметок посещаемости"""
    __tablename__ = "attendance_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    qr_data: Mapped[str] = mapped_column(Text)  # Данные из QR-кода
    success: Mapped[bool] = mapped_column(default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
