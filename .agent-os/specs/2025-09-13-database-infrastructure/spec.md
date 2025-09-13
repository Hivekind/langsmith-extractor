# Phase 8: Database Infrastructure Setup Specification

## Overview
Establish Postgres database with JSONB document storage as the foundation for migrating from file-based storage to database-driven operations. This phase creates the infrastructure needed to support all future database migration phases.

## Problem Statement
Current limitations with file-based storage:
1. **Limited Query Capabilities**: Cannot perform complex queries across trace data
2. **Single-Date Restrictions**: Difficult to analyze data across date ranges
3. **Performance Issues**: File scanning becomes slow with large datasets
4. **Data Integrity**: No enforced relationships or constraints
5. **Scalability Concerns**: File system operations don't scale well

Required database characteristics:
1. **Document Storage**: Preserve LangSmith's nested trace data model
2. **Query Performance**: Fast aggregation and filtering operations
3. **Date-Based Indexing**: Efficient date range queries for evaluations
4. **ACID Compliance**: Ensure data consistency and reliability
5. **Development Workflow**: Easy local setup and migration management

## Solution Design

### Database Technology Choice
**Postgres with JSONB** selected for:
- **Native JSON Support**: JSONB storage with full query capabilities
- **Performance**: Binary JSON format with indexing support
- **Flexibility**: Schema evolution without migrations for document structure
- **SQL Compatibility**: Standard SQL for complex queries and aggregations
- **Ecosystem**: Rich tooling and Python library support

### Database Schema

#### Core Tables
```sql
-- Primary run storage table (correctly models LangSmith's Run-based architecture)
CREATE TABLE runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(255) UNIQUE NOT NULL,
    trace_id VARCHAR(255) NOT NULL,
    project VARCHAR(255) NOT NULL,
    run_date DATE NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure consistency between table fields and JSONB data
    CONSTRAINT check_run_id_matches CHECK (data->>'run_id' = run_id),
    CONSTRAINT check_trace_id_matches CHECK (data->>'trace_id' = trace_id),
    CONSTRAINT check_project_matches CHECK (data->>'project' = project),
    CONSTRAINT check_date_matches CHECK ((data->>'run_date')::date = run_date),
    
    -- Unique constraint on run_id (LangSmith's unique identifier for each run)
    CONSTRAINT unique_run UNIQUE(run_id)
);

-- Indexes for query performance
CREATE INDEX idx_runs_project_date ON runs(project, run_date);
CREATE INDEX idx_runs_trace_id ON runs(trace_id);
CREATE INDEX idx_runs_run_date ON runs(run_date);
CREATE INDEX idx_runs_data_gin ON runs USING gin(data);

-- JSONB path indexes for common queries
CREATE INDEX idx_runs_data_name ON runs USING gin((data->'name'));
CREATE INDEX idx_runs_data_status ON runs USING gin((data->'status'));

-- Composite index for trace aggregation queries
CREATE INDEX idx_runs_trace_project_date ON runs(trace_id, project, run_date);
```

#### Schema Design Rationale

**LangSmith Data Model Correction**:
- **Run-Based Storage**: Stores individual LangSmith Runs, not aggregated Traces
- **Trace Relationships**: Multiple runs can share same trace_id (Root Run + Child Runs)
- **Root Run Identification**: Root Run has run_id = trace_id in LangSmith model

**Hybrid Table + JSONB Approach**:
- **Table Fields**: Extracted from JSONB for query performance (project, dates, IDs)
- **JSONB Data**: Complete run document as single source of truth  
- **Consistency Constraints**: Database enforces table fields match JSONB content
- **Performance**: Fast B-tree indexes on table columns, flexible GIN indexes on JSONB

**Field Definitions**:
- **run_id**: LangSmith's unique identifier for each individual run
- **trace_id**: Groups runs into traces (same trace_id = same trace)
- **project**: Project name for filtering and organization
- **run_date**: UTC date for efficient date-based queries
- **data**: Complete LangSmith run as JSONB document (authoritative source)
- **created_at**: Insertion timestamp for debugging and auditing

### Docker Infrastructure

#### Docker Compose Configuration
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16
    container_name: lse_postgres
    environment:
      POSTGRES_DB: langsmith_extractor
      POSTGRES_USER: lse_user
      POSTGRES_PASSWORD: lse_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lse_user -d langsmith_extractor"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  postgres_data:
```

#### Initialization Scripts
```sql
-- sql/init/001_create_schema.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(255) UNIQUE NOT NULL,
    trace_id VARCHAR(255) NOT NULL,
    project VARCHAR(255) NOT NULL,
    run_date DATE NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure consistency between table fields and JSONB data
    CONSTRAINT check_run_id_matches CHECK (data->>'run_id' = run_id),
    CONSTRAINT check_trace_id_matches CHECK (data->>'trace_id' = trace_id),
    CONSTRAINT check_project_matches CHECK (data->>'project' = project),
    CONSTRAINT check_date_matches CHECK ((data->>'run_date')::date = run_date),
    
    -- Unique constraint on run_id
    CONSTRAINT unique_run UNIQUE(run_id)
);

