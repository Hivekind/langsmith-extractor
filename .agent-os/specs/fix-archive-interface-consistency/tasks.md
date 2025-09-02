# Task Tracking: Fix Archive Interface Consistency

## Status: 📋 PLANNED

**Start Date**: TBD  
**Target Completion**: 1 day
**Priority**: MEDIUM - UX improvement, high user impact

## Overview

Replace the date range interface of `lse archive restore` command with a simple `--date` parameter to match other archive commands exactly, eliminating interface inconsistency.

## Task Breakdown

### Phase 1: Core Interface Enhancement ⚡

#### 1.1 Replace Parameter Interface
- [ ] **Update restore command signature**
  - [ ] Add `--date` option to CLI decorator (required)
  - [ ] Remove `--start-date` and `--end-date` options entirely
  - [ ] Update function signature to only accept date parameter
  - **File**: `lse/cli.py` (restore command)
  - **Estimate**: 15 minutes

#### 1.2 Implement Simple Validation
- [ ] **Add date parameter validation**
  - [ ] Use same date validation as other archive commands
  - [ ] Remove complex date range validation logic
  - [ ] Ensure date format matches YYYY-MM-DD pattern
  - [ ] Add clear error messages for invalid dates
  - **File**: `lse/cli.py` (restore command function)
  - **Estimate**: 20 minutes

#### 1.3 Update Help Text
- [ ] **Update command documentation**
  - [ ] Update command docstring with single date usage only
  - [ ] Match parameter descriptions with other archive commands
  - [ ] Include example showing --date usage (like fetch/zip/upload)
  - [ ] Remove all references to date range functionality
  - **File**: `lse/cli.py` (restore command)
  - **Estimate**: 15 minutes

### Phase 2: Testing & Validation 🧪

#### 2.1 Add New Parameter Tests
- [ ] **Test --date parameter usage**
  - [ ] Test --date parameter parsing and validation
  - [ ] Test date format validation (YYYY-MM-DD)
  - [ ] Test --date with valid dates
  - [ ] Test --date with invalid date formats
  - **File**: `tests/test_cli.py`
  - **Estimate**: 30 minutes

#### 2.2 Test Breaking Changes
- [ ] **Test removed parameter handling**
  - [ ] Test --start-date usage (should error with helpful message)
  - [ ] Test --end-date usage (should error with helpful message)
  - [ ] Test combined --start-date/--end-date usage (should error)
  - [ ] Verify error messages guide users to new interface
  - **File**: `tests/test_cli.py`
  - **Estimate**: 30 minutes

#### 2.3 Update Existing Tests
- [ ] **Migrate existing restore tests**
  - [ ] Update tests using --start-date/--end-date to use --date
  - [ ] Remove tests for date range functionality
  - [ ] Ensure all restore functionality still works with --date
  - [ ] Verify no regressions in restore behavior
  - **File**: `tests/test_cli.py`
  - **Estimate**: 25 minutes

### Phase 3: Documentation & Polish 📚

#### 3.1 Update Documentation
- [ ] **Sync examples across commands**
  - [ ] Update CLAUDE.md with consistent archive examples
  - [ ] Ensure all archive commands show similar usage patterns
  - [ ] Add examples showing the new --date interface
  - **File**: `CLAUDE.md`
  - **Estimate**: 15 minutes

#### 3.2 Validate Interface Consistency
- [ ] **Check all archive commands**
  - [ ] Verify fetch, zip, upload, restore all support --date
  - [ ] Ensure help text format is consistent across commands
  - [ ] Test parameter validation consistency
  - [ ] Validate examples and documentation alignment
  - **Estimate**: 15 minutes

## Implementation Details

### Before (Inconsistent Interface)
```bash
# Other commands (consistent)
lse archive fetch --date 2025-08-20 --project my-project
lse archive zip --date 2025-08-20 --project my-project
lse archive upload --date 2025-08-20 --project my-project

# Restore command (inconsistent)
lse archive restore --start-date 2025-08-20 --end-date 2025-08-20 --project my-project
```

### After (Consistent Interface)
```bash  
# All commands use --date consistently
lse archive fetch --date 2025-08-20 --project my-project
lse archive zip --date 2025-08-20 --project my-project
lse archive upload --date 2025-08-20 --project my-project
lse archive restore --date 2025-08-20 --project my-project  # NEW

# Range operations no longer supported (breaking change)
lse archive restore --start-date 2025-08-01 --end-date 2025-08-31 --project my-project  # REMOVED
```

### Parameter Validation Logic

```python
def validate_restore_date(date):
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

## Breaking Changes

### Yes - Intentional Breaking Changes
- **--start-date and --end-date parameters removed**: Existing range usage will break
- **--date parameter required**: Matches other archive commands exactly
- **Single date operations only**: Multi-date restore requires multiple commands

## Dependencies

- Understanding of current restore command implementation in `lse/cli.py`
- No external dependencies or API changes required
- Existing date parsing and validation logic can be reused

## Definition of Done

- [ ] `--date` parameter added to restore command
- [ ] Parameter validation prevents conflicting date specifications
- [ ] Help text shows both single date and range usage examples
- [ ] All tests pass including new parameter validation tests
- [ ] Existing restore functionality unchanged (zero regressions)
- [ ] Interface consistency achieved across all archive commands
- [ ] Documentation updated with new usage examples
- [ ] Code linted and formatted

## Commands for Testing

```bash
# Test the new single date interface
lse archive restore --date 2025-08-20 --project my-project

# Test existing range interface (should be unchanged)  
lse archive restore --start-date 2025-08-01 --end-date 2025-08-31 --project my-project

# Test parameter conflict (should error with helpful message)
lse archive restore --date 2025-08-20 --start-date 2025-08-01 --project my-project

# Run all tests
uv run pytest tests/test_cli.py -k "restore" -v

# Check help text
lse archive restore --help
```

## Expected Outcomes

### User Experience Improvements
1. **Natural interface**: Users can use `--date` for single date restore operations
2. **Consistent learning**: Same parameter pattern across all archive commands  
3. **Reduced friction**: No more verbose date range syntax for simple operations
4. **Better discoverability**: Help text shows the expected interface options

### Technical Benefits
1. **Interface standardization**: All archive commands follow same parameter patterns
2. **Improved error messages**: Clear guidance when parameters conflict
3. **Enhanced testing**: Comprehensive coverage of parameter combinations
4. **Better maintainability**: Consistent interface patterns across codebase

## Future Considerations

After this fix:
- Consider adding date range support to other archive commands (fetch, zip, upload)
- Evaluate whether to add parameter shortcuts or aliases
- Review other CLI commands for similar interface inconsistencies

This small change significantly improves the user experience with minimal implementation effort and zero risk to existing functionality.