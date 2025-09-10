# GitHub Workflows

This directory contains GitHub Actions workflows for automated CI/CD.

## CI Workflow (`ci.yml`)

The main CI workflow runs on:
- **Pull requests** to the `main` branch
- **Pushes** to any branch except `main` (covers PR branches)
- **Manual triggers** via GitHub UI

### What it does:

1. **Code Quality Checks**
   - Runs `ruff format --check` to verify code formatting
   - Runs `ruff check` for linting violations

2. **Test Suite**
   - Runs the full pytest suite (267 tests)
   - Uses verbose output for better debugging

3. **CLI Functionality Test**
   - Verifies that the CLI commands work correctly
   - Tests help commands to ensure the CLI is functional

### Requirements:

- Python 3.13
- `uv` package manager
- All dependencies defined in `pyproject.toml`

### Status Checks:

When you create a PR or push to a PR branch, you'll see:
- ✅ Green check mark if all tests pass and code quality checks pass
- ❌ Red X if any tests fail or code quality issues are found
- 🟡 Yellow dot while the workflow is running

This provides immediate feedback on the health of your changes before merging.