-- Create indexes for query performance
CREATE INDEX idx_runs_project_date ON runs(project, run_date);
CREATE INDEX idx_runs_trace_id ON runs(trace_id);
CREATE INDEX idx_runs_run_date ON runs(run_date);
CREATE INDEX idx_runs_data_gin ON runs USING gin(data);

-- JSONB path indexes for common queries
CREATE INDEX idx_runs_data_name ON runs USING gin((data->'name'));
CREATE INDEX idx_runs_data_status ON runs USING gin((data->'status'));

-- Composite index for trace aggregation queries
CREATE INDEX idx_runs_trace_project_date ON runs(trace_id, project, run_date);
```

### Python Integration

#### Dependencies
Add to `pyproject.toml`:
```toml
[tool.uv.dev-dependencies]
asyncpg = "^0.29.0"
sqlalchemy = "^2.0.0"
alembic = "^1.13.0"
```

#### Database Configuration
```python
# lse/config.py additions
class DatabaseSettings(BaseSettings):
    database_url: str = Field(
        default="postgresql://lse_user:lse_password@localhost:5432/langsmith_extractor",
        description="Database connection URL"
    )
    database_pool_size: int = Field(default=10, description="Connection pool size")
    database_pool_timeout: int = Field(default=30, description="Connection timeout")
    database_echo: bool = Field(default=False, description="Enable SQL query logging")

    class Config:
        env_prefix = "LSE_DB_"
```

#### Database Connection Management
```python
# lse/database.py (new file)
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator

class DatabaseManager:
    def __init__(self, database_url: str, pool_size: int = 10):
        self.engine = create_async_engine(
            database_url,
            pool_size=pool_size,
            pool_pre_ping=True,
            echo=False
        )
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
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
        try:
            async with self.get_session() as session:
                await session.execute("SELECT 1")
                return True
        except Exception:
            return False
```

### Migration Management

#### Alembic Configuration
```python
# alembic/env.py
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from lse.config import get_settings

config = context.config
settings = get_settings()

# Set database URL from settings
config.set_main_option("sqlalchemy.url", settings.database.database_url)

def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def do_run_migrations(connection: Connection) -> None:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()

    asyncio.run(run_async_migrations())
```

## Implementation Plan

### Phase 1: Docker Infrastructure (Week 1)
- [ ] Create Docker Compose configuration
- [ ] Set up Postgres 16 container
- [ ] Create initialization SQL scripts
- [ ] Configure persistent volume storage
- [ ] Add health checks and monitoring

### Phase 2: Python Integration (Week 1)
- [ ] Add database dependencies to pyproject.toml
- [ ] Create DatabaseSettings configuration class
- [ ] Implement DatabaseManager with connection pooling
- [ ] Add database health check functionality
- [ ] Create async session management

### Phase 3: Schema Management (Week 2)
- [ ] Initialize Alembic migration system
- [ ] Create initial schema migration
- [ ] Set up migration execution scripts
- [ ] Add schema validation tests
- [ ] Document migration workflow

### Phase 4: Testing & Validation (Week 2)
- [ ] Write database connectivity tests
- [ ] Create schema validation tests
- [ ] Add performance benchmarks
- [ ] Test Docker setup and teardown
- [ ] Validate JSONB operations

## Testing Strategy

### Unit Tests
```python
# tests/test_database.py
import pytest
from lse.database import DatabaseManager
from lse.config import get_settings

@pytest.fixture
async def db_manager():
    settings = get_settings()
    manager = DatabaseManager(settings.database.database_url)
    yield manager
    await manager.engine.dispose()

@pytest.mark.asyncio
async def test_database_connection(db_manager):
    health = await db_manager.health_check()
    assert health is True

@pytest.mark.asyncio
async def test_session_management(db_manager):
    async with db_manager.get_session() as session:
        result = await session.execute("SELECT 1 as test")
        row = result.fetchone()
        assert row.test == 1
```

### Integration Tests
```python
# tests/test_database_integration.py
@pytest.mark.asyncio
async def test_run_insertion(db_manager):
    sample_run = {
        "run_id": "test-run-123",
        "trace_id": "test-trace-123", 
        "project": "test-project",
        "run_date": "2025-09-13",
        "data": {
            "run_id": "test-run-123",
            "trace_id": "test-trace-123",
            "project": "test-project", 
            "run_date": "2025-09-13",
            "name": "test_run",
            "status": "success"
        }
    }
    
    async with db_manager.get_session() as session:
        await session.execute(
            "INSERT INTO runs (run_id, trace_id, project, run_date, data) VALUES (:run_id, :trace_id, :project, :run_date, :data)",
            sample_run
        )
        
        result = await session.execute(
            "SELECT data FROM runs WHERE run_id = :run_id",
            {"run_id": "test-run-123"}
        )
        row = result.fetchone()
        assert row.data["name"] == "test_run"

