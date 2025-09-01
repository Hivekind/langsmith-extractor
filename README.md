# LangSmith Extractor

A CLI tool for extracting, analyzing, and archiving LangSmith trace data with automated reporting and Google Drive integration.

## Overview

LangSmith Extractor (LSE) is a command-line utility that helps teams extract and analyze LangSmith trace data by providing automated data fetching, transformation, and export capabilities. It enables comprehensive local analysis, custom reporting, and secure archival of trace data to Google Drive.

Key capabilities:
- 🚀 Automated trace data extraction from LangSmith API
- 📁 Local storage with intelligent date-based organization
- 🔄 Complete trace hierarchy fetching (root traces + all child runs)
- ☁️ Google Drive archival with compression
- 📊 Custom report generation and analysis
- 🔒 Secure credential management
## Developer Tools & Philosophy

This project was developed using modern Python tooling and AI-assisted development:

### Development Tools

- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager and project management tool. We use `uv` exclusively for dependency management, virtual environments, and running commands. It's significantly faster than pip and provides better dependency resolution.

- **[ruff](https://github.com/astral-sh/ruff)** - Extremely fast Python linter and formatter. Replaces multiple tools (black, isort, flake8) with a single, performant solution.

- **[Agent-OS](https://buildermethods.com/agent-os)** - A structured framework for AI-assisted software development. This is an organizational methodology where all project specifications, roadmap, and development standards are captured directly in the codebase within the `.agent-os/` directory structure. This approach ensures AI assistants have full context and standards for consistent development.

- **[Claude Code](https://claude.ai/code)** - This entire codebase was developed with Claude Code, Anthropic's AI coding assistant. The project includes specific support files (`CLAUDE.md`) to maintain context and development standards for AI-assisted contributions.

## Getting Started

### Prerequisites

1. Python 3.13 or higher
2. uv package manager (install from https://github.com/astral-sh/uv)
3. A LangSmith account with API access
4. (Optional) Google Cloud project with Drive API enabled for archival features

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone git@github.com:Hivekind/langsmith-extractor.git
   cd langsmith-extractor
   ```

2. **Install dependencies using uv:**
   ```bash
   # Install all dependencies including dev tools
   uv sync
   ```

3. **Set up your environment variables:**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your credentials
   # Required: LANGSMITH_API_KEY
   # Optional: Google OAuth credentials for Drive archival
   ```

4. **Source your environment (important for each new session):**
   ```bash
   # Load environment variables
   source .env
   # Or use a tool like direnv for automatic loading
   ```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=lse

# Run specific test file
uv run pytest tests/test_analysis.py -v

# After making code changes, always run linting
uv run ruff check --fix .
uv run ruff format .
```

### Complete Archive Workflow Example

Here's how to run through a complete trace archival sequence:

```bash
# 1. Fetch traces from LangSmith for a specific date
uv run lse fetch --project my-project --date 2024-01-15

# 2. Generate a report from fetched data
uv run lse report zenrows-errors --project my-project --date 2024-01-15

# 3. Archive workflow (fetch, compress, and upload to Google Drive)
# First, fetch all traces including child runs
uv run lse archive fetch --project my-project --date 2024-01-15 --include-children

# Create a zip archive
uv run lse archive zip --project my-project --date 2024-01-15

# Upload to Google Drive (requires OAuth setup)
uv run lse archive upload --project my-project --date 2024-01-15

# Or do all three steps at once
uv run lse archive --project my-project --date 2024-01-15 --include-children

# 4. Restore archived data from Google Drive
uv run lse archive restore --project my-project --start-date 2024-01-01 --end-date 2024-01-31
```

## Command Reference

### Core Commands

- `lse fetch` - Fetch traces from LangSmith API
  - Options: `--project`, `--date`, `--start-date`, `--end-date`, `--limit`

- `lse report` - Generate analysis reports from stored traces
  - Subcommands: `zenrows-errors` (analyze zenrows scraper failures)
  - Options: `--project`, `--date`, `--start-date`, `--end-date`

- `lse archive` - Archive trace data to Google Drive
  - Subcommands: `fetch`, `zip`, `upload`, `restore`
  - Options: `--project`, `--date`, `--include-children`, `--force`

### Common Options

- `--project` - LangSmith project name to process
- `--date` - Single date in YYYY-MM-DD format (UTC)
- `--start-date` / `--end-date` - Date range for processing
- `--include-children` - Fetch complete trace hierarchies (all child runs)
- `--force` - Skip confirmation prompts

## Security Considerations

### API Key Management

**Critical:** Never commit API keys or credentials to version control.

1. **Environment Variables:** Always use `.env` files for local development
2. **The `.env` file is gitignored** and should never be committed
3. **Google OAuth:** The `token.json` file created after OAuth authentication is also gitignored
4. **Production:** Use secure secret management systems (environment variables, secret managers)

### Contribution Guidelines

When contributing to this project:

- **Never include real API keys** in code, comments, or documentation
- **Never reference specific client names** or projects - use generic examples like "my-project"
- **Never divulge any specific information about Hivekind's clients** - this includes project names, data patterns, or business logic specific to any client
- **Use example data** that is clearly fictional when writing tests or documentation
- **Sanitize any debug output** before sharing logs or error messages

### Google Drive Authentication

For archival features, you'll need to set up Google OAuth:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create or select a project
3. Enable the Google Drive API
4. Create OAuth 2.0 credentials (Desktop application type)
5. Add credentials to your `.env` file:
   ```bash
   GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
   GOOGLE_DRIVE_FOLDER_URL=https://drive.google.com/drive/folders/YOUR-FOLDER-ID
   ```

## Project Management

This project uses the **Agent-OS framework** for project management and development standards. All specifications, roadmap, and development guidelines are maintained in the source code itself.

### Key Locations

- **Product Vision & Roadmap:** `.agent-os/product/`
  - `mission.md` - Project mission and user personas
  - `roadmap.md` - Development roadmap with phase breakdowns
  - `tech-stack.md` - Technology decisions and architecture

- **Development Standards:** `.agent-os/standards/`
  - `code-style.md` - Code formatting and style guidelines
  - Language-specific guides in subdirectories

- **Active Specifications:** `.agent-os/specs/`
  - Detailed specifications for features in development
  - Task tracking and implementation details

- **Instructions:** `.agent-os/instructions/`
  - Development workflow instructions
  - Custom rules for this project

### Current Development Status

To see the current development status and roadmap:
```bash
# View the current roadmap
cat .agent-os/product/roadmap.md

# Check active feature specifications
ls .agent-os/specs/

# View coding standards
cat .agent-os/standards/code-style.md
```

## Architecture

The project follows a modular architecture:

- `lse/cli.py` - CLI command definitions using Typer
- `lse/client.py` - LangSmith API client wrapper
- `lse/storage.py` - Local trace storage management
- `lse/analysis.py` - Trace analysis and reporting logic
- `lse/archive.py` - Archive management utilities
- `lse/drive.py` - Google Drive integration
- `lse/config.py` - Configuration management with Pydantic

## Troubleshooting

### Common Issues

1. **Rate Limiting:** If you encounter 429 errors when fetching traces with `--include-children`, increase the delay:
   ```bash
   uv run lse archive fetch --project my-project --date 2024-01-15 --include-children --delay-ms 500
   ```

2. **OAuth Authentication:** First run will open a browser for Google authentication. The token is cached in `token.json` for future use.

3. **Missing Traces:** Ensure your date filters use UTC timezone. All date operations are in UTC.

## Contributing

This project was developed by Hivekind with AI assistance from Claude Code. While we're not accepting contributions at this time, you're welcome to fork and adapt for your own use.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
