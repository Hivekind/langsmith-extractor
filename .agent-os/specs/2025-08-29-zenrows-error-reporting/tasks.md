# Zenrows Error Reporting Tasks

> Spec: Zenrows Error Reporting
> Created: 2025-08-29
> Status: Ready for Implementation

## Tasks

- [ ] 1. Create Report Command Infrastructure
  - [ ] 1.1 Write tests for report command structure and parameter validation
  - [ ] 1.2 Create `lse/commands/report.py` module with Typer command group
  - [ ] 1.3 Add `zenrows-errors` subcommand with date parameters (--date, --start-date, --end-date)
  - [ ] 1.4 Implement date parameter parsing and validation logic
  - [ ] 1.5 Register report command group with main CLI application
  - [ ] 1.6 Add basic help text and command documentation
  - [ ] 1.7 Verify all tests pass and command appears in CLI help

- [ ] 2. Implement Trace Analysis Engine
  - [ ] 2.1 Write tests for JSON trace parsing and error detection logic
  - [ ] 2.2 Create `lse/analysis.py` module for trace file processing
  - [ ] 2.3 Implement file discovery logic for scanning data directory structure
  - [ ] 2.4 Add JSON parsing with robust error handling for malformed files
  - [ ] 2.5 Implement zenrows_scraper sub-trace detection logic
  - [ ] 2.6 Add error status identification for detected sub-traces
  - [ ] 2.7 Create date extraction from trace timestamps or file paths
  - [ ] 2.8 Verify all tests pass with real trace data

- [ ] 3. Build Data Aggregation and Output System
  - [ ] 3.1 Write tests for aggregation logic and CSV output formatting
  - [ ] 3.2 Create `lse/formatters.py` module for output formatting
  - [ ] 3.3 Implement daily grouping and counting logic for traces and errors
  - [ ] 3.4 Add error rate calculation with percentage formatting
  - [ ] 3.5 Create CSV output formatter with proper headers and formatting
  - [ ] 3.6 Add stdout output handling for easy piping and redirection
  - [ ] 3.7 Implement date range support for multi-day analysis
  - [ ] 3.8 Verify all tests pass and output format matches specification

- [ ] 4. Integration and End-to-End Testing
  - [ ] 4.1 Write integration tests using existing trace files from data directory
  - [ ] 4.2 Test command with single date parameter using real data
  - [ ] 4.3 Test command with date range parameters using real data
  - [ ] 4.4 Verify CSV output format and error rate calculations are accurate
  - [ ] 4.5 Test error handling for invalid dates, missing files, and malformed data
  - [ ] 4.6 Add progress indication for long-running operations on large datasets
  - [ ] 4.7 Verify backward compatibility with existing CLI commands
  - [ ] 4.8 Verify all tests pass including integration scenarios

## Definition of Done

Each task is considered complete when:
1. **Implementation**: Code is written and functional
2. **Testing**: Unit tests pass and achieve target coverage
3. **Integration**: Changes integrate properly with existing CLI structure
4. **Documentation**: Code is documented with docstrings and help text
5. **Validation**: Manual testing confirms expected behavior with real data
6. **Code Quality**: Code passes all linting and formatting checks

## Success Criteria

The implementation is considered successful when:
1. `lse report zenrows-errors --date 2025-08-29` generates accurate CSV output for existing trace data
2. `lse report zenrows-errors --start-date 2025-08-01 --end-date 2025-08-31` processes date ranges correctly
3. Output format exactly matches: "Date,Total Traces,Zenrows Errors,Error Rate"
4. All existing CLI functionality continues to work without changes
5. Error handling is robust and provides helpful user feedback
6. Performance is acceptable for typical datasets (hundreds of trace files)