#!/bin/bash

# Database Setup Script for LangSmith Extractor
# This script sets up the local development database infrastructure

set -e  # Exit on any error

echo "🗄️  LangSmith Extractor Database Setup"
echo "=================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker compose is available (try modern syntax first, then legacy)
if ! docker compose version >/dev/null 2>&1; then
    if ! command -v docker-compose >/dev/null 2>&1; then
        echo "❌ Docker Compose is not available. Please install Docker Compose and try again."
        echo "   Modern Docker installations include Compose as 'docker compose'"
        echo "   Legacy installations use 'docker-compose'"
        exit 1
    else
        DOCKER_COMPOSE="docker-compose"
    fi
else
    DOCKER_COMPOSE="docker compose"
fi

echo "🔧 Using: $DOCKER_COMPOSE"

# Function to wait for database to be ready
wait_for_db() {
    echo "⏳ Waiting for database to be ready..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker exec lse_postgres pg_isready -U lse_user -d langsmith_extractor >/dev/null 2>&1; then
            echo "✅ Database is ready!"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo "   Attempt $attempt/$max_attempts..."
        sleep 2
    done
    
    echo "❌ Database failed to start within expected time"
    return 1
}

# Start Docker Compose services
echo "🚀 Starting PostgreSQL database..."
$DOCKER_COMPOSE up -d postgres

# Wait for database to be ready
if ! wait_for_db; then
    echo "❌ Failed to start database. Check Docker logs:"
    $DOCKER_COMPOSE logs postgres
    exit 1
fi

# Check if uv is available
if ! command -v uv >/dev/null 2>&1; then
    echo "❌ uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
uv sync

# Run database migrations
echo "🔄 Running database migrations..."
uv run alembic upgrade head

# Verify setup
echo "🔍 Verifying database setup..."
if uv run python -c "
import asyncio
from lse.database import get_database_manager

async def test_connection():
    manager = await get_database_manager()
    is_healthy = await manager.health_check()
    await manager.close()
    return is_healthy

result = asyncio.run(test_connection())
print('✅ Database connection successful!' if result else '❌ Database connection failed!')
exit(0 if result else 1)
"; then
    echo ""
    echo "🎉 Database setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "   • Database is running at: postgresql://lse_user:lse_password@localhost:5432/langsmith_extractor"
    echo "   • Run tests: uv run pytest tests/test_database.py -v"
    echo "   • Stop database: $DOCKER_COMPOSE down"
    echo "   • View logs: $DOCKER_COMPOSE logs postgres"
    echo ""
    echo "🔧 Development commands:"
    echo "   • Create migration: uv run alembic revision --autogenerate -m 'Description'"
    echo "   • Apply migrations: uv run alembic upgrade head"
    echo "   • Rollback migration: uv run alembic downgrade -1"
    echo ""
else
    echo "❌ Database setup verification failed!"
    exit 1
fi