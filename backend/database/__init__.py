from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from backend.config import settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs() -> dict:
    if settings.database_url.startswith("sqlite"):
        return {}
    workers = max(1, int(getattr(settings, "worker_count", 1)))
    pool_size = max(5, 20 // workers)
    max_overflow = max(10, 40 // workers)
    return {"pool_size": pool_size, "max_overflow": max_overflow}


engine = create_async_engine(settings.database_url, echo=False, **_engine_kwargs())
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
