"""Tests for database functionality."""

import json
from datetime import date
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from lse.config import Settings
from lse.database import DatabaseManager, create_database_manager


@pytest_asyncio.fixture
async def test_settings() -> Settings:
    """Create test database settings."""
    return Settings(
        database_url="postgresql+asyncpg://lse_user:lse_password@localhost:5432/langsmith_extractor",
        database_pool_size=5,
        database_pool_timeout=10,
        database_echo=True,  # Enable SQL logging for debugging
    )


@pytest_asyncio.fixture
async def db_manager(test_settings: Settings) -> AsyncGenerator[DatabaseManager, None]:
    """Create a test database manager."""
    manager = DatabaseManager(test_settings)

    # The runs table should already exist from Alembic migrations
    # Clean up any existing test data before running tests
    async with manager.get_session() as session:
        await session.execute(text("DELETE FROM runs WHERE run_id LIKE 'test-%'"))

    yield manager

    # Cleanup test data after running tests
    async with manager.get_session() as session:
        await session.execute(text("DELETE FROM runs WHERE run_id LIKE 'test-%'"))
    
    await manager.close()


class TestDatabaseManager:
    """Test DatabaseManager functionality."""

    async def test_database_manager_initialization(self, test_settings: Settings):
        """Test DatabaseManager can be initialized."""
        manager = DatabaseManager(test_settings)
        assert manager.settings == test_settings
        assert manager.engine is not None
        assert manager.session_factory is not None
        await manager.close()

    async def test_get_session_context_manager(self, db_manager: DatabaseManager):
        """Test getting database session."""
        async with db_manager.get_session() as session:
            assert isinstance(session, AsyncSession)
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    async def test_health_check_success(self, db_manager: DatabaseManager):
        """Test database health check succeeds."""
        is_healthy = await db_manager.health_check()
        assert is_healthy is True

    async def test_health_check_failure(self, test_settings: Settings):
        """Test database health check fails with invalid connection."""
        # Use invalid database URL (wrong port)
        bad_settings = Settings(
            database_url="postgresql+asyncpg://lse_user:lse_password@localhost:9999/langsmith_extractor",
            database_pool_size=1,
        )
        manager = DatabaseManager(bad_settings)

        is_healthy = await manager.health_check()
        assert is_healthy is False

        await manager.close()

    async def test_execute_raw_sql(self, db_manager: DatabaseManager):
        """Test executing raw SQL queries."""
        result = await db_manager.execute_raw_sql("SELECT 42 as answer")
        assert len(result) == 1
        assert result[0][0] == 42

    async def test_execute_raw_sql_with_parameters(self, db_manager: DatabaseManager):
        """Test executing raw SQL with parameters."""
        result = await db_manager.execute_raw_sql("SELECT :value as answer", {"value": "test_param"})
        assert len(result) == 1
        assert result[0][0] == "test_param"

    async def test_session_transaction_commit(self, db_manager: DatabaseManager):
        """Test session automatically commits on success."""
        test_run = {
            "run_id": "test-run-123",
            "trace_id": "test-trace-123", 
            "project": "test-project",
            "run_date": date(2024, 1, 1),
            "data": json.dumps({
                "run_id": "test-run-123",
                "trace_id": "test-trace-123",
                "project": "test-project", 
                "run_date": "2024-01-01",
                "test": "data"
            }),
        }

        # Insert test data
        async with db_manager.get_session() as session:
            await session.execute(
                text("""
                INSERT INTO runs (run_id, trace_id, project, run_date, data)
                VALUES (:run_id, :trace_id, :project, :run_date, :data)
            """),
                test_run,
            )

        # Verify data was committed
        result = await db_manager.execute_raw_sql(
            "SELECT run_id FROM runs WHERE run_id = :run_id", {"run_id": "test-run-123"}
        )
        assert len(result) == 1
        assert result[0][0] == "test-run-123"

    async def test_session_transaction_rollback(self, db_manager: DatabaseManager):
        """Test session automatically rolls back on exception."""
        try:
            async with db_manager.get_session() as session:
                await session.execute(text("""
                    INSERT INTO runs (run_id, trace_id, project, run_date, data)
                    VALUES ('test-rollback', 'test-trace-123', 'test-project', '2024-01-01', '{}')
                """))
                # Force an exception
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected

        # Verify data was rolled back
        result = await db_manager.execute_raw_sql(
            "SELECT run_id FROM runs WHERE run_id = 'test-rollback'"
        )
        assert len(result) == 0

    async def test_repr(self, test_settings: Settings):
        """Test DatabaseManager string representation."""
        manager = DatabaseManager(test_settings)
        repr_str = repr(manager)
        assert "DatabaseManager" in repr_str
        assert test_settings.database_url in repr_str
        assert str(test_settings.database_pool_size) in repr_str
        await manager.close()


