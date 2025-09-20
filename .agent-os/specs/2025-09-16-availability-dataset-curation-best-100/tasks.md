# Phase 16: Availability Dataset Curation (Best 100) - Tasks

## Task Status Overview

### Phase 16.1: CLI and Framework Integration ✅ (M - Must Have)
**Objective**: Add --best-100 CLI parameter and integrate with existing dataset creation workflow

- [ ] **Add --best-100 CLI parameter to eval command** - Integrate with typer CLI framework
  - Add `--best-100` flag to `lse eval create-dataset` command in eval.py
  - Add parameter validation (**CRITICAL**: only allowed for availability eval_type)
  - Add clear help text explaining the feature purpose and availability-only constraint
  - Handle parameter conflicts and provide helpful error messages with guidance

- [ ] **Extend DatasetBuilder constructor for curation mode** - Support curation-enabled instantiation
  - Add `curation_enabled: bool = False` parameter to DatasetBuilder.__init__
  - Store curation flag as instance variable for use in dataset creation
  - Maintain backward compatibility with existing DatasetBuilder usage
  - Add documentation for new curation functionality

- [ ] **Integrate curation logic into create_dataset_from_db workflow** - Connect CLI to curation logic
  - Modify create_dataset_from_db to check curation_enabled flag
  - Add conditional logic for availability eval_type + curation mode
  - Preserve existing behavior for non-curated dataset creation
  - Add curation statistics output to user-facing workflow

- [ ] **Add parameter validation and error handling** - Ensure robust CLI behavior
  - Validate --best-100 only works with --eval-type availability (**CRITICAL CONSTRAINT**)
  - Provide clear error messages for invalid parameter combinations (token_name, website)
  - Add helpful suggestions when users try invalid combinations
  - Test edge cases like empty date ranges with curation enabled

### Phase 16.2: Negative Case Collection ✅ (M - Must Have)
**Objective**: Ensure all false availability cases are captured with proper deduplication

- [ ] **Implement _extract_negative_examples() method** - Core negative case extraction logic
  - Filter all examples for is_available: false cases
  - Implement URL-based deduplication logic
  - Prioritize most recent examples when deduplicating
  - Handle edge cases like missing or malformed URLs

- [ ] **Add URL uniqueness validation for negative cases** - Ensure no duplicate negative examples
  - Create URL normalization logic (handle www, trailing slashes, etc.)
  - Implement deduplication by normalized URL
  - Add validation to catch any duplicate URLs that slip through
  - Log deduplication statistics for transparency

- [ ] **Create comprehensive negative case coverage logic** - Ensure no false negatives missed
  - Validate all is_available: false examples are captured
  - Add logging for negative case discovery and selection
  - Handle malformed data gracefully (missing fields, invalid values)
  - Create fallback logic for edge cases in data structure

- [ ] **Add recency-based prioritization for duplicates** - Keep most valuable negative examples
  - Implement sorting by creation timestamp or run date
  - Prefer examples with more complete data when timestamps equal
  - Add quality scoring for negative examples when multiple duplicates exist
  - Document prioritization logic for transparency

### Phase 16.3: Positive Case Selection ✅ (M - Must Have)
**Objective**: Select representative positive examples with domain diversity optimization

- [ ] **Implement _select_representative_positive_examples() method** - Core positive selection algorithm
  - Group positive examples by domain/subdomain
  - Select best example from each unique domain
  - Fill remaining slots with highest quality examples from any domain
  - Ensure target count reached when sufficient data available

- [ ] **Add domain diversity optimization algorithm** - Maximize website type variety
  - Create domain extraction logic from website URLs
  - Implement domain grouping with proper normalization
  - Prioritize unique domains over multiple examples from same domain
  - Handle edge cases like IP addresses, localhost, invalid URLs

- [ ] **Create quality scoring system for positive examples** - Prioritize high-value examples
  - Implement _calculate_quality_score() method with multiple factors
  - Score based on notes completeness and success indicators
  - Bonus for successful scraping, analysis completion
  - Penalty for unclear status or generic failure messages

- [ ] **Implement slot-filling logic for remaining capacity** - Optimize dataset size utilization
  - Calculate remaining slots after negative examples and unique domains
  - Sort remaining positive examples by quality score
  - Fill slots with highest scoring examples regardless of domain
  - Ensure final dataset reaches target size when possible

### Phase 16.4: Quality Validation and Reporting ✅ (M - Must Have)
**Objective**: Validate curated dataset meets quality requirements and provide clear statistics

- [ ] **Implement _validate_curated_dataset() method** - Comprehensive quality validation
  - Check URL uniqueness across entire dataset (negative + positive)
  - Validate data completeness (website_url, is_available, notes fields)
  - Ensure size constraints met (target size or justified if less)
  - Add validation for data type correctness and format consistency

- [ ] **Add _print_curation_statistics() reporting method** - Detailed curation insight
  - Report negative/positive example counts
  - Show domain diversity statistics for positive examples
  - Display original vs curated dataset size comparison
  - Provide curation ratio and efficiency metrics

- [ ] **Create dataset size and balance validation** - Ensure optimal dataset composition
  - Validate target size achieved or provide clear justification
  - Check balance between negative and positive examples
  - Warn if negative examples exceed reasonable percentage
  - Add warnings for insufficient data scenarios

