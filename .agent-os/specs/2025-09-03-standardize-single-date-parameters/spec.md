# Standardize Single-Date Parameters Specification

**Phase:** 5.5  
**Created:** 2025-09-03  
**Status:** PLANNED  

## Overview

Remove date range support from all commands to enforce consistent single-date operations across the LangSmith Extractor CLI. This addresses interface inconsistencies where some commands support both single dates and date ranges.

## Current State Analysis

### Commands with Date Range Support
- ✅ `lse archive fetch` - Single date only (`--date`)
- ✅ `lse report zenrows-detail` - Single date only (`--date`) 
- ❌ `lse report zenrows-errors` - **Has both single (`--date`) AND range (`--start-date`/`--end-date`)**

### Problem Areas
1. **Interface Inconsistency**: Users must learn different parameter patterns
2. **Complex Validation**: Date range validation adds complexity
3. **UTC Handling**: Different timezone logic for single vs range dates
4. **Code Duplication**: Separate code paths for single and range operations

## Requirements

### User Stories
- **As a CLI user**, I want all commands to use the same date parameter format so I don't have to remember different interfaces
- **As a developer**, I want simplified date handling logic without complex range validation
- **As a maintainer**, I want consistent UTC timezone handling across all date operations

### Technical Requirements

#### 1. Remove Date Range Parameters
- Remove `--start-date` and `--end-date` from `zenrows-errors` command
- Keep only `--date YYYY-MM-DD` parameter
- All dates assume UTC timezone for the full day (00:00:00 to 23:59:59)

#### 2. Simplify Validation Logic
- Remove `validate_date_range()` function
- Keep only `validate_date()` for single date validation
- Remove complex date range comparison logic

#### 3. Update Analysis Functions
- Remove `start_date`/`end_date` parameters from `analyze_zenrows_errors()`
- Keep only `single_date` parameter for consistency
- Remove date range iteration logic

#### 4. Update Help Documentation
- Remove date range examples from command help
- Update command descriptions to reflect single-date operation only
- Ensure all examples use `--date YYYY-MM-DD` format

## Implementation Scope

### Files to Modify

#### Core Command Files
- `lse/commands/report.py`
  - Remove `start_date`/`end_date` parameters from `zenrows_errors_command()`
  - Remove `validate_date_range()` function
  - Update `generate_zenrows_report()` to single-date only
  - Update help text and examples

#### Analysis Module
- `lse/analysis.py`
  - Remove `start_date`/`end_date` parameters from `analyze_zenrows_errors()`
  - Remove date range iteration logic
  - Keep only single-date processing

#### Test Files  
- `tests/test_report_command.py`
  - Remove date range test cases
  - Update all tests to use single `--date` parameter
  - Verify error handling for invalid single dates

### Functions to Remove/Modify

#### Remove Completely
- `validate_date_range()` function and its logic
- Date range validation error messages
- Date range help text and examples

#### Modify to Single-Date Only
- `generate_zenrows_report()` - Remove range parameters
- `TraceAnalyzer.analyze_zenrows_errors()` - Remove range processing
- Command parameter definitions in `zenrows_errors_command()`

## Migration Strategy

### Backward Compatibility
- **Breaking Change**: This removes existing `--start-date`/`--end-date` functionality
- **Users must migrate** to multiple single-date command calls for range analysis
- **Clear error messages** if users attempt to use removed parameters

### Alternative for Range Analysis
Users who need range analysis can:
1. **Script multiple calls**: Use shell loops to call command for each date
2. **Future enhancement**: Phase 6 could add multi-date aggregation features if needed

Example migration:
```bash
# Old (will be removed):
lse report zenrows-errors --start-date 2025-08-01 --end-date 2025-08-03

# New (multiple calls):
for date in 2025-08-01 2025-08-02 2025-08-03; do
  lse report zenrows-errors --date $date
done
```

## Success Criteria

### Functional Requirements
- [ ] All commands accept only `--date YYYY-MM-DD` parameter
- [ ] No commands accept `--start-date` or `--end-date` parameters
- [ ] All dates processed in UTC timezone consistently
- [ ] Clear error messages for invalid date formats

### Quality Requirements  
- [ ] All existing tests pass after parameter changes
- [ ] No new test failures introduced
- [ ] Command help text is clear and consistent
- [ ] Error handling works for all edge cases

### Performance Requirements
- [ ] No performance regression in single-date operations
- [ ] Simplified validation reduces command startup time
- [ ] Reduced code complexity in date handling functions

## Testing Strategy

### Test Coverage
- [ ] Valid single date inputs work correctly
- [ ] Invalid date formats show clear error messages
- [ ] UTC timezone handling is consistent
- [ ] Command help displays correctly
- [ ] No regression in existing functionality

### Test Cases to Update
- Remove all `--start-date`/`--end-date` test cases
- Update parameter validation tests for single-date only  
- Verify error messages for removed parameters
- Test UTC date processing consistency

## Timeline

**Estimated Effort:** 1-2 days
**Priority:** Medium - Interface consistency improvement

### Implementation Steps
1. **Day 1**: Remove parameters and update command interface
2. **Day 1**: Update analysis functions and remove range logic  
3. **Day 2**: Update tests and verify functionality
4. **Day 2**: Update documentation and help text

## Dependencies

- No external dependencies
- No blocking issues
- Can be implemented independently

## Risks & Mitigations

### Risk: Breaking Change for Users
- **Impact**: Users using date ranges must change workflow
- **Mitigation**: Clear error messages, migration documentation

### Risk: Test Failures  
- **Impact**: Complex test updates required
- **Mitigation**: Systematic test review and update process

### Risk: Missed Date Range Logic
- **Impact**: Incomplete removal could cause bugs
- **Mitigation**: Thorough code review and testing

## Acceptance Criteria

- [ ] `lse report zenrows-errors --start-date 2025-08-01` shows clear error
- [ ] `lse report zenrows-errors --date 2025-08-01` works correctly  
- [ ] All 146+ tests pass after changes
- [ ] Command help shows only `--date` parameter
- [ ] UTC timezone handling is consistent across all date operations