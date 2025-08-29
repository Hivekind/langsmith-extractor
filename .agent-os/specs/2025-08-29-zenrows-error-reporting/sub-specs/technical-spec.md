# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-29-zenrows-error-reporting/spec.md

> Created: 2025-08-29
> Version: 1.0.0

## Technical Requirements

### Command Structure Integration
- Add new `report` command group to existing Typer CLI application
- Implement `zenrows-errors` subcommand with date filtering parameters
- Maintain existing CLI patterns for parameter validation and error handling
- Integrate with existing logging and progress indication systems

### Trace File Analysis
- Scan existing JSON trace files in `data/{project}/{date}/` directory structure
- Parse JSON trace structure to identify nested sub-traces (child runs)
- Implement efficient file discovery and filtering by date ranges
- Handle large trace files without loading entire contents into memory

### Error Detection Logic
- Search for sub-traces with `name` field matching "zenrows_scraper"
- Check `status` or `error` fields to identify Error state
- Support case-insensitive matching for robustness
- Handle missing or malformed trace structure gracefully

### Data Aggregation Engine
- Group traces by date extracted from trace timestamps or file paths
- Calculate daily totals: total traces processed and zenrows errors found
- Compute error rates as percentage with configurable decimal precision
- Support both single-date and date-range aggregations

### Output Formatting
- Generate CSV format with headers: "Date,Total Traces,Zenrows Errors,Error Rate"
- Output to stdout for easy piping and redirection
- Format error rates as percentages (e.g., "4.5%")
- Ensure consistent date formatting (YYYY-MM-DD)

### Performance Considerations
- Stream process large directories of trace files
- Use generators for memory-efficient file processing
- Implement progress indication for long-running operations
- Cache file metadata to avoid repeated filesystem operations

### Error Handling
- Validate date parameters and ranges before processing
- Handle missing or corrupted JSON files gracefully
- Provide clear error messages for invalid date formats
- Skip unreadable files with warning messages rather than failing

## Approach

### Phase 1: Core Command Infrastructure
1. Add `lse/commands/report.py` module with Typer command structure
2. Implement date parameter parsing and validation
3. Add command registration to main CLI application
4. Create basic file discovery for trace directories

### Phase 2: Trace Analysis Engine
1. Create `lse/analysis.py` module for trace parsing logic
2. Implement JSON parsing with error detection
3. Add zenrows_scraper pattern matching
4. Test with existing trace files from data directory

### Phase 3: Aggregation and Output
1. Implement daily grouping and error rate calculations
2. Add CSV formatting and stdout output
3. Support for date ranges and batch processing
4. Integration testing with real trace data

### Code Organization
```
lse/
├── commands/
│   ├── fetch.py          # Existing
│   └── report.py         # New - report commands
├── analysis.py           # New - trace analysis logic
└── formatters.py         # New - output formatting utilities
```

## Dependencies

No new external dependencies required. The implementation will use:
- Existing JSON parsing (Python standard library)
- Existing Typer CLI framework
- Existing file system utilities
- Existing date/time handling with datetime module