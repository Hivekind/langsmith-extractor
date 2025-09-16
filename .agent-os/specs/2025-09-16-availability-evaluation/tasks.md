# Phase 14: Availability Evaluation Type - Tasks

## Task Status

### Phase 14.1: Core Infrastructure ✅ (M - Must Have)
- [ ] **CLI Validation Update** - Add "availability" to supported eval_type options in `/lse/commands/eval.py`
  - Update eval_type validation logic to include "availability"
  - Update help text and error messages
  - Test CLI accepts availability without errors
  
- [ ] **Format Method Implementation** - Add `_format_availability()` method to `/lse/evaluation.py`
  - Create new format method following existing pattern
  - Extract website_url from inputs
  - Format boolean is_available and notes from outputs
  - Return properly formatted inputs, outputs, reference tuple

- [ ] **Integration Update** - Update `_apply_format()` method to handle availability eval_type
  - Add availability case to format dispatch logic
  - Ensure proper routing to `_format_availability()` method
  - Maintain backward compatibility with existing eval_types

- [ ] **Basic Testing** - Create unit tests for new availability functionality
  - Test format method with various input structures
  - Test CLI validation accepts availability
  - Test format dispatch routes to correct method

### Phase 14.2: Data Extraction Logic ✅ (M - Must Have)
- [ ] **Filtering Criteria Update** - Modify `_meets_filtering_criteria()` for availability logic
  - Implement simplified filtering for availability eval_type
  - Create `_has_website_url()` helper method
  - Ensure no high-confidence filtering for availability
  - Maintain strict filtering for token_name and website eval_types

- [ ] **Input Extraction Enhancement** - Update `_extract_inputs()` for website_url extraction
  - Extract website_url from /due-diligence API request parameters
  - Handle nested data structures for website_url location
  - Implement robust extraction from multiple potential locations
  - Return clean inputs dictionary with website_url

- [ ] **Output Extraction Enhancement** - Update `_extract_outputs()` for availability status
  - Extract is_available boolean from trace outputs
  - Extract descriptive notes about availability status
  - Handle various output formats and response patterns
  - Return clean outputs dictionary with availability data

- [ ] **All-Trace Processing** - Ensure availability processes every trace with website_url
  - Verify no high-confidence filtering applied to availability
  - Test that all traces with website_url are included
  - Compare trace counts between availability and other eval_types

### Phase 14.3: Integration & Testing ✅ (M - Must Have)
- [ ] **End-to-End Testing** - Test complete availability workflow
  - Create dataset with availability eval_type
  - Upload availability dataset to LangSmith
  - Run availability evaluation via external API
  - Verify all steps work without errors

- [ ] **Database Integration** - Verify availability works with database queries
  - Test database query filtering for availability traces
  - Verify date range support works with availability eval_type
  - Test single date and date range dataset creation
  - Ensure database performance acceptable with all-trace processing

- [ ] **Format Validation** - Ensure output matches expected dataset format
  - Test generated datasets match specification exactly
  - Validate inputs contain only website_url field
  - Validate outputs contain is_available boolean and notes
  - Test format consistency across different trace types

- [ ] **Performance Testing** - Validate performance with expanded trace processing
  - Benchmark dataset creation time for availability vs other eval_types
  - Test memory usage with all-trace processing
  - Verify database query performance remains acceptable
  - Test large date range processing performance

### Phase 14.4: Documentation & Polish 🆂 (S - Should Have)
- [ ] **Help Text Updates** - Update CLI help messages to include availability
  - Update --eval-type option description
  - Add availability to usage examples
  - Update command help text in all relevant commands
  - Test help text displays correctly

- [ ] **Usage Examples** - Add availability examples to documentation
  - Update README with availability examples
  - Add availability examples to command help
  - Create usage documentation for availability eval_type
  - Update Agent-OS specs with availability information

- [ ] **Error Handling** - Comprehensive error handling for availability
  - Handle missing website_url gracefully
  - Handle malformed availability outputs
  - Provide clear error messages for availability-specific issues
  - Test error scenarios and recovery

- [ ] **Integration Documentation** - Document availability in specs and roadmap
  - Update Phase 6 evaluation specification
  - Update product roadmap with availability feature
  - Create dedicated availability evaluation specification
  - Update technical documentation

## Completion Status

### Overall Progress: 0/16 tasks completed (0%)

#### Phase Breakdown:
- **Phase 14.1** (Core Infrastructure): 0/4 tasks (0%) ✅ Ready to start
- **Phase 14.2** (Data Extraction): 0/4 tasks (0%) ✅ Depends on 14.1  
- **Phase 14.3** (Integration & Testing): 0/4 tasks (0%) ✅ Depends on 14.2
- **Phase 14.4** (Documentation): 0/4 tasks (0%) 🆂 Can be done in parallel

## Next Steps

1. **Start with Phase 14.1** - Implement core infrastructure
2. **CLI Validation** - Update eval_type validation as first task
3. **Format Method** - Implement `_format_availability()` method
4. **Testing** - Add unit tests for each component as implemented

## Dependencies Verified
- ✅ Phase 10 (Evaluation Database Migration) completed
- ✅ Database populated with trace data
- ✅ Existing evaluation infrastructure in place
- ⚠️  Phase 13 (Dataset Format Fix) recommended but not blocking

## Quality Metrics Targets
- **Test Coverage**: >95% for availability-specific code
- **Performance**: Dataset creation time within 2x of current eval_types
- **Format Compliance**: 100% match to specification format
- **Integration Success**: All workflow steps complete without errors