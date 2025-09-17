# Is_Available Report Feature Specification

## Overview

**Specification ID**: 2025-09-17-is-available-report  
**Feature**: Add `is_available` report type for analyzing website availability failures  
**Priority**: Medium  
**Estimated Effort**: 1 week  
**Dependencies**: Phase 11 (Reporting Database Migration)

## Problem Statement

Current reporting infrastructure focuses on zenrows scraper errors, but there's a business need for dedicated analysis of website availability failures. Stakeholders need clear visibility into when `is_available` checks fail, separate from general scraper errors.

### Business Context

The `is_available` field in trace outputs indicates whether a website was accessible during analysis. This data is crucial for:

1. **Operational Monitoring**: Understanding website accessibility patterns
2. **Trend Analysis**: Identifying periods of high unavailability  
3. **Evaluation Alignment**: Complementing availability dataset insights
4. **Business Reporting**: Providing stakeholders with clear availability metrics

### Current Gap

- **No dedicated availability reporting**: Current reports focus on zenrows scraper technical errors
- **Data exists but not analyzed**: `is_available` data is stored but not easily accessible for analysis
- **Business visibility lacking**: Stakeholders need clear availability failure metrics

## Solution Design

### Core Concept

Add a new `lse report is_available` command that:

1. **Analyzes root runs**: Focuses on traces (root runs where `trace_id = run_id`)
2. **Extracts availability data**: Reads `is_available` from `data->'outputs'->'website_analysis'->'is_available'`
3. **Counts failures**: Reports traces where `is_available = false`
4. **Calculates percentages**: Provides failure rate as percentage of total traces
5. **Supports date ranges**: Works with single dates or date ranges
6. **Enables project filtering**: Single project or aggregated across all projects

### Data Source

The report extracts data from the PostgreSQL `runs` table:

```sql
-- Primary data extraction path
data->'outputs'->'website_analysis'->'is_available'

-- Target: Root runs only
WHERE trace_id = run_id
```

### Expected Output Format

CSV format matching existing report conventions:

```csv
date,Trace count,is_available = false count,percentage
2025-09-01,40,3,7.5
2025-09-02,35,1,2.9
2025-09-03,42,5,11.9
```

**Output Columns:**
- `date`: YYYY-MM-DD format (UTC)
- `Trace count`: Total traces with availability data for the date
- `is_available = false count`: Number of traces where `is_available` was false
- `percentage`: `(false count / total count) * 100` rounded to 1 decimal place

## Technical Architecture

### Component Integration

**Existing Infrastructure Reuse:**
- `DatabaseTraceAnalyzer`: Add new method `analyze_is_available_from_db()`
- `ReportFormatter`: Extend to format availability statistics
- `report` CLI command: Add new `is_available` subcommand
- Database connection management: Reuse existing connection pooling

**New Components:**
- Availability-specific SQL queries
- CSV formatting logic for availability data
- CLI parameter validation for the new subcommand

### Database Query Design

**Core Query Structure:**
```sql
SELECT 
    run_date::text as date,
    COUNT(*) as total_traces,
    COUNT(*) FILTER (
        WHERE (data->'outputs'->'website_analysis'->>'is_available')::boolean = false
    ) as false_count,
    ROUND(
        (COUNT(*) FILTER (
            WHERE (data->'outputs'->'website_analysis'->>'is_available')::boolean = false
        ) * 100.0 / COUNT(*)), 1
    ) as percentage
FROM runs 
WHERE trace_id = run_id  -- Root runs only
    AND data->'outputs'->'website_analysis'->'is_available' IS NOT NULL
    {project_filter}
    {date_filter}
GROUP BY run_date
ORDER BY run_date
```

**Query Features:**
- **Root Run Filtering**: `trace_id = run_id` ensures we analyze traces, not individual runs
- **Null Handling**: `IS NOT NULL` filter excludes traces without availability data
- **Aggregation**: `GROUP BY run_date` provides daily statistics
- **Boolean Casting**: `::boolean` ensures proper type handling for true/false values
- **Percentage Calculation**: Database-level calculation with proper rounding

