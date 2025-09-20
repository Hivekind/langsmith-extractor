# Phase 15: Availability Dataset Root Run Priority Bug Fix - Tasks

## Task Status Overview

### Phase 15.1: Root Run Identification ✅ (M - Must Have)
**Objective**: Separate root run from child runs in trace processing

- [ ] **Implement _identify_trace_hierarchy() method** - Create method to separate root run (trace_id == run_id) from child runs
  - Add method to DatasetBuilder class in evaluation.py
  - Implement logic to identify root run where trace_id equals run_id
  - Return tuple of (root_run, child_runs_list)
  - Handle edge cases where no root run exists

- [ ] **Add root run detection logic** - Core logic for identifying authoritative run
  - Compare trace_id and run_id fields for each run in trace
  - Validate that only one root run exists per trace
  - Log warnings when multiple or zero root runs found
  - Provide fallback logic for malformed traces

- [ ] **Create unit tests for hierarchy identification** - Comprehensive test coverage
  - Test normal case: one root run + multiple child runs
  - Test edge case: no root run (all child runs)
  - Test edge case: multiple root runs (data inconsistency)
  - Test edge case: single run trace (root run only)

- [ ] **Performance benchmark hierarchy identification** - Ensure no significant performance impact
  - Benchmark current trace processing time
  - Measure hierarchy identification overhead
  - Ensure <5% performance degradation
  - Optimize if necessary for large traces

### Phase 15.2: Priority Extraction Logic ✅ (M - Must Have) 
**Objective**: Extract data with root run taking absolute priority for critical fields

- [ ] **Implement _extract_with_priority() method** - Core priority-based extraction logic
  - Create method that takes root_run, child_runs, and eval_type parameters
  - Extract data from root run first (authoritative source)
  - Use child runs only to fill gaps in root run data
  - Apply eval_type-specific priority rules

- [ ] **Add root run data extraction with highest priority** - Ensure authoritative data preserved
  - Extract inputs, outputs, and reference from root run first
  - Mark root run data as authoritative and protected
  - Implement logging to track which run provides each field
  - Handle missing or incomplete root run data gracefully

- [ ] **Implement child run gap-filling logic** - Supplement without overriding
  - Use child runs only for fields missing from root run
  - Never override root run data with child run data for critical fields
  - Preserve root run authority while maximizing data completeness
  - Implement field-level priority rules

- [ ] **Integrate with _build_example_from_runs() method** - Connect new logic to existing workflow
  - Modify _build_example_from_runs to use priority extraction for availability
  - Maintain existing logic for token_name and website eval_types
  - Add conditional logic based on eval_type parameter
  - Ensure seamless integration without breaking existing functionality

### Phase 15.3: Protected Merge Implementation ✅ (M - Must Have)
**Objective**: Prevent child runs from overriding root run's critical data

- [ ] **Implement _merge_with_protection() method** - Safe merging with field protection
  - Create method that takes primary_data, supplement_data, and protected_fields
  - Never overwrite protected fields from primary data
  - Allow supplementation of missing fields from supplement data
  - Support nested dictionary merging with protection

- [ ] **Add protected field definition system** - Define which fields need protection per eval_type
  - Create _get_critical_fields() method for eval_type-specific protection
  - Define protected fields for availability eval_type (is_available, notes)
  - Leave other eval_types unchanged (empty protection lists)
  - Support future expansion for additional eval_types

- [ ] **Implement deep merge logic with field protection** - Handle nested data structures
  - Recursively merge nested dictionaries
  - Apply field protection at all nesting levels
  - Preserve data types during merge operations
  - Handle edge cases like mismatched data types

- [ ] **Create comprehensive test suite for merge protection** - Verify protection logic works
  - Test protected fields are never overwritten
  - Test non-protected fields can be supplemented
  - Test deep merge functionality with nested structures
  - Test edge cases like None values and type mismatches

### Phase 15.4: Availability Field Protection ✅ (M - Must Have)
**Objective**: Define critical fields that must preserve root run authority

- [ ] **Implement _get_critical_fields() method** - Define eval_type-specific field protection
  - Return protected field lists based on eval_type parameter
  - For availability: protect 'is_available' and 'notes' in outputs
  - For other eval_types: return empty lists (no protection)
  - Support future extension for additional eval_types and protected fields

- [ ] **Add availability-specific field protection** - Protect critical availability fields
  - Mark 'is_available' as protected field for availability eval_type
  - Mark 'notes' as protected field for availability eval_type
  - Ensure these fields always come from root run when available
  - Test protection works with real availability dataset generation

