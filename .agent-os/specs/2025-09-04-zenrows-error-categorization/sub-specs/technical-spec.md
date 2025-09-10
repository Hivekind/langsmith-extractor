# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-09-04-zenrows-error-categorization/spec.md

> Created: 2025-09-04
> Version: 1.0.0

## Technical Requirements

### Error Parsing and Classification

1. **Error Message Analysis**
   - Extend `extract_zenrows_errors()` function in `lse/analysis.py` to parse error messages and HTTP responses
   - Implement regex patterns and string matching to identify error types from trace error messages
   - Extract HTTP status codes from error messages when present
   - Parse timeout indicators from error strings (e.g., "timeout", "timed out", "connection timeout")
   - Identify connection failures from network error messages

2. **Categorization Logic Implementation**
   - Create new function `categorize_zenrows_error(error_record: Dict) -> str` in `lse/analysis.py`
   - Implement classification logic based on error message content and HTTP status codes
   - Return standardized category strings for consistent aggregation
   - Handle edge cases where error messages are incomplete or ambiguous

3. **Data Structure Updates**
   - Modify error record dictionaries to include `category` field
   - Update `analyze_zenrows_errors()` method to return category breakdowns
   - Maintain backward compatibility by keeping existing total error count structure
   - Add category aggregation logic for multi-date and multi-project reports

### Error Category Classifications

Based on comprehensive analysis of production data, the following error categories reflect actual zenrows_scraper failure patterns:

#### 1. Target Resource Issues (51.2% of all errors)
Issues with the target URLs being scraped:

1. **HTTP 404 Not Found**
   - `http_404_not_found`: 61 errors (50.4% of total) - **MOST COMMON**
   - Patterns: `404 Client Error: Not Found for url`
   - Causes: Target websites offline, incorrect URLs, moved/deleted pages
   - Common with websites that go offline or have moved pages
   - Detection: Match "404 Client Error" in error messages

2. **HTTP 503 Service Unavailable**
   - `http_503_service_unavailable`: 1 error (0.8% of total)
   - Patterns: `503 Server Error: Service Unavailable for url`
   - Causes: CDN or server temporarily unavailable
   - Detection: Match "503 Server Error" in error messages

#### 2. ZenRows Proxy Issues (35.5% of all errors)
Issues with ZenRows proxy service processing content:

3. **HTTP 422 Unprocessable Entity**
   - `http_422_unprocessable`: 22 errors (18.2% of total) - **SECOND MOST COMMON**
   - Patterns: `422 Client Error: Unprocessable Entity for url`
   - Causes: Anti-bot detection triggered, complex content ZenRows can't process
   - Common with sites that have complex JavaScript or anti-bot measures
   - Detection: Match "422 Client Error" in error messages

4. **HTTP 413 Request Entity Too Large**
   - `http_413_too_large`: 15 errors (12.4% of total)
   - Patterns: `413 Client Error: Request Entity Too Large for url`
   - Causes: Content exceeds ZenRows size limits (especially PDF files)
   - File type impact: 27 PDF errors out of 121 total (22.3%)
   - Detection: Match "413 Client Error" in error messages

5. **HTTP 400 Bad Request**
   - `http_400_bad_request`: 7 errors (5.8% of total)
   - Patterns: `400 Client Error: Bad Request for url`
   - Causes: Invalid URLs, blocked content types (Google Drive, Instagram)
   - Detection: Match "400 Client Error" in error messages

#### 3. Network Connectivity Issues (13.2% of all errors)
Network and timeout problems:

6. **Read Timeouts**
   - `read_timeout`: 16 errors (13.2% of total)
   - Patterns: `ReadTimeout: HTTPSConnectionPool` with 60-second timeout
   - Common with slow-loading websites or unreliable servers
   - Detection: Match "ReadTimeout" in error messages

7. **Dynamic Categories**
   - `unknown_errors`: Fallback category for unclassified errors
   - New categories can be added dynamically as patterns are discovered

### Production Data Insights

**File Type Distribution**:
- Directory/No Extension URLs: 91 errors (75.2%) - mostly 404 issues
- PDF Files: 27 errors (22.3%) - size/processing limits
- HTML Files: 2 errors (1.7%)

**Common Error Patterns**:
- Slow-loading domains: timeout errors (consistently slow)
- Complex content sites: processing errors (JavaScript-heavy, anti-bot measures)
- Size-heavy sites: processing errors (large files, media-rich content)
- Multiple domains exhibit recurring error patterns

### CSV Output Format Changes

1. **New Column Structure**
   - Maintain existing columns: `date`, `total_traces`, `zenrows_errors`, `error_rate`
   - Add new category columns based on comprehensive production data analysis:
     - `http_404_not_found` (50.4% - most common)
     - `http_422_unprocessable` (18.2% - second most common)
     - `http_413_too_large` (12.4% - PDF/size issues)
     - `read_timeout` (13.2% - network timeouts)
     - `http_400_bad_request` (5.8% - invalid requests)
     - `http_503_service_unavailable` (0.8% - server issues)
     - `unknown_errors` (fallback for new patterns)

2. **CSV Generation Updates**
   - Modify `ReportFormatter.format_zenrows_report()` in `lse/formatters.py`
   - Add new columns to CSV header generation
   - Update row data generation to include category counts
   - Ensure category counts sum to total error count for validation

3. **Aggregation Logic**
   - Update `calculate_error_rates()` to handle category aggregation across date ranges
   - Implement category summing for multi-project reports
   - Maintain percentage calculations for new category columns

### Dynamic Category Management

