# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-09-03-zenrows-errors-detail-report/spec.md

> Created: 2025-09-03
> Status: Ready for Implementation

## Tasks

- [ ] 1. Create zenrows-detail report command structure
  - [ ] 1.1 Write tests for zenrows-detail command interface and parameters
  - [ ] 1.2 Add zenrows_detail command function to lse/commands/report.py
  - [ ] 1.3 Implement command parameter handling (--date, --project, --format only)
  - [ ] 1.4 Add command to report command group with proper help text
  - [ ] 1.5 Verify command appears in CLI help and accepts all parameters

- [ ] 2. Implement crypto symbol extraction logic
  - [ ] 2.1 Write tests for crypto symbol extraction from trace names and metadata
  - [ ] 2.2 Create extract_crypto_symbol() function in lse/analysis.py
  - [ ] 2.3 Implement pattern matching for common formats (BTC_USDT, ETH-USD, etc.)
  - [ ] 2.4 Handle edge cases and missing symbols (group as "Unknown")
  - [ ] 2.5 Verify all crypto symbol extraction tests pass

- [ ] 3. Build hierarchical error data structure
  - [ ] 3.1 Write tests for building crypto → trace → error hierarchy
  - [ ] 3.2 Create build_zenrows_detail_hierarchy() function in lse/analysis.py
  - [ ] 3.3 Implement zenrows error detection with full error message extraction
  - [ ] 3.4 Group errors by crypto symbol and root trace ID
  - [ ] 3.5 Add metadata tracking (counts, timestamps)
  - [ ] 3.6 Verify hierarchy building tests pass

- [ ] 4. Implement output formatting
  - [ ] 4.1 Write tests for text and JSON output formats
  - [ ] 4.2 Create format_zenrows_detail_text() function for hierarchical text output
  - [ ] 4.3 Implement proper indentation and Rich formatting for text output
  - [ ] 4.4 Create format_zenrows_detail_json() function for JSON output
  - [ ] 4.5 Include metadata in JSON output (date range, totals)
  - [ ] 4.6 Verify all formatting tests pass

- [ ] 5. Integration testing and documentation
  - [ ] 5.1 Write end-to-end integration tests with sample trace data
  - [ ] 5.2 Test with real archived trace data containing zenrows errors
  - [ ] 5.3 Update CLI help documentation
  - [ ] 5.4 Add usage examples to README.md
  - [ ] 5.5 Run full test suite and ensure all tests pass
  - [ ] 5.6 Perform manual testing with various dates and projects