### CLI Command Design

**Command Structure:**
```python
@report_app.command("is_available")
def is_available_command(
    date: Optional[str] = typer.Option(None, "--date", help="Single date (YYYY-MM-DD)"),
    start_date: Optional[str] = typer.Option(None, "--start-date", help="Start date for range"),
    end_date: Optional[str] = typer.Option(None, "--end-date", help="End date for range"),
    project: Optional[str] = typer.Option(None, "--project", help="Project to analyze"),
) -> None:
    """Generate availability failure reports showing is_available=false patterns."""
```

**Parameter Validation:**
- **Date Validation**: Ensure dates are in YYYY-MM-DD format
- **Range Validation**: If using date range, both start_date and end_date required
- **Mutual Exclusion**: Either single date OR date range, not both
- **Project Validation**: Optional project name, defaults to all projects

**Usage Examples:**
```bash
# Single date, all projects
lse report is_available --date 2025-09-01

# Date range, all projects  
lse report is_available --start-date 2025-09-01 --end-date 2025-09-07

# Single date, specific project
lse report is_available --date 2025-09-01 --project crypto-scanner

# Date range, specific project
lse report is_available --start-date 2025-09-01 --end-date 2025-09-07 --project crypto-scanner
```

## Implementation Plan

### Phase 1: Database Analysis Engine

**Objective**: Implement core database query logic for availability analysis

**Tasks:**
1. Add `analyze_is_available_from_db()` method to `DatabaseTraceAnalyzer` class
2. Implement SQL query with proper filtering and aggregation
3. Add date range filtering logic (single date vs range)
4. Implement project filtering (single project vs all projects)
5. Add proper error handling for database connectivity issues

**Deliverables:**
- Method `analyze_is_available_from_db()` in `lse/analysis.py`
- Unit tests for database query logic
- Edge case handling for missing data

**Acceptance Criteria:**
- Database queries return accurate availability statistics
- Date filtering works correctly for both single dates and ranges
- Project filtering supports single projects and aggregated results
- Performance acceptable for typical date ranges (< 30 seconds)

### Phase 2: CLI Command Integration

**Objective**: Add `is_available` subcommand to existing report CLI structure

**Tasks:**
1. Add `is_available` subcommand to report command group in `lse/commands/report.py`
2. Implement parameter validation matching existing report patterns
3. Add comprehensive help text and usage examples
4. Integrate with existing database analyzer infrastructure
5. Add async execution wrapper for database operations

**Deliverables:**
- New `is_available_command()` function in `lse/commands/report.py`
- Parameter validation logic
- Help text and documentation
- Integration tests for CLI functionality

**Acceptance Criteria:**
- CLI command accepts all specified parameters correctly
- Help text provides clear usage guidance with examples
- Parameter validation prevents invalid input combinations
- Error messages provide actionable feedback to users

### Phase 3: Output Formatting and Integration

**Objective**: Format availability statistics into CSV output matching existing patterns

**Tasks:**
1. Extend `ReportFormatter` class to handle availability statistics
2. Implement CSV formatting with proper column headers
3. Add percentage calculation with correct rounding (1 decimal place)
4. Implement edge case handling for zero traces or missing data
5. Ensure output formatting consistency with existing reports

**Deliverables:**
- `format_availability_report()` method in `lse/formatters.py`
- CSV output formatting logic
- Edge case handling
- Format validation tests

**Acceptance Criteria:**
- CSV output matches specification exactly
- Percentage calculations are mathematically correct
- Edge cases handled gracefully without crashes
- Output formatting consistent with existing reports

### Phase 4: Testing and Quality Assurance

**Objective**: Comprehensive testing and validation of the new feature

