# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-09-06-url-pattern-analysis/spec.md

> Created: 2025-09-06
> Status: Ready for Implementation

## Tasks

### 1. Core URL Analysis Utilities

- [x] 1.1 Write tests for URL parsing utilities (`test_utils.py`)
- [x] 1.2 Implement `extract_domain_from_url()` function in `lse/utils.py`
- [x] 1.3 Implement `classify_file_type()` function in `lse/utils.py`
- [x] 1.4 Add file type classification rules (PDFs, images, APIs, HTML)
- [x] 1.5 Handle edge cases (malformed URLs, missing extensions, query parameters)
- [x] 1.6 Verify all URL parsing tests pass

### 2. Domain and File Type Analysis Engine

- [ ] 2.1 Write tests for domain/file type analysis functions (`test_analysis.py`)
- [ ] 2.2 Extend `lse/analysis.py` with `analyze_url_patterns()` function
- [ ] 2.3 Integrate with existing error categorization system
- [ ] 2.4 Implement domain frequency counting and sorting
- [ ] 2.5 Implement file type distribution analysis
- [ ] 2.6 Add filtering by date range (reuse existing logic)
- [ ] 2.7 Handle traces without URL data gracefully
- [ ] 2.8 Verify all analysis tests pass

### 3. CLI Command Implementation

- [ ] 3.1 Write tests for new CLI command (`test_cli.py`)
- [ ] 3.2 Add `zenrows-url-patterns` command to `lse/cli.py`
- [ ] 3.3 Implement date range filtering arguments (`--start-date`, `--end-date`)
- [ ] 3.4 Add output format options (`--format table/csv`)
- [ ] 3.5 Integrate with existing trace loading pipeline
- [ ] 3.6 Add error handling for missing trace data
- [ ] 3.7 Verify CLI command tests pass

### 4. Output Formatting and Display

- [ ] 4.1 Write tests for URL pattern formatters (`test_formatters.py`)
- [ ] 4.2 Create `format_url_patterns_table()` in `lse/formatters.py`
- [ ] 4.3 Implement Rich console table for domain analysis
- [ ] 4.4 Implement Rich console table for file type analysis
- [ ] 4.5 Create CSV export functionality for URL patterns
- [ ] 4.6 Add summary statistics display (total domains, file types, traces analyzed)
- [ ] 4.7 Verify all formatting tests pass

### 5. Integration and Quality Assurance

- [ ] 5.1 Run end-to-end testing with real trace data
- [ ] 5.2 Test CLI command with various date ranges
- [ ] 5.3 Verify CSV output format matches specification
- [ ] 5.4 Test error handling with malformed/missing data
- [ ] 5.5 Run linting and formatting (`ruff check --fix . && ruff format .`)
- [ ] 5.6 Update CLI help documentation
- [ ] 5.7 Verify all tests pass across the entire test suite
- [ ] 5.8 Performance test with large datasets