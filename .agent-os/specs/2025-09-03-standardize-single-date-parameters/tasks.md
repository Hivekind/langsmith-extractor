# Standardize Single-Date Parameters - Tasks

**Phase:** 5.5  
**Status:** PLANNED  
**Created:** 2025-09-03

## Overview
Remove date range support from `zenrows-errors` command to enforce consistent single-date operations across all CLI commands.

## Task Breakdown

### 1. Command Interface Updates (lse/commands/report.py)

#### 1.1 Remove Date Range Parameters
- [ ] Remove `start_date` parameter from `zenrows_errors_command()`
- [ ] Remove `end_date` parameter from `zenrows_errors_command()` 
- [ ] Update command help text to show only `--date` parameter
- [ ] Remove date range examples from command docstring

#### 1.2 Remove Date Range Validation
- [ ] Remove `validate_date_range()` function completely
- [ ] Remove date range validation logic in `zenrows_errors_command()`
- [ ] Remove error messages for date range validation
- [ ] Keep only single date validation with `validate_date()`

#### 1.3 Update Report Generation Function  
- [ ] Remove `start_date`/`end_date` parameters from `generate_zenrows_report()`
- [ ] Remove date range processing logic
- [ ] Keep only `single_date` parameter and logic
- [ ] Update function docstring and parameter documentation

### 2. Analysis Module Updates (lse/analysis.py)

#### 2.1 Update TraceAnalyzer.analyze_zenrows_errors()
- [ ] Remove `start_date` parameter from method signature
- [ ] Remove `end_date` parameter from method signature  
- [ ] Remove date range iteration logic
- [ ] Keep only `single_date` parameter processing
- [ ] Update method docstring and parameter docs

#### 2.2 Update Helper Functions
- [ ] Review `find_trace_files()` for any date range dependencies
- [ ] Update any date range logic to single-date only
- [ ] Ensure consistent UTC timezone handling

### 3. Test Updates (tests/test_report_command.py)

#### 3.1 Remove Date Range Tests
- [ ] Remove all test cases using `--start-date`/`--end-date`
- [ ] Remove `test_validates_date_range_order()` test
- [ ] Remove date range validation error tests
- [ ] Remove date range parameter combination tests

#### 3.2 Add Single-Date Error Tests
- [ ] Add test for `--start-date` showing clear error message  
- [ ] Add test for `--end-date` showing clear error message
- [ ] Verify single `--date` parameter works correctly
- [ ] Test invalid date format handling

#### 3.3 Update Existing Tests
- [ ] Update any tests using date ranges to single dates
- [ ] Verify command help text shows only `--date` parameter
- [ ] Update integration tests for single-date operation

### 4. Documentation Updates

#### 4.1 Command Help Text  
- [ ] Update `zenrows_errors_command()` help to show single-date usage only
- [ ] Remove all date range examples from command help
- [ ] Add clear single-date usage examples
- [ ] Update parameter descriptions

#### 4.2 Error Messages
- [ ] Add clear error for removed `--start-date` parameter
- [ ] Add clear error for removed `--end-date` parameter  
- [ ] Update validation error messages for clarity
- [ ] Test all error message scenarios

### 5. Code Cleanup

#### 5.1 Remove Dead Code
- [ ] Remove unused imports related to date range processing
- [ ] Remove unused variables in date range functions
- [ ] Clean up any leftover date range constants or config
- [ ] Remove commented-out date range code

#### 5.2 Simplify Logic
- [ ] Simplify conditional logic that handled both single/range dates
- [ ] Remove complex date range validation paths
- [ ] Consolidate single-date processing logic
- [ ] Optimize UTC timezone handling

### 6. Quality Assurance

#### 6.1 Testing
- [ ] Run full test suite and verify all 146+ tests pass
- [ ] Test command with various date formats
- [ ] Test error handling for invalid inputs
- [ ] Test UTC timezone behavior consistency

#### 6.2 Integration Testing  
- [ ] Test `zenrows-errors` command with real data
- [ ] Verify report output format unchanged
- [ ] Test with different project configurations
- [ ] Validate performance with large datasets

#### 6.3 Documentation Review
- [ ] Review all help text for accuracy
- [ ] Verify examples work correctly
- [ ] Check error messages are helpful
- [ ] Update any README or spec documentation

## Completion Criteria

### Must Have
- [ ] No `--start-date` or `--end-date` parameters in any command
- [ ] All commands use only `--date YYYY-MM-DD` format
- [ ] All existing tests pass without modification (except date range tests)
- [ ] Clear error messages for removed parameters

### Should Have  
- [ ] Simplified validation logic with reduced complexity
- [ ] Consistent UTC timezone handling across all commands
- [ ] Updated help text and documentation
- [ ] No performance regression

### Could Have
- [ ] Improved error messaging for date format issues
- [ ] Better examples in command help
- [ ] Code cleanup for improved maintainability

## Risk Mitigation

### Breaking Change Communication
- [ ] Document migration path for users using date ranges
- [ ] Provide clear error messages explaining the change
- [ ] Update any user documentation or examples

### Testing Thoroughness
- [ ] Test edge cases for single-date operations
- [ ] Verify no regressions in existing functionality  
- [ ] Test error handling thoroughly
- [ ] Validate timezone handling consistency

## Timeline

**Day 1:**
- Complete tasks 1.1-1.3 (Command interface updates)
- Complete tasks 2.1-2.2 (Analysis module updates)

**Day 2:**  
- Complete tasks 3.1-3.3 (Test updates)
- Complete tasks 4.1-4.2 (Documentation updates)
- Complete tasks 5.1-6.3 (Cleanup and QA)

**Total Estimated Time:** 1-2 days