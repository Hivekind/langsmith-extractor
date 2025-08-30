# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with the langsmith-extractor codebase.

## Critical: Agent-OS Integration

**This project uses Agent-OS for workflow management and standards. You MUST refer to and follow all Agent-OS managed context and instructions.**

### Key Agent-OS Files to Reference

- **Product Definition**:
  - `.agent-os/product/mission.md` - Product mission, users, and key features
  - `.agent-os/product/tech-stack.md` - Technology choices and architecture
  - `.agent-os/product/roadmap.md` - Development roadmap

- **Standards**:
  - `.agent-os/standards/code-style.md` - Code formatting and style rules
  - Additional language-specific guides in `.agent-os/standards/code-style/`

- **Instructions**:
  - `.agent-os/instructions/custom/always-lint-after-changes.md` - Mandatory linting after code changes
  - `.agent-os/instructions/custom/no-auto-commits.md` - NEVER commit without explicit user approval
  - Core workflow instructions in `.agent-os/instructions/core/`

- **Specifications**:
  - Active specs in `.agent-os/specs/` directories with task tracking

## Project Overview

**LangSmith Extractor** is a CLI tool for extracting and analyzing LangSmith trace data, developed internally at Hivekind for automated data fetching, transformation, and reporting.

### Primary Purpose
- Extract trace data from LangSmith accounts via API
- Store data locally for fast access and analysis
- Transform raw traces into customizable tabular formats
- Export to Google Sheets for stakeholder reporting

## Technology Stack

### Core Technologies
- **Language**: Python 3.13+
- **Package Manager**: `uv` (NOT pip, NOT poetry)
- **CLI Framework**: Typer with Rich for output
- **API Client**: langsmith SDK
- **Configuration**: Pydantic & pydantic-settings
- **Testing**: pytest with pytest-cov
- **Linting/Formatting**: ruff

### Key Dependencies
- `typer[all]` - CLI framework with full features
- `python-dotenv` - Environment variable management
- `pydantic` & `pydantic-settings` - Configuration and validation
- `rich` - Terminal formatting and output
- `langsmith` - LangSmith API client

## Project Structure

```
langsmith-extractor/
├── lse/                    # Main package (langsmith-extractor -> lse)
│   ├── __init__.py
│   ├── cli.py             # Typer CLI app and commands
│   ├── client.py          # LangSmith API client wrapper
│   ├── config.py          # Pydantic settings management
│   ├── storage.py         # Local data storage
│   ├── analysis.py        # Data analysis and transformations
│   ├── formatters.py      # Output formatting
│   ├── retry.py           # Retry logic for API calls
│   ├── timezone.py        # Timezone handling
│   ├── utils.py           # Utility functions
│   └── exceptions.py      # Custom exceptions
├── tests/                 # Test suite
│   ├── test_*.py         # Unit and integration tests
├── .agent-os/            # Agent-OS configuration and standards
├── pyproject.toml        # Project configuration
└── CLAUDE.md            # This file
```

## Development Commands

### Environment Setup
```bash
# Install all dependencies (including dev)
uv sync

# Install only production dependencies
uv sync --no-dev
```

### Running the CLI
```bash
# Run the CLI directly
uv run lse --help

# Or via Python module
uv run python -m lse.cli
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=lse

# Run specific test file
uv run pytest tests/test_cli.py

# Run with verbose output
uv run pytest -v
```

### Code Quality (MANDATORY after code changes)
```bash
# Check for linting issues
uv run ruff check .

# Auto-fix fixable issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# Combined (recommended after any code change)
uv run ruff check --fix . && uv run ruff format .
```

## Critical Development Rules

### 1. ALWAYS Follow Agent-OS Context
- Check `.agent-os/` files for project-specific instructions
- Follow standards defined in `.agent-os/standards/`
- Refer to active specs in `.agent-os/specs/` for current work

### 2. Linting is MANDATORY
After ANY Python code changes, you MUST:
1. Run `uv run ruff check --fix .`
2. Run `uv run ruff format .`
3. Fix any remaining issues manually
4. Only then proceed with next steps

### 3. NO Automatic Commits
- NEVER run `git commit` without explicit user request
- User must explicitly say "commit" or "create a commit"
- Show changes with `git status` and `git diff` for review
- Wait for approval before committing

### 4. Code Style Standards
- **Indentation**: 2 spaces (enforced by ruff)
- **Line Length**: 100 characters max
- **Naming**: 
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`  
  - Constants: `UPPER_SNAKE_CASE`
- **Strings**: Single quotes preferred
- **Comments**: Explain "why" not "what"

### 5. Testing Requirements
- Write tests for new functionality
- Maintain existing test coverage
- Run tests after significant changes
- Use pytest fixtures for common test data

## CLI Usage Examples

```bash
# Fetch traces from a project
uv run lse fetch --project my-project --limit 100

# Fetch with date range
uv run lse fetch --project my-project --start-date 2024-01-01 --end-date 2024-01-31

# Generate report from fetched data
uv run lse report --format table

# Export to Google Sheets
uv run lse export --format sheets --sheet-id <sheet-id>
```

## Environment Variables

Required environment variables (use `.env` file):
```bash
LANGSMITH_API_KEY=your-api-key
OUTPUT_DIR=./data  # Optional, defaults to ./data
```

## Common Tasks

### Adding a New Command
1. Create command function in `lse/cli.py`
2. Use Typer decorators for arguments/options
3. Add corresponding logic in appropriate module
4. Write tests in `tests/test_cli.py`
5. Run linting and formatting

### Adding a New Data Transformation
1. Add transformation logic to `lse/analysis.py`
2. Create formatter in `lse/formatters.py` if needed
3. Write comprehensive tests
4. Update CLI to expose new functionality

### Debugging API Issues
1. Check retry logic in `lse/retry.py`
2. Verify API key in environment
3. Use `--debug` flag for verbose output
4. Check `lse/exceptions.py` for error handling

## Important Notes

1. **Always use `uv`** - Never use pip or poetry directly
2. **Python 3.13+** is required - Don't use older versions
3. **Follow Agent-OS specs** - Check `.agent-os/specs/` for active work
4. **Maintain test coverage** - Add tests for new features
5. **Document complex logic** - Add comments explaining "why"
6. **Use type hints** - Leverage Pydantic for validation
7. **Handle errors gracefully** - Use custom exceptions from `lse/exceptions.py`

## Getting Help

- Check `.agent-os/product/mission.md` for product vision
- Review `.agent-os/specs/` for detailed specifications
- Refer to test files for usage examples
- Use `--help` flag on CLI commands for documentation