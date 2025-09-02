# Fix Zenrows Error Detection

## Problem Summary

The `lse report zenrows-errors` command is not detecting errors correctly. When analyzing data from 2025-08-20:
- LangSmith UI shows 17 zenrows_scraper errors
- LSE report shows 0 errors
- Root cause: Current code only searches `child_runs` but they are all `None`

## Root Cause Analysis

### Current Implementation Issues
1. **`extract_zenrows_errors()` only searches child_runs**
   - Function recursively searches `trace.child_runs` for errors
   - All fetched traces have `child_runs: None` (not populated)
   - zenrows_scraper errors occur at root trace level

2. **Missing child_runs data**
   - Archive fetch doesn't use `--include-children` flag
   - LangSmith API returns `child_runs: None` without this flag
   - Even with flag, zenrows errors are at root level

3. **Incorrect assumptions**
   - Code assumes zenrows_scraper is a child operation
   - Actually, zenrows_scraper is often the root trace itself
   - Error status needs to be checked at root level

## Solution Design

### Core Changes

1. **Update `extract_zenrows_errors()` function**
   ```python
   def extract_zenrows_errors(trace_data: Dict[str, Any]) -> List[Dict[str, Any]]:
       errors = []
       
       # Check root trace first
       name = trace_data.get("name", "").lower()
       status = trace_data.get("status", "").lower()
       
       if "zenrows_scraper" in name and status == "error":
           error_record = {
               "id": trace_data.get("id"),
               "name": trace_data.get("name"),
               "status": trace_data.get("status"),
               "error": trace_data.get("error", "Unknown error"),
               "start_time": trace_data.get("start_time"),
               "end_time": trace_data.get("end_time"),
           }
           errors.append(error_record)
       
       # Then check child_runs if they exist
       child_runs = trace_data.get("child_runs")
       if child_runs:  # Only search if not None/empty
           search_child_runs(child_runs)
       
       return errors
   ```

2. **Handle None child_runs gracefully**
   - Check if child_runs exists and is not None
   - Don't fail if child_runs is missing
   - Log warning if expected children are missing

3. **Add support for fetching child runs**
   - Update archive fetch to optionally include children
   - Document performance implications
   - Consider separate analysis mode for deep inspection

## Implementation Tasks

### Phase 1: Fix Core Logic (Priority: HIGH)
- [ ] Update `extract_zenrows_errors()` to check root trace
- [ ] Handle None/missing child_runs gracefully
- [ ] Maintain backward compatibility for traces with children

### Phase 2: Testing (Priority: HIGH)
- [ ] Add unit tests for root-level error detection
- [ ] Test with traces having None child_runs
- [ ] Test with traces having populated child_runs
- [ ] Validate against real 2025-08-20 data (17 errors expected)

### Phase 3: Enhanced Fetching (Priority: MEDIUM)
- [ ] Add `--include-children` flag to archive fetch command
- [ ] Document performance impact of fetching children
- [ ] Update storage to handle larger trace files

### Phase 4: Documentation (Priority: LOW)
- [ ] Update command help text
- [ ] Document error detection logic
- [ ] Add troubleshooting guide

## Success Criteria

1. **Correctness**
   - Report shows 17 errors for 2025-08-20 data
   - Works with both root and child-level errors
   - Handles missing child_runs without failing

2. **Performance**
   - No significant slowdown for existing use cases
   - Efficient handling of large trace files

3. **Compatibility**
   - Existing reports continue to work
   - No breaking changes to API

## Test Data

### Known Test Case: 2025-08-20
- Total traces: 4191 (128 root traces)
- Expected zenrows errors: 17
- All errors at root trace level
- All traces have `child_runs: None`

### Sample Error Trace
```json
{
  "trace": {
    "id": "0435ea26-35a5-4d4d-af8e-e6e1cc8e3de6",
    "name": "zenrows_scraper",
    "status": "error",
    "error": "ReadTimeout(...)",
    "child_runs": null,
    ...
  }
}
```

## Risks and Mitigations

### Risk 1: Breaking existing functionality
- **Mitigation**: Comprehensive test coverage before changes
- **Mitigation**: Keep child_runs search logic intact

### Risk 2: Performance impact
- **Mitigation**: Only check root if name matches pattern
- **Mitigation**: Early return if no errors found

### Risk 3: Missing other error patterns
- **Mitigation**: Log and analyze unmatched errors
- **Mitigation**: Consider generic error detection framework

## Timeline

- **Day 1**: Implement core logic fix
- **Day 1**: Add unit tests
- **Day 1**: Validate with real data
- **Day 2**: Add enhanced fetching (if needed)
- **Day 2**: Update documentation

## Notes

- This is a critical bug affecting production reporting
- Fix should be backwards compatible
- Consider broader refactoring for Phase 5