- [ ] **Update _extract_availability_notes() for root run priority** - Ensure notes reflect root run assessment
  - Modify availability notes extraction to prioritize root run data
  - Use root run availability status for notes generation logic
  - Only fall back to child run data if root run lacks availability info
  - Update notes to reflect source of availability determination

- [ ] **Create end-to-end testing with Foo trace** - Validate fix with real problematic case
  - Test specific Foo trace (49751c71-4b79-469e-90cb-b83241e3afa1)
  - Verify generated dataset shows is_available: true (root run value)
  - Confirm child run contamination is eliminated
  - Test dataset creation from database to JSONL output

### Phase 15.5: Testing and Validation 🆂 (S - Should Have)
**Objective**: Comprehensive testing to ensure fix works and no regressions

- [ ] **Implement critical test cases** - Core functionality validation
  - Foo URL fix validation test
  - Root run priority enforcement test  
  - Child run supplementation test (fills missing fields only)
  - Multiple child runs with conflicting data test

- [ ] **Create regression test suite** - Ensure other eval_types unchanged
  - Test token_name eval_type maintains existing functionality
  - Test website eval_type maintains existing functionality  
  - Performance regression tests (dataset creation time)
  - Format compliance tests (output structure unchanged)

- [ ] **Add integration tests** - End-to-end workflow validation
  - Database to JSONL dataset creation test
  - Dataset upload compatibility test
  - Format specification compliance test
  - Real trace data processing test

- [ ] **Implement performance benchmarks** - Ensure acceptable performance impact
  - Benchmark current dataset creation time
  - Measure performance impact of root run priority logic
  - Ensure total impact <10% of baseline
  - Optimize if performance targets not met

### Phase 15.6: Documentation and Deployment 🆂 (S - Should Have)
**Objective**: Document changes and prepare for deployment

- [ ] **Update method documentation** - Document new priority extraction logic
  - Add comprehensive docstrings for all new methods
  - Document root run priority behavior
  - Update existing method docs where integration occurs
  - Add examples of root run vs child run data handling

- [ ] **Create deployment validation tests** - Ensure production readiness
  - Create tests that can be run post-deployment
  - Foo URL validation as canary test
  - Sample dataset quality validation tests
  - Performance monitoring tests

- [ ] **Implement monitoring and logging** - Track behavior in production
  - Add logging to track root run identification
  - Log when child run data supplements root run data
  - Monitor for traces where no root run is identified
  - Track performance metrics for root run priority logic

- [ ] **Create rollback plan** - Prepare for potential issues
  - Document steps to disable root run priority if needed
  - Create feature flag for root run priority logic
  - Test rollback procedures
  - Document symptoms that would trigger rollback

## Completion Status

### Overall Progress: 0/24 tasks completed (0%)

#### Phase Breakdown:
- **Phase 15.1** (Root Run Identification): 0/4 tasks (0%) ✅ Ready to start
- **Phase 15.2** (Priority Extraction): 0/4 tasks (0%) ✅ Depends on 15.1
- **Phase 15.3** (Protected Merge): 0/4 tasks (0%) ✅ Depends on 15.2  
- **Phase 15.4** (Availability Protection): 0/4 tasks (0%) ✅ Depends on 15.3
- **Phase 15.5** (Testing): 0/4 tasks (0%) 🆂 Can be done in parallel with implementation
- **Phase 15.6** (Documentation): 0/4 tasks (0%) 🆂 Can be done in parallel

## Next Steps

1. **Start with Phase 15.1** - Begin with root run identification
2. **Critical Test Case First** - Implement Foo URL test as acceptance criteria
3. **Incremental Testing** - Test each phase before proceeding to next
4. **Regression Prevention** - Ensure other eval_types work throughout development

## Dependencies Verified

- ✅ Phase 14 (Availability Evaluation Type) completed
- ✅ Database with Foo trace data available for testing
- ✅ Existing test framework in place
- ✅ Problematic trace identified and accessible

## Success Criteria Reminders

- **Primary**: Foo URL shows `is_available: true` in availability datasets
- **Secondary**: No regression in token_name or website eval_types  
- **Tertiary**: Performance impact <10% of baseline dataset creation time
- **Quality**: >95% test coverage for all new root run priority logic

## Risk Mitigation

- **Regression Risk**: Test all eval_types after each implementation phase
- **Performance Risk**: Benchmark after each phase and optimize if needed
- **Data Risk**: Validate with multiple problematic traces, not just Foo
- **Integration Risk**: Test database-to-JSONL workflow end-to-end frequently
