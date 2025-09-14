# Phase 13: Dataset Format Fix - Task Tracking

## Task Status Overview
- **Phase**: Phase 13.1 - Fix Input Data Extraction  
- **Status**: Ready to Start
- **Priority**: 🚨 URGENT
- **Assigned**: Not assigned
- **Due Date**: TBD

---

## Phase 13.1: Fix Input Data Extraction

### Tasks
- [ ] **Update `_extract_inputs()` method** - Extract clean fields from `input_data` nested structure
  - **File**: `/lse/evaluation.py` lines 806-823
  - **Status**: Pending
  - **Description**: Modify method to extract only clean input fields, ignoring LangChain artifacts
  - **Acceptance Criteria**:
    - Extracts name, symbol, description from `input_data` 
    - Maps `crypto_symbol` to `symbol` field
    - No LangChain message objects in output
    - Handles both database and file format correctly

- [ ] **Add website-specific field extraction**
  - **File**: `/lse/evaluation.py` lines 806-823  
  - **Status**: Pending
  - **Description**: Extract website_url, network, contract_address, social_profiles for website eval type
  - **Acceptance Criteria**:
    - All website fields extracted when present
    - Defaults to empty values for missing fields
    - social_profiles defaults to empty array

- [ ] **Remove LangChain artifacts handling**
  - **File**: `/lse/evaluation.py` lines 806-823
  - **Status**: Pending  
  - **Description**: Ensure no LangChain message structures appear in extracted inputs
  - **Acceptance Criteria**:
    - No `messages` key in output
    - No `id`, `lc`, `type`, `kwargs` keys in output
    - Clean dictionary with only evaluation-relevant fields

- [ ] **Add input extraction tests**
  - **File**: `/tests/test_evaluation_extraction.py` (new file)
  - **Status**: Pending
  - **Description**: Comprehensive tests for input extraction method
  - **Acceptance Criteria**:
    - Tests for token_name input extraction
    - Tests for website input extraction  
    - Tests for handling missing fields
    - Tests for LangChain artifact removal
    - 100% code coverage for `_extract_inputs()` method

### Completion Criteria for Phase 13.1
- [ ] Input extraction produces clean dictionaries with only expected fields
- [ ] No LangChain message objects or framework artifacts in inputs  
- [ ] Token name and website eval types produce correct input field sets
- [ ] Input extraction tests achieve 100% coverage

---

## Phase 13.2: Fix Output Data Extraction

### Tasks
- [ ] **Update `_extract_outputs()` method** - Extract actual evaluation results from nested output structure
  - **File**: `/lse/evaluation.py` lines 825-846
  - **Status**: Not Started
  - **Description**: Navigate through nested analysis structures to extract clean boolean results
  - **Dependencies**: Phase 13.1 completion

- [ ] **Add `_extract_boolean_results()` helper method**
  - **File**: `/lse/evaluation.py` (new method)
  - **Status**: Not Started
  - **Description**: Helper method to extract boolean fields from nested analysis structures
  - **Dependencies**: Phase 13.1 completion

- [ ] **Remove LangChain output artifacts**
  - **File**: `/lse/evaluation.py` lines 825-846
  - **Status**: Not Started
  - **Description**: Ensure no LangChain generation data appears in extracted outputs
  - **Dependencies**: Phase 13.1 completion

- [ ] **Add output extraction tests**
  - **File**: `/tests/test_evaluation_extraction.py`
  - **Status**: Not Started
  - **Description**: Comprehensive tests for output extraction method
  - **Dependencies**: Phase 13.1 completion

### Completion Criteria for Phase 13.2
- [ ] Output extraction produces clean boolean dictionaries matching expected format
- [ ] No raw LangChain outputs or nested generation data in results
- [ ] Boolean fields correctly extracted from nested analysis structures  
- [ ] Output extraction tests achieve 100% coverage

---

## Phase 13.3: Update Format Methods

### Tasks  
- [ ] **Update `_format_token_name()` method** - Simplify to work with clean data
  - **File**: `/lse/evaluation.py` lines 897-975
  - **Status**: Not Started
  - **Description**: Update method to work with clean extracted data
  - **Dependencies**: Phases 13.1 and 13.2 completion

- [ ] **Update `_format_website()` method** - Simplify to work with clean data
  - **File**: `/lse/evaluation.py` lines 977-1071
  - **Status**: Not Started  
  - **Description**: Update method to work with clean extracted data
  - **Dependencies**: Phases 13.1 and 13.2 completion

- [ ] **Add format method tests**
  - **File**: `/tests/test_evaluation_extraction.py`
  - **Status**: Not Started
  - **Description**: Tests for updated format methods
  - **Dependencies**: Phases 13.1 and 13.2 completion

### Completion Criteria for Phase 13.3
- [ ] Format methods work with clean extracted data
- [ ] No redundant processing of already-clean data
- [ ] Format method tests achieve 100% coverage

---

## Phase 13.4: Comprehensive Test Coverage