@pytest.mark.asyncio
async def test_trace_aggregation_query(db_manager):
    # Test querying multiple runs belonging to same trace
    async with db_manager.get_session() as session:
        result = await session.execute(
            "SELECT trace_id, COUNT(*) as run_count FROM runs WHERE trace_id = :trace_id GROUP BY trace_id",
            {"trace_id": "test-trace-123"}
        )
        row = result.fetchone()
        assert row.run_count >= 1
```

## Performance Considerations

### Indexing Strategy
- **Primary Indexes**: project, run_date, run_id, trace_id for common queries
- **JSONB Indexes**: GIN indexes for document queries within runs
- **Composite Indexes**: trace_id+project+date for trace aggregation
- **Path Indexes**: Specific JSONB paths for frequent filters (name, status)
- **Trace Aggregation**: Optimized indexes for grouping runs by trace_id

### Connection Pooling
- **Pool Size**: Start with 10 connections, tune based on usage
- **Timeout Settings**: 30-second timeout for connections
- **Health Checks**: Pre-ping connections to detect failures
- **Async Operations**: Use asyncio for non-blocking database operations

### Query Optimization
- **Prepared Statements**: Use parameterized queries for security and performance
- **Batch Operations**: Bulk inserts for large datasets
- **Transaction Management**: Minimize transaction scope for concurrency
- **Query Analysis**: Use EXPLAIN ANALYZE for query optimization

## Security Considerations

### Access Control
- **Database User**: Dedicated user with minimal required permissions
- **Connection Security**: SSL/TLS for production environments
- **Environment Variables**: Secure credential management
- **Network Isolation**: Database accessible only from application

### Data Protection
- **Input Validation**: Sanitize all database inputs
- **SQL Injection Prevention**: Use parameterized queries exclusively
- **Audit Logging**: Track data access and modifications
- **Backup Strategy**: Regular automated backups

## Deployment Considerations

### Development Environment
- **Docker Compose**: One-command setup for developers
- **Volume Persistence**: Retain data across container restarts
- **Port Configuration**: Standard Postgres port (5432)
- **Environment Variables**: Easy configuration management

### Production Environment
- **Managed Postgres**: Consider cloud-managed instances
- **High Availability**: Multi-AZ deployment for production
- **Monitoring**: Database performance and health monitoring
- **Backup Strategy**: Automated backups with point-in-time recovery

## Success Criteria

### Functional Requirements
- [ ] Postgres container starts successfully via Docker Compose
- [ ] Database schema creates without errors
- [ ] Python application connects to database
- [ ] JSONB operations work correctly (insert, query, update)
- [ ] Migration system executes successfully
- [ ] Health checks pass consistently

### Performance Requirements
- [ ] Database connection established within 5 seconds
- [ ] JSONB document insertion under 10ms per document
- [ ] Date-based queries return results within 100ms
- [ ] Concurrent connections handled without blocking
- [ ] Index queries perform within expected thresholds

### Quality Requirements
- [ ] All tests pass with 100% success rate
- [ ] Code coverage above 90% for database components
- [ ] Docker setup works on macOS, Linux, and Windows
- [ ] Documentation complete and accurate
- [ ] Migration scripts validated and tested

## Dependencies

### External Dependencies
- **Docker**: Version 20.0+ with Compose support
- **Postgres**: Version 16 with JSONB support
- **Python**: Version 3.13+ with asyncio support

### Internal Dependencies
- **Current LSE Codebase**: No breaking changes to existing functionality
- **Configuration System**: Extend existing Pydantic settings
- **Testing Framework**: Integrate with existing pytest setup

## Risks and Mitigation

### Technical Risks
- **Performance Impact**: JSONB queries may be slower than file operations
  - *Mitigation*: Comprehensive indexing and query optimization
- **Schema Evolution**: JSONB structure changes may require migrations
  - *Mitigation*: Flexible schema design and migration planning
- **Connection Management**: Database connections may become bottleneck
  - *Mitigation*: Connection pooling and async operations

### Operational Risks
- **Docker Dependencies**: Additional complexity in development setup
  - *Mitigation*: Clear documentation and automated setup scripts
- **Data Migration**: Risk of data loss during file-to-database migration
  - *Mitigation*: Parallel operation during transition phases
- **Backup and Recovery**: New backup requirements for database
  - *Mitigation*: Automated backup strategy and recovery testing

## Future Considerations

### Scalability
- **Horizontal Scaling**: Read replicas for reporting workloads
- **Partitioning**: Date-based table partitioning for large datasets
- **Caching**: Redis integration for frequently accessed data
- **Connection Pooling**: PgBouncer for connection management

### Observability
- **Query Monitoring**: Slow query logging and analysis
- **Performance Metrics**: Database performance monitoring
- **Health Checks**: Automated health monitoring and alerting
- **Audit Logging**: Comprehensive data access logging

### Integration
- **Cloud Migration**: Support for cloud database services
- **Multi-Environment**: Development, staging, production configurations
- **Backup Integration**: Cloud backup and disaster recovery
- **Monitoring Integration**: Prometheus/Grafana for database metrics