class TestDatabaseManagerFactory:
    """Test database manager factory functions."""

    async def test_create_database_manager_with_settings(self, test_settings: Settings):
        """Test creating database manager with provided settings."""
        manager = await create_database_manager(test_settings)
        assert manager.settings == test_settings
        await manager.close()

    async def test_create_database_manager_without_settings(self):
        """Test creating database manager with default settings."""
        manager = await create_database_manager()
        assert manager.settings is not None
        await manager.close()


class TestRunsTableOperations:
    """Test operations specific to the runs table schema."""

    async def test_insert_run_data(self, db_manager: DatabaseManager):
        """Test inserting run data into the runs table."""
        run_data = {
            "run_id": "test-run-456",
            "trace_id": "test-trace-456",
            "project": "test-project",
            "run_date": date(2024, 1, 15),
            "data": json.dumps(
                {
                    "run_id": "test-run-456",
                    "trace_id": "test-trace-456",
                    "project": "test-project",
                    "run_date": "2024-01-15",
                    "run_type": "llm",
                    "status": "success",
                    "duration": 1.5,
                    "tokens": {"input": 100, "output": 50},
                }
            ),
        }

        async with db_manager.get_session() as session:
            await session.execute(
                text("""
                INSERT INTO runs (run_id, trace_id, project, run_date, data)
                VALUES (:run_id, :trace_id, :project, :run_date, :data)
            """),
                run_data,
            )

        # Verify insertion
        result = await db_manager.execute_raw_sql(
            "SELECT run_id, trace_id, project, data FROM runs WHERE run_id = :run_id",
            {"run_id": "test-run-456"},
        )
        assert len(result) == 1
        row = result[0]
        assert row[0] == "test-run-456"
        assert row[1] == "test-trace-456"
        assert row[2] == "test-project"

        # Verify JSONB data
        stored_data = row[3]  # JSONB comes back as dict
        if isinstance(stored_data, str):
            stored_data = json.loads(stored_data)
        assert stored_data["run_id"] == "test-run-456"
        assert stored_data["status"] == "success"

    async def test_query_runs_by_trace_id(self, db_manager: DatabaseManager):
        """Test querying runs by trace_id to reconstruct a trace."""
        trace_id = "test-trace-789"

        # Insert multiple runs for the same trace
        runs = [
            {
                "run_id": f"{trace_id}",  # Root run has run_id == trace_id
                "trace_id": trace_id,
                "project": "test-project",
                "run_date": date(2024, 1, 20),
                "data": json.dumps(
                    {
                        "run_id": trace_id,
                        "trace_id": trace_id,
                        "project": "test-project",
                        "run_date": "2024-01-20",
                        "run_type": "chain",
                        "parent_id": None,
                    }
                ),
            },
            {
                "run_id": "test-run-789-child-1",
                "trace_id": trace_id,
                "project": "test-project",
                "run_date": date(2024, 1, 20),
                "data": json.dumps(
                    {
                        "run_id": "test-run-789-child-1",
                        "trace_id": trace_id,
                        "project": "test-project", 
                        "run_date": "2024-01-20",
                        "run_type": "llm",
                        "parent_id": trace_id,
                    }
                ),
            },
            {
                "run_id": "test-run-789-child-2",
                "trace_id": trace_id,
                "project": "test-project",
                "run_date": date(2024, 1, 20),
                "data": json.dumps(
                    {
                        "run_id": "test-run-789-child-2",
                        "trace_id": trace_id,
                        "project": "test-project",
                        "run_date": "2024-01-20", 
                        "run_type": "tool",
                        "parent_id": trace_id,
                    }
                ),
            },
        ]

        # Insert all runs
        for run in runs:
            async with db_manager.get_session() as session:
                await session.execute(
                    text("""
                    INSERT INTO runs (run_id, trace_id, project, run_date, data)
                    VALUES (:run_id, :trace_id, :project, :run_date, :data)
                """),
                    run,
                )

        # Query all runs for the trace
        result = await db_manager.execute_raw_sql(
            """
            SELECT run_id, data FROM runs 
            WHERE trace_id = :trace_id 
            ORDER BY run_id
        """,
            {"trace_id": trace_id},
        )

        assert len(result) == 3

        # Verify we can reconstruct the trace structure
        trace_runs = {}
        for row in result:
            run_data = row[1]  # JSONB comes back as dict
            if isinstance(run_data, str):
                run_data = json.loads(run_data)
            trace_runs[row[0]] = run_data

        # Root run
        assert trace_id in trace_runs
        assert trace_runs[trace_id]["parent_id"] is None

        # Child runs
        assert "test-run-789-child-1" in trace_runs
        assert trace_runs["test-run-789-child-1"]["parent_id"] == trace_id
        assert "test-run-789-child-2" in trace_runs
        assert trace_runs["test-run-789-child-2"]["parent_id"] == trace_id

    async def test_query_runs_by_project_and_date(self, db_manager: DatabaseManager):
        """Test querying runs by project and date range."""
        project_name = "test-analytics-project"
        target_date = date(2024, 2, 1)

        run_data = {
            "run_id": "test-analytics-run-1",
            "trace_id": "test-analytics-trace-1",
            "project": project_name,
            "run_date": target_date,
            "data": json.dumps(
                {"run_id": "test-analytics-run-1", "project": project_name, "run_date": "2024-02-01"}
            ),
        }

        async with db_manager.get_session() as session:
            await session.execute(
                text("""
                INSERT INTO runs (run_id, trace_id, project, run_date, data)
                VALUES (:run_id, :trace_id, :project, :run_date, :data)
            """),
                run_data,
            )

        # Query by project and date
        result = await db_manager.execute_raw_sql(
            """
            SELECT run_id FROM runs 
            WHERE project = :project AND run_date = :run_date
        """,
            {"project": project_name, "run_date": target_date},
        )

        assert len(result) == 1
        assert result[0][0] == "test-analytics-run-1"


