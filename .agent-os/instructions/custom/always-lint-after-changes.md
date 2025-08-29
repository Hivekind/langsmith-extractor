# Always Lint After Code Changes

## Rule: Mandatory Linting After Every Code Change

You MUST run linting checks after every code modification to maintain code quality and catch issues early.

### Required Actions After Code Changes

When you make ANY changes to Python code files (*.py), you MUST:

1. **Run ruff check**: `uv run ruff check .`
2. **Fix auto-fixable issues**: `uv run ruff check --fix .` 
3. **Format code**: `uv run ruff format .`
4. **Re-run tests if needed**: If linting changes affect functionality

### When This Applies

- After creating new Python files
- After editing existing Python files
- After refactoring code
- Before creating commits
- When requested by the user

### Process

1. Make code changes
2. Immediately run: `uv run ruff check --fix . && uv run ruff format .`
3. Address any remaining linting errors manually
4. Re-run tests if linting made functional changes
5. Only then proceed with next steps or commits

### Benefits

- Catches errors early in development cycle
- Maintains consistent code style across project
- Prevents accumulation of technical debt
- Ensures commits contain clean, properly formatted code
- Reduces noise in diffs by maintaining consistent formatting

This rule ensures code quality is maintained throughout the development process rather than being addressed as an afterthought.