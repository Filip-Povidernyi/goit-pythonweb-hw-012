import contextlib

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)


"""Database session manager for handling async database sessions."""

from src.conf.config import config


class DatabaseSessionManager:
    """Manages database sessions for asynchronous operations."""

    def __init__(self, url: str):
        self._engine: AsyncEngine | None = create_async_engine(url, echo=True)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise  # Re-raise the original error
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(config.DB_URL)


async def get_db():
    """Dependency to get a database session."""
    """Provides a database session for the request."""
    async with sessionmanager.session() as session:
        yield session
