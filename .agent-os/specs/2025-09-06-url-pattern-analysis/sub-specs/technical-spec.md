# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-09-06-url-pattern-analysis/spec.md

> Created: 2025-09-06
> Version: 1.0.0

## Technical Requirements

### CLI Command Structure
- Add new `lse report zenrows-url-patterns` command following existing Typer patterns
- Reuse existing date filtering options (`--date`, `--start-date`, `--end-date`)
- Add URL-specific options:
  - `--top N`: Limit results to top N URLs/domains/file types (default: 20)
  - `--group-by`: Group by 'domain', 'file-type', or 'both' (default: 'both')
  - `--format`: Output format (table, csv) (default: table)
  - `--project`: Filter by LangSmith project (reuse existing parameter)

### URL Extraction and Processing
- Leverage existing `target_url` field extraction from `lse/analysis.py`
- Implement URL parsing using standard library `urllib.parse.urlparse`
- Create domain extraction function to normalize URLs to domains
- Extract file extensions from URL paths to identify content types
- Classify file types: PDFs (.pdf), images (.jpg, .png, .gif), API endpoints (/api/, .json), HTML pages (no extension or .html)
- Handle URL edge cases (missing protocols, malformed URLs, query parameters)

### Domain and File Type Analysis Engine
- Implement domain frequency analysis from ZenRows error traces
- Implement file type frequency analysis from URL extensions
- Calculate error rates and counts per domain and file type
- Integrate with existing error categorization system from `lse/error_categories.py`
- Provide breakdown of error types per domain and file type
- Cross-correlate domains with file types for comprehensive analysis

### Integration with Existing Systems
- Extend existing trace analysis pipeline in `lse/analysis.py`
- Reuse existing date filtering and project filtering logic
- Leverage existing error categorization from `ErrorCategoryManager`
- Follow existing CLI command patterns from `lse/cli.py`

### Output Formatting
- Console output using existing Rich table formatting patterns
- CSV export using existing formatter infrastructure
- Table columns:
  - Domain/URL/File Type
  - Total Error Count
  - Error Rate (%)
  - Top Error Categories
  - File Type (when grouping by domain)
  - Domain (when grouping by file type)
  - First/Last Seen

### Performance Considerations
- Use existing trace loading infrastructure for memory efficiency
- Process URLs in batches for large datasets
- Cache domain extractions to avoid redundant parsing

## Implementation Approach

### Phase 1: Core URL Analysis Logic
- Add `extract_domain_from_url()` and `extract_file_type_from_url()` utility functions
- Create file type classification system (PDF, image, API, HTML, other)
- Extend `TraceAnalyzer.analyze_zenrows_errors()` with domain and file type grouping
- Create domain and file type statistics calculation logic

### Phase 2: CLI Integration
- Add `report_zenrows_url_patterns` command to `lse/cli.py`
- Implement argument parsing and validation
- Connect to existing trace loading and filtering

### Phase 3: Output Formatting
- Extend existing table formatters for domain and file type analysis
- Add CSV export capability following existing patterns
- Implement Rich console output for domain and file type statistics
- Support different grouping modes (domain-only, file-type-only, combined)

### File Changes Required
- `lse/cli.py` - Add new `zenrows-url-patterns` subcommand to report group
- `lse/analysis.py` - Extend with domain and file type analysis functionality
- `lse/utils.py` - Add URL parsing and file type classification utilities
- `tests/test_analysis.py` - Add tests for URL pattern and file type analysis

## External Dependencies

No new external dependencies required. Implementation uses:
- Standard library `urllib.parse` for URL parsing
- Existing project dependencies (Typer, Rich, Pydantic)
- Existing error categorization and trace analysis infrastructure