**Tasks:**
1. Unit tests for database query logic and edge cases
2. Integration tests for end-to-end CLI functionality
3. Performance tests with realistic datasets
4. Error handling tests for various failure scenarios
5. Regression tests to ensure existing functionality unaffected

**Deliverables:**
- Comprehensive test suite in `tests/test_is_available_report.py`
- Performance benchmarks and validation
- Integration tests covering full workflows
- Documentation updates

**Acceptance Criteria:**
- Test coverage exceeds 95% for all new functionality
- Performance tests validate acceptable response times
- Edge case tests cover all identified scenarios
- Integration tests validate end-to-end workflows
- No regressions introduced to existing report functionality

## Quality Gates

### Functional Requirements

**Data Accuracy:**
- [ ] Database queries correctly extract `is_available` values from website_analysis
- [ ] Root run filtering works correctly (`trace_id = run_id`)
- [ ] Boolean casting handles true/false values properly
- [ ] Null values excluded appropriately from analysis

**Date Handling:**
- [ ] Single date filtering works correctly
- [ ] Date range filtering supports start_date/end_date parameters
- [ ] UTC timezone handling consistent with existing reports
- [ ] Date validation prevents invalid date formats

**Project Filtering:**
- [ ] Single project filtering works correctly
- [ ] All-projects aggregation works correctly
- [ ] Project name validation handles invalid project names
- [ ] Empty project results handled gracefully

### Performance Requirements

**Query Performance:**
- [ ] Single date reports complete within 30 seconds
- [ ] 7-day range reports complete within 2 minutes
- [ ] Query performance scales reasonably with data volume
- [ ] Database connections managed efficiently

**Memory Usage:**
- [ ] Report generation uses reasonable memory for large datasets
- [ ] No memory leaks during extended operation
- [ ] Streaming processing for large result sets if needed

### User Experience Requirements

**CLI Interface:**
- [ ] Command interface matches patterns from existing reports
- [ ] Help text provides clear guidance and examples
- [ ] Parameter validation provides actionable error messages
- [ ] Output format enables easy further analysis

**Error Handling:**
- [ ] Clear error messages for all failure scenarios
- [ ] Graceful degradation when data is missing
- [ ] Appropriate handling of database connectivity issues
- [ ] User-friendly messages for common error conditions

## Risk Assessment

### Technical Risks

**Data Availability Risk: Medium**
- **Risk**: `is_available` field may not be present in all traces
- **Impact**: Reports may have incomplete data or fail to generate
- **Mitigation**: Implement robust null checking and clearly document data requirements

**Query Performance Risk: Low**
- **Risk**: Large date ranges could impact database performance
- **Impact**: Slow report generation or database load
- **Mitigation**: Use appropriate database indexes and implement query optimization

**Data Consistency Risk: Low**
- **Risk**: Mixed data formats across different trace versions
- **Impact**: Incorrect availability calculations
- **Mitigation**: Validate data format compatibility and implement robust type checking

### Integration Risks

**Regression Risk: Low**
- **Risk**: Changes to report infrastructure could affect existing functionality
- **Impact**: Existing reports may break or behave differently
- **Mitigation**: Comprehensive regression testing and careful code isolation

**CLI Interface Risk: Low**  
- **Risk**: New command parameters might conflict with existing patterns
- **Impact**: User confusion or interface inconsistency
- **Mitigation**: Follow established CLI patterns and validate interface consistency

### Business Risks

**Stakeholder Expectations Risk: Medium**
- **Risk**: Report data might not align with business understanding of availability
- **Impact**: Confusion about report interpretation or incorrect business decisions
- **Mitigation**: Clear documentation of data sources and calculation methods

**Workflow Integration Risk: Low**
- **Risk**: New reports might not fit into existing analysis workflows
- **Impact**: Low adoption or duplicate effort
- **Mitigation**: Design report format to integrate with existing tools and processes

## Success Criteria

### Data Accuracy Metrics

