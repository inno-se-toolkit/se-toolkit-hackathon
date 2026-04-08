# Database engine and session

from sqlmodel import SQLModel, create_engine, Session
from .settings import settings

DATABASE_URL = settings.database_url or (
    f"postgresql+asyncpg://{settings.postgres_user}:"
    f"{settings.postgres_password}@{settings.postgres_host}:"
    f"{settings.postgres_port}/{settings.postgres_db}"
)

# Async engine for FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
async_engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,
    future=True,
)

# Sync engine for migrations/init if needed
engine = create_engine(
    DATABASE_URL.replace("asyncpg", "psycopg2"),
    echo=settings.debug,
)

def get_session() -> AsyncSession:
    return AsyncSession(async_engine)

async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
