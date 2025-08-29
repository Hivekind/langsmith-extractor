# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project called `langsmith-extractor` that appears to be in early development. It uses `uv` as the package manager and `ruff` for linting.

## Commands

### Development Setup
```bash
# Install dependencies
uv sync
```

### Running the Application
```bash
# Run main script
uv run python main.py
```

### Linting
```bash
# Run ruff linter
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

## Project Structure

- `main.py` - Entry point for the application
- `pyproject.toml` - Project configuration and dependencies
- Python 3.13+ required