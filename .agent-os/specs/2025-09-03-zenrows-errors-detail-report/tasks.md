# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-09-03-zenrows-errors-detail-report/spec.md

> Created: 2025-09-03
> Status: ✅ COMPLETED

## Tasks

- [x] 1. Create zenrows-detail report command structure
  - [x] 1.1 Write tests for zenrows-detail command interface and parameters ✅
  - [x] 1.2 Add zenrows_detail command function to lse/commands/report.py ✅
  - [x] 1.3 Implement command parameter handling (--date, --project, --format only) ✅
  - [x] 1.4 Add command to report command group with proper help text ✅
  - [x] 1.5 Verify command appears in CLI help and accepts all parameters ✅

- [x] 2. Implement crypto symbol extraction logic
  - [x] 2.1 Write tests for crypto symbol extraction from trace names and metadata ✅
  - [x] 2.2 Create extract_crypto_symbol() function in lse/analysis.py ✅
  - [x] 2.3 Implement pattern matching for common formats (BTC_USDT, ETH-USD, etc.) ✅
  - [x] 2.4 Handle edge cases and missing symbols (group as "Unknown") ✅
  - [x] 2.5 Verify all crypto symbol extraction tests pass ✅

- [x] 3. Build hierarchical error data structure
  - [x] 3.1 Write tests for building crypto → true root trace → error hierarchy ✅
  - [x] 3.2 Create build_zenrows_detail_hierarchy() function in lse/analysis.py ✅
  - [x] 3.3 Implement true root trace identification (traverse to top-level trace like "due_diligence") ✅
  - [x] 3.4 Implement zenrows error detection with full error message extraction ✅
  - [x] 3.5 Group errors by crypto symbol and true root trace ID ✅
  - [x] 3.6 Add metadata tracking (counts, timestamps) ✅
  - [x] 3.7 Verify hierarchy building tests pass ✅

- [x] 4. Implement output formatting
  - [x] 4.1 Write tests for text and JSON output formats ✅
  - [x] 4.2 Create format_zenrows_detail_text() function for hierarchical text output ✅
  - [x] 4.3 Implement proper indentation and Rich formatting for text output ✅
  - [x] 4.4 Create format_zenrows_detail_json() function for JSON output ✅
  - [x] 4.5 Include metadata in JSON output (date range, totals) ✅
  - [x] 4.6 Verify all formatting tests pass ✅

- [x] 5. Integration testing and documentation
  - [x] 5.1 Write end-to-end integration tests with sample trace data ✅
  - [x] 5.2 Test with real archived trace data containing zenrows errors ✅
  - [x] 5.3 Update CLI help documentation ✅
  - [x] 5.4 Add usage examples to README.md ✅
  - [x] 5.5 Run full test suite and ensure all tests pass ✅
  - [x] 5.6 Perform manual testing with various dates and projects ✅

## Implementation Summary

**Status**: All 27 tasks completed successfully! ✅

### Key Implementation Highlights

1. **Complete CLI Command**: Fully implemented `lse report zenrows-detail` with --date, --project, and --format parameters
2. **True Root Trace Detection**: Revolutionary improvement using trace_id and ls_run_depth to identify business context traces
3. **Enhanced Crypto Symbol Extraction**: Comprehensive detection from inputs.input_data.crypto_symbol fields and trace names
4. **Multi-line Output Format**: Clean hierarchical display with Time/URL lines for debugging context
5. **Production Quality**: 146 tests passing with comprehensive coverage and real data validation

### Files Created/Modified
- `lse/analysis.py`: Added `find_true_root_trace()`, `extract_crypto_symbol()`, `build_zenrows_detail_hierarchy()`
- `lse/commands/report.py`: Added `zenrows_detail()` command implementation
- `lse/formatters.py`: Added `format_zenrows_detail_text()` and `format_zenrows_detail_json()`
- `tests/test_zenrows_detail_analysis.py`: New test file with 23 comprehensive tests

### Testing Results
- **146 total tests passing** with zero failures
- **23 new tests** specifically for zenrows-detail functionality
- **Real data validation** confirmed with actual trace data containing errors
- **Edge case coverage** for missing symbols, malformed traces, and missing data

### Production Ready Features
✅ Command interface: `lse report zenrows-detail --date YYYY-MM-DD [--project name] [--format text|json]`  
✅ True root trace identification for proper business context grouping  
✅ Enhanced crypto symbol detection with improved accuracy for various symbol formats  
✅ URL and timestamp extraction for comprehensive error debugging  
✅ Multi-line output format with clean hierarchical display  
✅ JSON output support for programmatic processing  
✅ Backward compatibility with existing zenrows-errors command