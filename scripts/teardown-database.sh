#!/bin/bash

# Database Teardown Script for LangSmith Extractor
# This script cleans up the local development database infrastructure

set -e  # Exit on any error

echo "🗑️  LangSmith Extractor Database Teardown"
echo "======================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Cannot clean up containers."
    exit 1
fi

# Check if docker compose is available (try modern syntax first, then legacy)
if ! docker compose version >/dev/null 2>&1; then
    if ! command -v docker-compose >/dev/null 2>&1; then
        echo "❌ Docker Compose is not available."
        exit 1
    else
        DOCKER_COMPOSE="docker-compose"
    fi
else
    DOCKER_COMPOSE="docker compose"
fi

echo "🔧 Using: $DOCKER_COMPOSE"

# Stop and remove containers, networks, and volumes
echo "🛑 Stopping database containers..."
$DOCKER_COMPOSE down

# Ask user if they want to remove volumes (data)
read -p "🗄️  Do you want to remove all database data? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing database volumes and data..."
    $DOCKER_COMPOSE down -v
    
    # Remove any orphaned volumes
    if docker volume ls -q -f "name=langsmith-extractor" | grep -q .; then
        echo "🧹 Cleaning up orphaned volumes..."
        docker volume rm $(docker volume ls -q -f "name=langsmith-extractor") 2>/dev/null || true
    fi
    
    echo "✅ All database data has been removed."
else
    echo "📦 Database data preserved in Docker volumes."
fi

# Clean up any dangling images
echo "🧹 Cleaning up Docker resources..."
docker system prune -f >/dev/null 2>&1 || true

echo ""
echo "🎉 Database teardown completed!"
echo ""
echo "📋 What was cleaned up:"
echo "   • Stopped PostgreSQL container"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   • Removed all database volumes and data"
else
    echo "   • Preserved database volumes and data"
fi
echo "   • Cleaned up Docker system resources"
echo ""
echo "💡 To start fresh:"
echo "   ./scripts/setup-database.sh"