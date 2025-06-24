from contextlib import asynccontextmanager

from config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = str(settings.DATABASE_URL).replace(
    "postgresql", "postgresql+asyncpg", 1
)

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False, future=True)

SessionLocal = sessionmaker(
    engine, class_=AsyncSession, autocommit=False, autoflush=False
)

Base = declarative_base()


async def get_db_session():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncSession:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()