- [ ] **Implement domain diversity analysis and reporting** - Track positive example variety
  - Count unique domains in curated positive examples
  - Report most common domains and their representation
  - Calculate domain diversity score (unique domains / total positives)
  - Warn if domain concentration too high (lack of diversity)

### Phase 16.5: Testing and Edge Case Handling 🆂 (S - Should Have)
**Objective**: Comprehensive testing coverage and robust edge case handling

- [ ] **Create negative case extraction test suite** - Validate negative case logic
  - Test all negative examples captured from mixed datasets
  - Test URL deduplication with various duplicate scenarios
  - Test recency prioritization with different timestamp formats
  - Test edge cases like malformed URLs, missing fields

- [ ] **Create positive case selection test suite** - Validate positive selection algorithm
  - Test domain diversity optimization with concentrated domains
  - Test quality scoring system with various note patterns
  - Test slot-filling logic with different capacity scenarios
  - Test edge cases like single domain datasets, empty positive sets

- [ ] **Create integration tests for full curation workflow** - End-to-end validation
  - Test complete CLI workflow with --best-100 parameter
  - Test curation with real database data from various date ranges
  - Test curation statistics accuracy and reporting
  - Test error handling for invalid combinations and edge cases

- [ ] **Add edge case handling for insufficient data scenarios** - Robust failure handling
  - Handle date ranges with fewer than 100 total examples
  - Handle datasets with only positive or only negative examples
  - Handle datasets with insufficient domain diversity
  - Provide clear warnings and fallback behavior for all edge cases

### Phase 16.6: Performance and Optimization 🆂 (S - Should Have)
**Objective**: Ensure curation performs efficiently and scales to large datasets

- [ ] **Implement performance benchmarking for curation logic** - Monitor impact
  - Benchmark curation overhead vs non-curated dataset creation
  - Test performance with large date ranges (1000+ examples)
  - Identify bottlenecks in sorting, grouping, and validation logic
  - Ensure <10% overhead requirement met

- [ ] **Add memory efficiency optimizations for large datasets** - Handle scale gracefully
  - Implement streaming/batched processing for very large date ranges
  - Optimize data structures used in curation algorithms
  - Add memory usage monitoring and limits
  - Test with datasets exceeding typical memory constraints

- [ ] **Create curation algorithm optimization** - Improve selection quality
  - Optimize domain extraction and normalization logic
  - Improve quality scoring algorithm based on real dataset analysis
  - Add advanced deduplication logic for similar but not identical URLs
  - Fine-tune curation parameters based on real usage patterns

- [ ] **Add monitoring and logging for production use** - Operational visibility
  - Add detailed logging for curation decisions and statistics
  - Monitor curation success rates and user satisfaction
  - Track domain diversity trends across different date ranges
  - Log performance metrics for ongoing optimization

## Completion Status

### Overall Progress: 0/20 tasks completed (0%)

#### Phase Breakdown:
- **Phase 16.1** (CLI Integration): 0/4 tasks (0%) ✅ Ready to start
- **Phase 16.2** (Negative Cases): 0/4 tasks (0%) ✅ Depends on 16.1
- **Phase 16.3** (Positive Cases): 0/4 tasks (0%) ✅ Depends on 16.1  
- **Phase 16.4** (Quality Validation): 0/4 tasks (0%) ✅ Depends on 16.2, 16.3
- **Phase 16.5** (Testing): 0/4 tasks (0%) 🆂 Can be done in parallel with implementation
- **Phase 16.6** (Performance): 0/4 tasks (0%) 🆂 Optimization phase after core functionality

## Next Steps

1. **Start with Phase 16.1** - Begin with CLI parameter integration
2. **Create comprehensive test cases first** - TDD approach for core algorithms
3. **Implement curation logic incrementally** - Test each stage before proceeding
4. **Validate with real data** - Test with actual database examples throughout development

## Dependencies Verified

- ✅ Phase 15 (Availability Dataset Root Run Priority Bug) completed
- ✅ Existing availability dataset creation functionality
- ✅ Database with availability trace data for testing
- ✅ CLI framework supports additional parameters

## Success Criteria Reminders

- **Primary**: --best-100 creates optimally curated 100-example availability datasets
- **Secondary**: All negative cases included, positive cases show domain diversity
- **Tertiary**: Clear statistics reporting, <10% performance overhead
- **Quality**: >95% test coverage, robust edge case handling

## Risk Mitigation

- **Performance Risk**: Benchmark early and optimize bottlenecks as found
- **Data Quality Risk**: Comprehensive testing with diverse real data scenarios
- **User Experience Risk**: Clear error messages and helpful guidance for invalid usage
- **Scalability Risk**: Test with large datasets and implement memory optimizations

## Implementation Notes

- **🚨 CRITICAL CONSTRAINT**: `--best-100` parameter ONLY works with `--eval-type availability`
- **Domain Extraction**: Use urllib.parse for robust URL domain extraction
- **Quality Scoring**: Start with simple scoring system, iterate based on real data
- **Deduplication**: Consider fuzzy matching for similar URLs (optional enhancement)
- **Statistics**: Rich console output with clear formatting and helpful insights