from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


@dataclass(frozen=True)
class Migration:
    """Single DB migration, applied once and recorded in schema_migrations."""

    id: str
    description: str
    apply: Callable[[AsyncConnection], Awaitable[None]]


async def _apply_baseline(_conn: AsyncConnection) -> None:
    return


async def _apply_social_core(conn: AsyncConnection) -> None:
    stmts = [
        """CREATE TABLE IF NOT EXISTS posts (
            id          BIGSERIAL PRIMARY KEY,
            author_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            text        TEXT NOT NULL DEFAULT '',
            visibility  VARCHAR(20) NOT NULL DEFAULT 'public',
            has_poll    BOOLEAN NOT NULL DEFAULT FALSE,
            is_deleted  BOOLEAN NOT NULL DEFAULT FALSE,
            created_at  TIMESTAMP NOT NULL DEFAULT now(),
            updated_at  TIMESTAMP NOT NULL DEFAULT now()
        )""",
        "CREATE INDEX IF NOT EXISTS ix_posts_author_id ON posts(author_id)",
        "CREATE INDEX IF NOT EXISTS ix_posts_feed ON posts(created_at DESC) WHERE is_deleted = FALSE",
        """CREATE TABLE IF NOT EXISTS post_images (
            id         BIGSERIAL PRIMARY KEY,
            post_id    BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            path       VARCHAR(512) NOT NULL,
            thumb_path VARCHAR(512),
            width      SMALLINT,
            height     SMALLINT,
            size_bytes INTEGER,
            position   SMALLINT NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )""",
        "CREATE INDEX IF NOT EXISTS ix_post_images_post_id ON post_images(post_id)",
        """CREATE TABLE IF NOT EXISTS reactions (
            id         BIGSERIAL PRIMARY KEY,
            post_id    BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            emoji      VARCHAR(32) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            UNIQUE(post_id, user_id, emoji)
        )""",
        "CREATE INDEX IF NOT EXISTS ix_reactions_post_id ON reactions(post_id)",
        "CREATE INDEX IF NOT EXISTS ix_reactions_user_id ON reactions(user_id)",
        """CREATE TABLE IF NOT EXISTS comments (
            id         BIGSERIAL PRIMARY KEY,
            post_id    BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            author_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            parent_id  BIGINT REFERENCES comments(id) ON DELETE CASCADE,
            text       TEXT NOT NULL,
            is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )""",
        "CREATE INDEX IF NOT EXISTS ix_comments_post_id ON comments(post_id, created_at)",
        "CREATE INDEX IF NOT EXISTS ix_comments_author_id ON comments(author_id)",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_social_polls(conn: AsyncConnection) -> None:
    stmts = [
        """CREATE TABLE IF NOT EXISTS polls (
            id          BIGSERIAL PRIMARY KEY,
            post_id     BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE UNIQUE,
            question    TEXT NOT NULL,
            is_multiple BOOLEAN NOT NULL DEFAULT FALSE,
            is_closed   BOOLEAN NOT NULL DEFAULT FALSE,
            created_at  TIMESTAMP NOT NULL DEFAULT now()
        )""",
        "CREATE INDEX IF NOT EXISTS ix_polls_post_id ON polls(post_id)",
        """CREATE TABLE IF NOT EXISTS poll_options (
            id       BIGSERIAL PRIMARY KEY,
            poll_id  BIGINT NOT NULL REFERENCES polls(id) ON DELETE CASCADE,
            text     VARCHAR(300) NOT NULL,
            position SMALLINT NOT NULL DEFAULT 0
        )""",
        "CREATE INDEX IF NOT EXISTS ix_poll_options_poll_id ON poll_options(poll_id)",
        """CREATE TABLE IF NOT EXISTS poll_votes (
            id         BIGSERIAL PRIMARY KEY,
            option_id  BIGINT NOT NULL REFERENCES poll_options(id) ON DELETE CASCADE,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            UNIQUE(option_id, user_id)
        )""",
        "CREATE INDEX IF NOT EXISTS ix_poll_votes_option_id ON poll_votes(option_id)",
        "CREATE INDEX IF NOT EXISTS ix_poll_votes_user_id ON poll_votes(user_id)",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_notifications(conn: AsyncConnection) -> None:
    stmts = [
        """CREATE TABLE IF NOT EXISTS notifications (
            id          BIGSERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            type        VARCHAR(50) NOT NULL,
            payload     TEXT NOT NULL DEFAULT '{}',
            is_read     BOOLEAN NOT NULL DEFAULT FALSE,
            created_at  TIMESTAMP NOT NULL DEFAULT now()
        )""",
        "CREATE INDEX IF NOT EXISTS ix_notifications_user_unread ON notifications(user_id, created_at DESC) WHERE is_read = FALSE",
        "CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications(user_id, created_at DESC)",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_messenger(conn: AsyncConnection) -> None:
    stmts = [
        """CREATE TABLE IF NOT EXISTS conversations (
            id                BIGSERIAL PRIMARY KEY,
            user1_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            user2_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            last_message_text VARCHAR(200),
            last_message_at   TIMESTAMP,
            created_at        TIMESTAMP NOT NULL DEFAULT now(),
            UNIQUE(user1_id, user2_id)
        )""",
        "CREATE INDEX IF NOT EXISTS ix_conversations_user1 ON conversations(user1_id)",
        "CREATE INDEX IF NOT EXISTS ix_conversations_user2 ON conversations(user2_id)",
        """CREATE TABLE IF NOT EXISTS messages (
            id              BIGSERIAL PRIMARY KEY,
            conversation_id BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            sender_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            text            TEXT NOT NULL,
            is_read         BOOLEAN NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMP NOT NULL DEFAULT now()
        )""",
        "CREATE INDEX IF NOT EXISTS ix_messages_conv_created ON messages(conversation_id, created_at DESC)",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_reports(conn: AsyncConnection) -> None:
    stmts = [
        """CREATE TABLE IF NOT EXISTS reports (
            id          BIGSERIAL PRIMARY KEY,
            reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_type VARCHAR(20) NOT NULL,
            target_id   BIGINT NOT NULL,
            reason      VARCHAR(500) NOT NULL DEFAULT '',
            created_at  TIMESTAMP NOT NULL DEFAULT now(),
            UNIQUE(reporter_id, target_type, target_id)
        )""",
        "CREATE INDEX IF NOT EXISTS ix_reports_reporter ON reports(reporter_id)",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_phase6(conn: AsyncConnection) -> None:
    stmts = [
        # User: avatar, bio, admin, banned
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_path VARCHAR(512)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio VARCHAR(500)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_banned BOOLEAN NOT NULL DEFAULT FALSE",
        # Report: status + resolution
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'open'",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS resolved_by INTEGER REFERENCES users(id)",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS resolution_note VARCHAR(500)",
        "CREATE INDEX IF NOT EXISTS ix_reports_status ON reports(status) WHERE status = 'open'",
        # Search: pg_trgm indexes
        "CREATE EXTENSION IF NOT EXISTS pg_trgm",
        "CREATE INDEX IF NOT EXISTS ix_posts_text_trgm ON posts USING gin (text gin_trgm_ops)",
        "CREATE INDEX IF NOT EXISTS ix_users_username_trgm ON users USING gin (username gin_trgm_ops)",
        "CREATE INDEX IF NOT EXISTS ix_users_full_name_trgm ON users USING gin (full_name gin_trgm_ops)",
        "CREATE INDEX IF NOT EXISTS ix_user_aliases_username_trgm ON user_aliases USING gin (username gin_trgm_ops)",
        # Push subscriptions
        """CREATE TABLE IF NOT EXISTS push_subscriptions (
            id          BIGSERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            endpoint    TEXT NOT NULL UNIQUE,
            p256dh      TEXT NOT NULL,
            auth        TEXT NOT NULL,
            created_at  TIMESTAMP NOT NULL DEFAULT now()
        )""",
        "CREATE INDEX IF NOT EXISTS ix_push_subs_user ON push_subscriptions(user_id)",
        # Set initial admin
        "UPDATE users SET is_admin = TRUE WHERE username = 'one'",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_messenger_v2(conn: AsyncConnection) -> None:
    stmts = [
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS edited_at TIMESTAMP",
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS forward_sender_name VARCHAR(100)",
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS forward_text TEXT",
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS attachment_type VARCHAR(10)",
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS attachment_path VARCHAR(512)",
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS attachment_thumb_path VARCHAR(512)",
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS deleted_for_sender BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS deleted_for_recipient BOOLEAN NOT NULL DEFAULT FALSE",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_single_reaction(conn: AsyncConnection) -> None:
    """Keep only the latest reaction per user per post, then enforce unique(post_id, user_id)."""
    stmts = [
        # Delete duplicates keeping the most recent one
        """DELETE FROM reactions WHERE id NOT IN (
            SELECT DISTINCT ON (post_id, user_id) id
            FROM reactions ORDER BY post_id, user_id, created_at DESC
        )""",
        # Drop old constraint and add new one
        "ALTER TABLE reactions DROP CONSTRAINT IF EXISTS reactions_post_id_user_id_emoji_key",
        "ALTER TABLE reactions ADD CONSTRAINT reactions_post_id_user_id_key UNIQUE (post_id, user_id)",
    ]
    for s in stmts:
        await conn.execute(text(s))


async def _apply_post_views(conn: AsyncConnection) -> None:
    stmts = [
        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS view_count INTEGER NOT NULL DEFAULT 0",
        """CREATE TABLE IF NOT EXISTS post_views (
            id         BIGSERIAL PRIMARY KEY,
            post_id    BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            UNIQUE(post_id, user_id)
        )""",
        "CREATE INDEX IF NOT EXISTS ix_post_views_post_id ON post_views(post_id)",
        "CREATE INDEX IF NOT EXISTS ix_post_views_user_id ON post_views(user_id)",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_comment_images(conn: AsyncConnection) -> None:
    stmts = [
        "ALTER TABLE comments ADD COLUMN IF NOT EXISTS image_path VARCHAR(512)",
        "ALTER TABLE comments ADD COLUMN IF NOT EXISTS image_thumb_path VARCHAR(512)",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_privacy_settings(conn: AsyncConnection) -> None:
    stmts = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_visibility VARCHAR(20) DEFAULT 'public'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS messaging_privacy VARCHAR(20) DEFAULT 'friends_only'",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_pinned_posts(conn: AsyncConnection) -> None:
    stmts = [
        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS pinned_at TIMESTAMP",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_user_email(conn: AsyncConnection) -> None:
    stmts = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email) WHERE email IS NOT NULL",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_conversation_sender_id(conn: AsyncConnection) -> None:
    stmts = [
        "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS last_message_sender_id INTEGER",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_voice_media(conn: AsyncConnection) -> None:
    stmts = [
        "ALTER TABLE messages ALTER COLUMN attachment_type TYPE VARCHAR(20)",
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS duration REAL",
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS waveform BYTEA",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_apns_device_tokens(conn: AsyncConnection) -> None:
    stmts = [
        """CREATE TABLE IF NOT EXISTS apns_device_tokens (
            id          BIGSERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            device_token TEXT NOT NULL UNIQUE,
            created_at  TIMESTAMP NOT NULL DEFAULT now()
        )""",
        "CREATE INDEX IF NOT EXISTS ix_apns_tokens_user ON apns_device_tokens(user_id)",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_user_blocks(conn: AsyncConnection) -> None:
    stmts = [
        """CREATE TABLE IF NOT EXISTS user_blocks (
            id          BIGSERIAL PRIMARY KEY,
            blocker_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            blocked_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at  TIMESTAMP NOT NULL DEFAULT now(),
            UNIQUE(blocker_id, blocked_id)
        )""",
        "CREATE INDEX IF NOT EXISTS ix_user_blocks_blocker ON user_blocks(blocker_id)",
        "CREATE INDEX IF NOT EXISTS ix_user_blocks_blocked ON user_blocks(blocked_id)",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_voip_push_tokens(conn: AsyncConnection) -> None:
    stmts = [
        "ALTER TABLE apns_device_tokens ADD COLUMN IF NOT EXISTS platform TEXT NOT NULL DEFAULT 'ios'",
        "ALTER TABLE apns_device_tokens DROP CONSTRAINT IF EXISTS apns_device_tokens_device_token_key",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_apns_tokens_token_platform ON apns_device_tokens(device_token, platform)",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))


async def _apply_voice_video(conn: AsyncConnection) -> None:
    await conn.execute(text(
        "ALTER TABLE voice_participants ADD COLUMN IF NOT EXISTS is_video_on BOOLEAN NOT NULL DEFAULT FALSE"
    ))


async def _apply_group_modules(conn: AsyncConnection) -> None:
    stmts = [
        # Module flags on groups
        "ALTER TABLE groups ADD COLUMN IF NOT EXISTS posts_enabled BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE groups ADD COLUMN IF NOT EXISTS channels_enabled BOOLEAN NOT NULL DEFAULT FALSE",
        # Group posts (broadcast)
        """CREATE TABLE IF NOT EXISTS group_posts (
            id          BIGSERIAL PRIMARY KEY,
            group_id    BIGINT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
            author_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            text        TEXT NOT NULL DEFAULT '',
            is_pinned   BOOLEAN NOT NULL DEFAULT FALSE,
            view_count  INTEGER NOT NULL DEFAULT 0,
            created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMP
        )""",
        "CREATE INDEX IF NOT EXISTS ix_group_posts_group ON group_posts (group_id, created_at DESC)",
        """CREATE TABLE IF NOT EXISTS group_post_images (
            id          BIGSERIAL PRIMARY KEY,
            post_id     BIGINT NOT NULL REFERENCES group_posts(id) ON DELETE CASCADE,
            url         TEXT NOT NULL,
            thumb_url   TEXT,
            width       INTEGER,
            height      INTEGER
        )""",
        """CREATE TABLE IF NOT EXISTS group_post_reactions (
            post_id     BIGINT NOT NULL REFERENCES group_posts(id) ON DELETE CASCADE,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            emoji       VARCHAR(50) NOT NULL,
            created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE (post_id, user_id, emoji)
        )""",
        """CREATE TABLE IF NOT EXISTS group_post_comments (
            id          BIGSERIAL PRIMARY KEY,
            post_id     BIGINT NOT NULL REFERENCES group_posts(id) ON DELETE CASCADE,
            author_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            text        TEXT NOT NULL,
            parent_id   BIGINT REFERENCES group_post_comments(id) ON DELETE CASCADE,
            created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMP
        )""",
        "CREATE INDEX IF NOT EXISTS ix_group_post_comments ON group_post_comments (post_id, created_at)",
        """CREATE TABLE IF NOT EXISTS group_post_views (
            post_id     BIGINT NOT NULL REFERENCES group_posts(id) ON DELETE CASCADE,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            PRIMARY KEY (post_id, user_id)
        )""",
        # Sub-channels
        """CREATE TABLE IF NOT EXISTS group_channels (
            id          BIGSERIAL PRIMARY KEY,
            group_id    BIGINT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
            name        VARCHAR(100) NOT NULL,
            type        VARCHAR(10) NOT NULL DEFAULT 'text',
            position    INTEGER NOT NULL DEFAULT 0,
            admin_only  BOOLEAN NOT NULL DEFAULT FALSE,
            created_at  TIMESTAMP NOT NULL DEFAULT NOW()
        )""",
        "CREATE INDEX IF NOT EXISTS ix_group_channels_group ON group_channels (group_id, position)",
        """CREATE TABLE IF NOT EXISTS group_channel_messages (
            id              BIGSERIAL PRIMARY KEY,
            channel_id      BIGINT NOT NULL REFERENCES group_channels(id) ON DELETE CASCADE,
            sender_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            text            TEXT NOT NULL DEFAULT '',
            reply_to_id     BIGINT,
            attachment_type VARCHAR(20),
            attachment_path TEXT,
            attachment_thumb_path TEXT,
            duration        REAL,
            waveform        BYTEA,
            file_name       TEXT,
            file_size       BIGINT,
            created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
            edited_at       TIMESTAMP
        )""",
        "CREATE INDEX IF NOT EXISTS ix_gcm_channel ON group_channel_messages (channel_id, created_at DESC)",
    ]
    for stmt in stmts:
        await conn.execute(text(stmt))



def get_migrations() -> list[Migration]:
    return [
        Migration(
            id="20260228_0001_baseline",
            description="baseline (stamp initial schema)",
            apply=_apply_baseline,
        ),
        Migration(
            id="20260301_0002_social_posts_comments_reactions",
            description="Add posts, post_images, comments, reactions tables",
            apply=_apply_social_core,
        ),
        Migration(
            id="20260302_0003_social_polls",
            description="Add polls, poll_options, poll_votes tables",
            apply=_apply_social_polls,
        ),
        Migration(
            id="20260302_0004_notifications",
            description="Add notifications table",
            apply=_apply_notifications,
        ),
        Migration(
            id="20260228_0005_messenger",
            description="Add conversations and messages tables",
            apply=_apply_messenger,
        ),
        Migration(
            id="20260228_0006_reports",
            description="Add reports table for moderation",
            apply=_apply_reports,
        ),
        Migration(
            id="20260301_0007_phase6",
            description="Profiles, search, admin, push notifications",
            apply=_apply_phase6,
        ),
        Migration(
            id="20260301_0008_messenger_v2",
            description="Messenger: edit, forward, attachments, soft-delete",
            apply=_apply_messenger_v2,
        ),
        Migration(
            id="20260301_0009_single_reaction",
            description="One reaction per user per post",
            apply=_apply_single_reaction,
        ),
        Migration(
            id="20260301_0010_post_views",
            description="Add unique post views tracking",
            apply=_apply_post_views,
        ),
        Migration(
            id="20260301_0011_privacy_settings",
            description="Add profile_visibility and messaging_privacy columns",
            apply=_apply_privacy_settings,
        ),
        Migration(
            id="20260301_0012_comment_images",
            description="Add optional image attachment to comments",
            apply=_apply_comment_images,
        ),
        Migration(
            id="20260302_0013_pinned_posts",
            description="Add is_pinned and pinned_at to posts",
            apply=_apply_pinned_posts,
        ),
        Migration(
            id="20260302_0014_user_email",
            description="Add email and email_verified columns to users",
            apply=_apply_user_email,
        ),
        Migration(
            id="20260303_0015_conversation_sender_id",
            description="Add last_message_sender_id to conversations",
            apply=_apply_conversation_sender_id,
        ),
        Migration(
            id="20260308_0016_voice_media",
            description="Widen attachment_type, add duration and waveform for voice/video messages",
            apply=_apply_voice_media,
        ),
        Migration(
            id="20260312_0017_apns_device_tokens",
            description="Add APNs device tokens table for iOS push notifications",
            apply=_apply_apns_device_tokens,
        ),
        Migration(
            id="20260312_0018_user_blocks",
            description="Add user_blocks table for user blocking",
            apply=_apply_user_blocks,
        ),
        Migration(
            id="20260316_0019_voip_push_tokens",
            description="Add platform column to apns_device_tokens for VoIP push support",
            apply=_apply_voip_push_tokens,
        ),
        Migration(
            id="20260316_0020_voice_video",
            description="Add is_video_on column to voice_participants",
            apply=_apply_voice_video,
        ),
        Migration(
            id="20260408_0021_group_modules",
            description="Add group posts, sub-channels, module flags",
            apply=_apply_group_modules,
        ),
    ]
