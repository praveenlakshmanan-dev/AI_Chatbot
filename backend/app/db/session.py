from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base

engine = create_async_engine(settings.DATABASE_URL, future=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255)"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255)"))
        await conn.execute(text("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL"))
        await conn.execute(text("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS thread_id UUID"))
        await conn.execute(
            text(
                "DO $$ "
                "BEGIN "
                "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chat_messages_thread_id_fkey') THEN "
                "ALTER TABLE chat_messages "
                "ADD CONSTRAINT chat_messages_thread_id_fkey "
                "FOREIGN KEY (thread_id) REFERENCES chat_threads(id) ON DELETE SET NULL; "
                "END IF; "
                "END $$;"
            )
        )