class TestDatabaseIntegration:
    """Test database integration with application components."""

    async def test_database_manager_with_real_langsmith_data_structure(
        self, db_manager: DatabaseManager
    ):
        """Test database operations with realistic LangSmith run data structure."""
        # Simulate real LangSmith run data
        langsmith_run_data = {
            "run_id": "test-ls-run-123",
            "trace_id": "test-ls-trace-123", 
            "project": "test-customer-support-bot",
            "run_date": date(2024, 3, 1),
            "data": json.dumps(
                {
                    "id": "test-ls-run-123",
                    "name": "ChatOpenAI",
                    "run_type": "llm",
                    "start_time": "2024-03-01T10:30:00Z",
                    "end_time": "2024-03-01T10:30:02.5Z",
                    "extra": {"invocation_params": {"model": "gpt-4", "temperature": 0.7}},
                    "inputs": {
                        "messages": [{"role": "user", "content": "How can I reset my password?"}]
                    },
                    "outputs": {
                        "generations": [
                            {
                                "text": "To reset your password, go to...",
                                "message": {
                                    "role": "assistant",
                                    "content": "To reset your password, go to...",
                                },
                            }
                        ]
                    },
                    "session_id": "session-456",
                    "trace_id": "test-ls-trace-123",
                    "dotted_order": "20240301T103000000000Z.test-ls-run-123",
                }
            ),
        }

        # Insert LangSmith-style run data
        async with db_manager.get_session() as session:
            await session.execute(
                text("""
                INSERT INTO runs (run_id, trace_id, project, run_date, data)
                VALUES (:run_id, :trace_id, :project, :run_date, :data)
            """),
                langsmith_run_data,
            )

        # Query and verify complex nested data
        result = await db_manager.execute_raw_sql(
            """
            SELECT data FROM runs WHERE run_id = :run_id
        """,
            {"run_id": "test-ls-run-123"},
        )

        assert len(result) == 1
        stored_data = result[0][0]  # JSONB comes back as dict
        if isinstance(stored_data, str):
            stored_data = json.loads(stored_data)

        # Verify nested structure is preserved
        assert stored_data["run_type"] == "llm"
        assert stored_data["extra"]["invocation_params"]["model"] == "gpt-4"
        assert stored_data["inputs"]["messages"][0]["content"] == "How can I reset my password?"
        assert "To reset your password" in stored_data["outputs"]["generations"][0]["text"]
