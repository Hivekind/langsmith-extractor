# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-09-03-zenrows-errors-detail-report/spec.md

## Technical Requirements

### Command Implementation
- Create new Typer command `zenrows_detail` in the report command group
- Command name in CLI: `lse report zenrows-detail`
- Support single date parameter (`--date`) only - consistent with archive commands
- Include `--project` parameter for project-specific filtering
- Add `--format` parameter with options: "text" (default) and "json"

### Data Processing Pipeline
1. **Trace Loading**
   - Load traces from storage based on date and project filters
   - Reuse existing `TraceStorage.load_traces()` functionality
   
2. **Crypto Symbol Extraction**
   - Parse trace `name` field for cryptocurrency symbols (BTC, ETH, SOL, etc.)
   - Check trace `metadata` and `extra` fields for symbol information
   - Look for patterns like "BTC_USDT", "ETH-USD", or standalone symbols
   - Handle missing symbols gracefully (group under "Unknown")

3. **Error Detection and Extraction**
   - Identify zenrows_scraper traces with status="error"
   - Extract error messages from trace `error` field
   - Preserve full error text for detailed reporting
   - Track root trace ID for each error

4. **Hierarchical Data Structure**
   ```python
   {
     "BTC": {
       "trace_123_abc": [
         "Connection timeout after 30s",
         "Proxy authentication failed"
       ],
       "trace_456_def": [
         "Rate limit exceeded"
       ]
     },
     "ETH": {
       "trace_789_ghi": [
         "Invalid API response"
       ]
     }
   }
   ```

### Output Formatting

#### Text Format (Default)
- Use Rich library for colored, indented output
- Three-level indentation: crypto (0), trace (2 spaces), error (4 spaces)
- Include trace timestamps and IDs for reference
- Show error counts at each level

#### JSON Format
- Output raw hierarchical data structure
- Include metadata: date range, total errors, total traces
- Ensure valid JSON for programmatic consumption

### Performance Considerations
- Process traces in batches to handle large datasets
- Use generators where possible to minimize memory usage
- Cache crypto symbol extraction results within a report run
- Leverage existing trace loading optimizations

### Error Handling
- Handle missing or corrupted trace files gracefully
- Provide clear error messages for invalid date format
- Validate project existence before processing
- Handle traces with missing or malformed error data

### Integration Points
- Extend existing `lse/commands/report.py` module
- Reuse `TraceStorage` class for data access
- Leverage existing date parsing utilities
- Use established Rich formatting patterns from other reports