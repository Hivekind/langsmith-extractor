"""Database connection and management for LangSmith Extractor."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from lse.config import Settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions for async operations."""

    def __init__(self, settings: Settings):
        """Initialize database manager with settings.

        Args:
            settings: Application settings containing database configuration
        """
        self.settings = settings

        # Create async engine with connection pooling
        self.engine = create_async_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            pool_timeout=settings.database_pool_timeout,
            pool_pre_ping=True,  # Validate connections before use
            echo=settings.database_echo,  # Log SQL queries if enabled
            # Use NullPool for testing to avoid connection issues
            poolclass=NullPool if "test" in settings.database_url else None,
        )

        # Create async session factory
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Allow access to objects after commit
        )

        logger.info(f"Database manager initialized with pool_size={settings.database_pool_size}")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session with automatic transaction management.

        Yields:
            AsyncSession: Database session with automatic commit/rollback

        Example:
            async with db_manager.get_session() as session:
                result = await session.execute("SELECT 1")
                # Automatic commit on success, rollback on exception
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def health_check(self) -> bool:
        """Check if database connection is healthy.

        Returns:
            bool: True if database is accessible, False otherwise
        """
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close database engine and clean up connections.

        Should be called when shutting down the application.
        """
        try:
            await self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")

    async def execute_raw_sql(self, sql: str, parameters: Optional[dict] = None) -> list:
        """Execute raw SQL query and return results.

        Args:
            sql: SQL query string
            parameters: Optional parameters for the query

        Returns:
            list: Query results

        Note:
            Use this sparingly - prefer using the ORM when possible
        """
        async with self.get_session() as session:
            result = await session.execute(text(sql), parameters or {})
            return result.fetchall()

    def __repr__(self) -> str:
        """String representation of DatabaseManager."""
        return f"DatabaseManager(url='{self.settings.database_url}', pool_size={self.settings.database_pool_size})"


async def create_database_manager(settings: Optional[Settings] = None) -> DatabaseManager:
    """Create and return a DatabaseManager instance.

    Args:
        settings: Optional settings instance. If None, will create new settings.

    Returns:
        DatabaseManager: Configured database manager
    """
    if settings is None:
        from lse.config import get_settings

        settings = get_settings()

    manager = DatabaseManager(settings)

    # Perform initial health check
    if not await manager.health_check():
        logger.warning("Database health check failed on initialization")

    return manager


# Convenience function for getting a database manager
async def get_database_manager() -> DatabaseManager:
    """Get a database manager instance with default settings.

    Returns:
        DatabaseManager: Database manager with default configuration
    """
    from lse.config import get_settings

    return await create_database_manager(get_settings())