1. **Category Configuration**
   - Create `lse/error_categories.py` module to manage error category definitions
   - Implement `ErrorCategoryManager` class for runtime category management
   - Load initial categories from configuration file or inline definitions
   - Support for adding new categories without code changes

2. **Category Detection Logic**
   ```python
   # Complete structure based on comprehensive production data analysis
   ERROR_CATEGORIES = {
       # Target Resource Issues (51.2% of all errors)
       'http_404_not_found': {
           'patterns': ['404 Client Error: Not Found'],
           'description': 'Target URL not found or website offline',
           'frequency_pct': 50.4
       },
       'http_503_service_unavailable': {
           'patterns': ['503 Server Error: Service Unavailable'],
           'description': 'CDN or server temporarily unavailable',
           'frequency_pct': 0.8
       },
       
       # ZenRows Proxy Issues (35.5% of all errors)
       'http_422_unprocessable': {
           'patterns': ['422 Client Error: Unprocessable Entity'],
           'description': 'Anti-bot detection or complex content processing failure',
           'frequency_pct': 18.2
       },
       'http_413_too_large': {
           'patterns': ['413 Client Error: Request Entity Too Large'],
           'description': 'Content exceeds size limits (especially PDF files)',
           'frequency_pct': 12.4
       },
       'http_400_bad_request': {
           'patterns': ['400 Client Error: Bad Request'],
           'description': 'Invalid URLs or blocked content types',
           'frequency_pct': 5.8
       },
       
       # Network Connectivity Issues (13.2% of all errors)
       'read_timeout': {
           'patterns': ['ReadTimeout: HTTPSConnectionPool'],
           'description': '60-second timeout exceeded during request',
           'frequency_pct': 13.2
       }
   }
   ```

3. **Unknown Error Logging**
   - Log unclassified error messages to `logs/unknown_errors.log`
   - Include timestamp, project, trace_id, and full error message
   - Enable periodic review for potential new categories
   - Implement `--debug-unknown-errors` flag to output unclassified patterns

4. **Category Expansion Process**
   - Monitor unknown_errors.log for recurring patterns
   - Add new categories to ERROR_CATEGORIES configuration
   - Update CSV column headers dynamically based on active categories
   - Maintain backward compatibility when new categories are added

### Data Processing Flow

1. **Error Extraction Phase**
   ```python
   # In extract_zenrows_errors()
   for trace in traces:
       errors = extract_errors_from_trace(trace)
       for error in errors:
           error['category'] = categorize_zenrows_error(error)
   ```

2. **Aggregation Phase**
   ```python
   # In analyze_zenrows_errors()
   daily_stats = {
       'total_traces': count,
       'zenrows_errors': total_errors,
       'categories': {
           'http_4xx_client_errors': count_4xx,
           'http_5xx_server_errors': count_5xx,
           'timeout_errors': count_timeouts,
           # ... other categories
       }
   }
   ```

3. **Output Generation Phase**
   - Flatten category counts into individual CSV columns
   - Calculate category percentages relative to total errors
   - Generate backward-compatible output with additional columns

## Implementation Approach

### Phase 1: Core Categorization Logic
1. Implement `categorize_zenrows_error()` function based on comprehensive production data patterns
2. Create `ErrorCategoryManager` class for dynamic category management
3. Validate categorization logic against comprehensive production data
4. Test against all 6 major error categories with 100% classification accuracy
5. Implement unknown error logging system for future category discovery
6. Validate error distribution percentages match production data

### Phase 2: Data Structure Integration  
1. Modify `analyze_zenrows_errors()` to collect category statistics
2. Update return data structure to include category breakdowns
3. Implement category aggregation for date ranges and multi-project reports
4. Add validation logic to ensure category counts sum correctly

### Phase 3: Output Format Enhancement
1. Update `ReportFormatter` to handle new category columns
2. Modify CSV generation to include category data
3. Implement backward compatibility tests
4. Add column headers and proper formatting

### Phase 4: Testing and Validation
1. Create comprehensive test cases for each error category
2. Test against historical trace data for accuracy
3. Validate backward compatibility with existing scripts
4. Performance testing with large datasets

## Backward Compatibility

### Command Interface
- No changes to CLI command parameters or flags
- Existing `zenrows-errors` command works identically
- Same date range and project filtering functionality

### Output Structure
- Preserve all existing CSV columns in same positions
- Add new category columns after existing columns
- Maintain existing column naming and data types
- Total error count remains unchanged and accurate

### Data Processing
- Existing aggregation logic continues to work
- Category data is additive - doesn't replace existing functionality
- Error detection logic remains consistent
- Same trace file processing and filtering

## Performance Considerations

### Processing Large Datasets
1. **Memory Optimization**
   - Process traces in batches to avoid memory overflow
   - Use generators for large file processing where possible
   - Implement streaming categorization to minimize memory footprint

2. **CPU Performance**
   - Compile regex patterns once during initialization
   - Use efficient string matching algorithms
   - Cache classification results for repeated error patterns
   - Optimize nested loop processing in error extraction

3. **I/O Efficiency**
   - Maintain existing file reading patterns
   - Minimize additional file system operations
   - Batch write operations for CSV output
   - Use efficient JSON parsing for trace data

### Scalability Targets
- Support processing 10,000+ traces per day without performance degradation
- Handle 100+ error categories without memory issues
- Process multi-month date ranges within reasonable time limits (< 5 minutes)
- Maintain sub-second response for single-day reports

### Error Handling Performance
- Graceful handling of malformed error messages
- Fallback to 'unknown_errors' category for unclassifiable errors
- Avoid exceptions in categorization logic that could slow processing
- Implement logging for categorization statistics and performance metrics