**Query Correctness: 100%**
- All `is_available` values extracted correctly from database
- Root run filtering works without including child runs
- Boolean type handling works correctly for all values
- Percentage calculations mathematically accurate

**Date and Project Filtering: 100%**
- Date filtering works correctly for single dates and ranges
- Project filtering accurate for single projects and aggregation
- UTC timezone handling consistent with other reports
- Edge cases handled appropriately

### Performance Metrics

**Query Performance:**
- Single date reports: < 30 seconds
- 7-day range reports: < 2 minutes  
- Memory usage: < 1GB for typical datasets
- Database connection efficiency: No connection leaks

### User Experience Metrics

**Interface Consistency: 100%**
- CLI interface matches existing report command patterns
- Help text provides sufficient guidance for all use cases
- Error messages actionable and user-friendly
- Output format enables easy analysis and integration

**Documentation Quality: 100%**
- Complete usage examples for all parameter combinations
- Clear explanation of data sources and calculations
- Integration guidance for existing workflows
- Troubleshooting guidance for common issues

## Dependencies

### Internal Dependencies

**Required:**
- Phase 11 (Reporting Database Migration) ✅ **COMPLETED**
- Existing report command infrastructure ✅ **AVAILABLE**
- PostgreSQL database with runs table ✅ **AVAILABLE**

**Optional:**
- Phase 16 (Availability Dataset Curation) for comprehensive availability analysis
- Enhanced error reporting integration for cross-reference analysis

### External Dependencies

**Database:**
- PostgreSQL database with appropriate indexing for performance
- Sufficient trace data with website_analysis outputs for meaningful reports
- Database access permissions for read operations

**Infrastructure:**
- Python 3.13+ runtime environment
- Required Python packages: asyncpg, sqlalchemy, typer, rich
- Development and testing environment access

### Data Dependencies

**Trace Data Requirements:**
- Traces must contain `data->'outputs'->'website_analysis'->'is_available'` field
- Root runs identifiable via `trace_id = run_id` condition
- Sufficient historical data for meaningful trend analysis
- Data consistency across different trace versions

## Validation Plan

### Test Coverage Requirements

**Unit Tests: >95% coverage**
- Database query logic with various input combinations
- Date filtering and validation logic
- Project filtering and aggregation logic
- CSV formatting and percentage calculations
- Error handling for all failure scenarios

**Integration Tests: Full workflow coverage**
- End-to-end CLI command execution
- Database connectivity and query execution
- Output formatting and file generation
- Error scenarios and edge cases

**Performance Tests: Baseline establishment**
- Single date query performance measurement
- Date range query performance measurement
- Memory usage profiling with large datasets
- Database connection efficiency validation

### Acceptance Testing

**Business Validation:**
- Stakeholder review of sample report outputs
- Validation of percentage calculations against manual verification
- Confirmation of report utility for business analysis workflows
- User experience validation with representative users

**Technical Validation:**
- Database query accuracy verification with known test data
- Output format validation against specification
- Performance validation against established benchmarks
- Error handling validation across failure scenarios

## Conclusion

The `is_available` report feature provides essential visibility into website availability patterns by analyzing trace data stored in the PostgreSQL database. The implementation leverages existing infrastructure while adding targeted availability analysis capabilities.

**Key Benefits:**
- **Business Visibility**: Clear metrics on website availability failures
- **Operational Insights**: Trend analysis for availability patterns
- **Integration**: Seamless integration with existing reporting infrastructure
- **Performance**: Efficient database queries optimized for large datasets

**Implementation Approach:**
- **Incremental**: Build on existing reporting infrastructure
- **Consistent**: Match established CLI and output patterns
- **Robust**: Comprehensive error handling and edge case coverage
- **Tested**: Extensive test coverage ensuring reliability

The feature directly addresses the business need for availability-specific reporting while maintaining consistency with existing LSE reporting capabilities.