### Tasks
- [ ] **Create format validation test suite**
  - **File**: `/tests/test_dataset_format.py` (new file)
  - **Status**: Not Started
  - **Description**: Tests that validate exact output format compliance  
  - **Dependencies**: Phases 13.1-13.3 completion

- [ ] **Add integration tests**
  - **File**: `/tests/test_eval_command_integration.py` (new file)
  - **Status**: Not Started
  - **Description**: End-to-end tests of create-dataset command output format
  - **Dependencies**: Phases 13.1-13.3 completion

- [ ] **Create test fixtures**
  - **File**: `/tests/fixtures/evaluation_format_examples.py` (new file)
  - **Status**: Not Started
  - **Description**: Expected format examples for test validation
  - **Dependencies**: Phases 13.1-13.3 completion

- [ ] **Add JSONL format validation**
  - **File**: `/tests/test_dataset_format.py`
  - **Status**: Not Started  
  - **Description**: Tests that validate generated JSONL files match expected format exactly
  - **Dependencies**: All previous phases completion

### Completion Criteria for Phase 13.4
- [ ] End-to-end tests validate complete JSONL output format
- [ ] Format compliance tests catch any deviation from expected structure
- [ ] Test coverage exceeds 95% for all dataset generation code paths
- [ ] Generated datasets pass format validation against expected examples

---

## Testing Strategy

### Unit Tests
- **Input Extraction**: Test `_extract_inputs()` with various trace data structures
- **Output Extraction**: Test `_extract_outputs()` with nested analysis structures  
- **Metadata Generation**: Test metadata field generation and formatting
- **Format Methods**: Test `_format_token_name()` and `_format_website()` with clean data

### Integration Tests
- **Command Testing**: Test complete `lse eval create-dataset` command execution
- **JSONL Validation**: Validate generated JSONL files against expected format
- **Upload Compatibility**: Ensure generated datasets work with upload command
- **Error Handling**: Test graceful handling of malformed or missing data

### Format Compliance Tests
- **Schema Validation**: Validate examples against expected JSON schema
- **Field Presence**: Ensure all required fields are present and correctly typed
- **Artifact Detection**: Detect any LangChain artifacts in output
- **Boolean Validation**: Ensure all output fields are proper boolean types

---

## Risk Assessment

### High Risk Items
- [ ] **Complex nested data extraction** - LangChain output structures are deeply nested and complex
  - **Mitigation**: Comprehensive unit tests for each extraction scenario
  - **Owner**: TBD
  - **Status**: Identified

- [ ] **Test coverage gaps** - Insufficient testing could allow format regressions  
  - **Mitigation**: Achieve >95% test coverage with format compliance tests
  - **Owner**: TBD
  - **Status**: Identified

- [ ] **Breaking existing workflows** - Format changes might affect downstream systems
  - **Mitigation**: Maintain backward compatibility during transition
  - **Owner**: TBD
  - **Status**: Identified

### Medium Risk Items
- [ ] **Performance impact** - Additional data processing might slow dataset generation
  - **Mitigation**: Performance benchmarking and optimization
  - **Owner**: TBD
  - **Status**: Identified

- [ ] **Data structure variations** - Different trace structures might break extraction
  - **Mitigation**: Test with diverse trace data samples
  - **Owner**: TBD  
  - **Status**: Identified

---

## Success Metrics

### Functional Metrics
- [ ] **100% Format Compliance** - All generated datasets match expected JSONL format exactly
- [ ] **Zero LangChain Artifacts** - No framework-specific data structures in output  
- [ ] **Complete Field Coverage** - All expected input/output fields present and correctly typed
- [ ] **Upload Compatibility** - Generated datasets work with existing LangSmith upload workflow

### Quality Metrics  
- [ ] **>95% Test Coverage** - Comprehensive test coverage for all dataset generation code
- [ ] **Zero Format Regressions** - Format validation tests prevent any structural deviations
- [ ] **Performance Maintenance** - Dataset generation performance within acceptable bounds
- [ ] **Error Handling** - Graceful handling of edge cases and malformed data

### Process Metrics
- [ ] **Implementation Timeline** - Complete implementation within planned timeline
- [ ] **Code Review Quality** - All code changes reviewed and approved  
- [ ] **Documentation Completeness** - All changes documented with examples
- [ ] **Deployment Success** - Successful deployment with monitoring in place

---

## Notes

### Implementation Dependencies
- **Database Access**: Requires populated database with evaluation-ready trace data
- **Test Data**: Need diverse trace data samples for comprehensive testing  
- **Expected Examples**: Access to correct format examples for validation
- **Performance Baseline**: Current performance metrics for comparison

### Documentation Updates Required
- Update format examples in `/docs/evaluation.md`
- Add troubleshooting guide for format issues
- Update CLI help text if needed
- Create migration guide for existing users

### Monitoring and Rollback
- Monitor dataset generation performance after deployment
- Set up alerts for format validation failures
- Maintain rollback capability to previous implementation
- Track success metrics post-deployment