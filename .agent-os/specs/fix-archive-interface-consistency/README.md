# Fix Archive Command Interface Consistency

## Problem Summary

The archive commands have inconsistent parameter interfaces that create user confusion and break the principle of least surprise. Users must remember different parameter patterns for different archive operations when they should all follow the same interface conventions.

## Current Interface Analysis

### Consistent Commands (Single Date Support)

All other archive commands follow the same pattern:

```bash
lse archive fetch --date 2025-08-20 --project my-project
lse archive zip --date 2025-08-20 --project my-project  
lse archive upload --date 2025-08-20 --project my-project
```

**Parameters:**
- `--date` (required): Single date in YYYY-MM-DD format
- `--project` (required): Project name
- `--force` (optional): Skip confirmations

### Inconsistent Command (Date Range Only)

The restore command forces users to use verbose date range syntax even for single dates:

```bash
# Current: Unnecessarily verbose for single date
lse archive restore --start-date 2025-08-20 --end-date 2025-08-20 --project my-project

# What users expect (but doesn't work):
lse archive restore --date 2025-08-20 --project my-project
```

**Parameters:**
- `--start-date` (optional): Start of date range
- `--end-date` (optional): End of date range
- `--project` (required): Project name
- `--force` (optional): Skip confirmations

## User Experience Issues

### 1. Interface Inconsistency
Users learning the archive commands naturally expect `--date` to work across all commands, but get confused when restore requires different parameters.

### 2. Verbose Single Date Operations
The most common restore operation (single date) requires the most verbose syntax:
```bash
# User expectation (simple)
lse archive restore --date 2025-08-20 --project my-project

# Current reality (verbose)
lse archive restore --start-date 2025-08-20 --end-date 2025-08-20 --project my-project
```

### 3. Error Messages Don't Help
When users try the expected interface, they get an unhelpful error:
```
No such option: --date (Possible options: --end-date, --start-date)
```

This doesn't explain why restore is different or how to fix it.

## Solution Design

### Primary Fix: Add --date Support to Restore

Replace the date range interface with a simple --date interface to match other commands:

```bash
# New: Single date support (matches other commands)
lse archive restore --date 2025-08-20 --project my-project

# Old: Date range support (will be removed)
lse archive restore --start-date 2025-08-01 --end-date 2025-08-31 --project my-project
```

### Parameter Logic

1. **Single --date parameter only**: Matches fetch/zip/upload exactly
2. **Remove range parameters**: Delete --start-date and --end-date entirely  
3. **Simple validation**: Same date format validation as other commands
4. **Breaking change**: Existing range usage must migrate to single dates

## Implementation Plan

### Phase 1: Interface Replacement
1. **Add --date parameter** to restore command
2. **Remove --start-date and --end-date parameters** entirely
3. **Update parameter validation** to match other archive commands
4. **Update help text** to show single date usage only

### Phase 2: Breaking Change Management  
1. **Clear deprecation** of old interface
2. **Migration guidance** for existing range usage
3. **Updated error messages** for removed parameters

### Phase 3: Documentation & Testing
1. **Update help text** to match other archive commands exactly
2. **Add tests** for --date parameter validation
3. **Remove tests** for old range parameters
4. **Update examples** in documentation and comments

## Technical Implementation

### Parameter Definition

```python
@click.command()
@click.option("--date", required=True, help="Date to restore (YYYY-MM-DD format)")
@click.option("--project", required=True, help="Project name to restore")
@click.option("--force", is_flag=True, help="Skip confirmation prompts")
def restore(date, project, force):
    """Restore archived traces from Google Drive."""
```

### Validation Logic

```python
def validate_date_parameters(date):
    """Simple date validation matching other archive commands."""
    # Same validation as fetch/zip/upload commands
    try:
        datetime.strptime(date, '%Y-%m-%d')
        return date
    except ValueError:
        raise click.UsageError(
            "Invalid date format. Use YYYY-MM-DD format."
        )
```

### Help Text Enhancement

```
Usage: lse archive restore [OPTIONS]

Restore archived traces from Google Drive.

Options:
  --date TEXT          Date to restore traces for (YYYY-MM-DD format) [required]
  --project TEXT       Project name to restore [required]  
  --force              Skip confirmation when overwriting local files

Examples:
  # Restore single date (matches other archive commands)
  lse archive restore --date 2025-08-20 --project my-project
```

## Breaking Changes Assessment

### Breaking Changes
- **--start-date and --end-date parameters removed**: Existing range usage will break
- **--date parameter required**: Matches other archive commands exactly
- **Single date operations only**: Multi-date restore requires multiple commands

### Migration Path
- **Replace range operations**: Use multiple single-date commands instead
- **Update scripts**: Change --start-date/--end-date to --date
- **Clear error messages**: Guide users to new interface when old parameters used

## Benefits

### For Users
- **Consistent interface**: Same `--date` pattern across all archive commands
- **Simpler single date operations**: Natural, expected parameter name
- **Reduced cognitive load**: One interface pattern to remember
- **Better discoverability**: Help text shows expected options

### For Maintenance
- **Interface consistency**: All commands follow same parameter patterns
- **Better help text**: Clear examples for both single date and range operations
- **Improved error messages**: Better guidance when parameters conflict

## Success Criteria

1. **Interface Consistency**: All archive commands support `--date` for single date operations
2. **Backward Compatibility**: All existing restore usage continues to work unchanged
3. **Clear Documentation**: Help text shows both usage patterns with examples
4. **Comprehensive Testing**: All parameter combinations covered by tests
5. **User Experience**: Single date restore operations use intuitive syntax

## Timeline

- **Day 1**: Add --date parameter and validation logic
- **Day 1**: Update help text and error messages
- **Day 1**: Add comprehensive test coverage  
- **Day 1**: Validate all existing usage still works

This is a small, focused change that significantly improves CLI usability with zero risk of breaking existing workflows.