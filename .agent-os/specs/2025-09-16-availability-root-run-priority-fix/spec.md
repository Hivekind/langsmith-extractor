# Phase 15: Availability Dataset Root Run Priority Bug Fix

## Overview
Critical bug fix for availability dataset creation that ensures root run data takes priority over child run data. This addresses incorrect availability status caused by incomplete child runs overriding correct root run assessments.

## Problem Statement

### 🚨 Critical Data Accuracy Issue
The current availability dataset creation produces incorrect `is_available` status due to child run contamination:

1. **Root Run Authority Ignored**: Root runs (where `trace_id == run_id`) contain the authoritative availability assessment
2. **Child Run Contamination**: Child runs with missing/incomplete `is_available` data override correct root run values  
3. **Sequential Override Flaw**: The `_deep_merge_dict()` approach allows later child runs to overwrite correct root run data
4. **Dataset Corruption**: Generated datasets contain false negative availability status

### Concrete Evidence

**Problematic Case: Foo URL**
- **Database Reality**: Root run shows `is_available: true` ✅
- **Generated Dataset**: Shows `is_available: false` ❌
- **Root Cause**: Child runs without complete website analysis override root run's correct assessment

**Database Structure Analysis**:
```sql
-- Root run (authoritative)
trace_id: 49751c71-4b79-469e-90cb-b83241e3afa1 = run_id: 49751c71-4b79-469e-90cb-b83241e3afa1
website_analysis.is_available: true ✅

-- Child runs (incomplete data)
run_id: db8f994e-dca1-495b-b83a-0558f381aa23, website_analysis.is_available: true
run_id: 38dcdef3-bd24-4260-80cf-f68494e8f19d, website_analysis.is_available: null ❌
run_id: d237da6f-440f-42fc-a45d-9acda66a1e9f, website_analysis.is_available: null ❌
```

### Business Impact
- **Evaluation Reliability**: Availability datasets cannot be trusted for ML evaluation
- **False Negative Bias**: Websites incorrectly marked as unavailable
- **Downstream Effects**: All evaluation workflows using availability datasets are compromised

## Solution Architecture

### Core Principle: Root Run Authority
The fix implements a hierarchical data extraction strategy:

1. **Root Run Priority**: Always prioritize data from run where `trace_id == run_id`
2. **Child Run Supplementation**: Child runs only fill gaps where root run lacks data
3. **Never Override**: Child runs cannot override root run's authoritative fields

### Technical Design

#### Phase 15.1: Root Run Identification
**Objective**: Separate root run from child runs in trace processing

```python
def _identify_trace_hierarchy(self, run_data_list):
    """Separate root run from child runs."""
    root_run = None
    child_runs = []
    
    for run_data in run_data_list:
        if run_data.get('trace_id') == run_data.get('run_id'):
            root_run = run_data
        else:
            child_runs.append(run_data)
    
    return root_run, child_runs
```

#### Phase 15.2: Priority-Based Data Extraction
**Objective**: Extract data with root run taking absolute priority for critical fields

```python
def _extract_with_priority(self, root_run, child_runs, eval_type):
    """Extract data with root run priority for critical fields."""
    
    # Phase 1: Extract from root run (authoritative)
    primary_inputs = self._extract_inputs(root_run) if root_run else {}
    primary_outputs = self._extract_outputs(root_run) if root_run else {}
    primary_reference = self._extract_reference(root_run) if root_run else {}
    
    # Phase 2: Supplement with child run data (gap filling only)
    critical_fields = self._get_critical_fields(eval_type)
    
    for child_run in child_runs:
        child_inputs = self._extract_inputs(child_run)
        child_outputs = self._extract_outputs(child_run)
        child_reference = self._extract_reference(child_run)
        
        # Merge with protection for critical fields
        self._merge_with_protection(primary_inputs, child_inputs, critical_fields.get('inputs', []))
        self._merge_with_protection(primary_outputs, child_outputs, critical_fields.get('outputs', []))
        self._merge_with_protection(primary_reference, child_reference, critical_fields.get('reference', []))
    
    return primary_inputs, primary_outputs, primary_reference
```

#### Phase 15.3: Protected Merge Logic
**Objective**: Prevent child runs from overriding root run's critical data

```python
def _merge_with_protection(self, primary_data, supplement_data, protected_fields):
    """Merge supplement data into primary without overriding protected fields."""
    
    for key, value in supplement_data.items():
        if key in protected_fields and key in primary_data:
            # Skip: Root run data takes priority for protected fields
            continue
        elif key not in primary_data:
            # Allow: Fill missing fields from child runs
            primary_data[key] = value
        elif isinstance(value, dict) and isinstance(primary_data[key], dict):
            # Recurse: Deep merge for nested structures
            self._merge_with_protection(primary_data[key], value, [])
```

#### Phase 15.4: Availability-Specific Field Protection
**Objective**: Define critical fields that must preserve root run authority

```python
def _get_critical_fields(self, eval_type):
    """Define fields that must maintain root run priority."""
    
    if eval_type == "availability":
        return {
            'inputs': [],  # No critical input fields for availability
            'outputs': ['is_available', 'notes'],  # These must come from root run
            'reference': []
        }
    else:
        # Other eval types use existing logic
        return {'inputs': [], 'outputs': [], 'reference': []}
```

### Implementation Plan

#### Phase 15.1: Root Run Identification `M`
**Deliverables**:
- [ ] `_identify_trace_hierarchy()` method implementation
- [ ] Root run detection logic with `trace_id == run_id` comparison
- [ ] Unit tests for root/child run separation
- [ ] Performance benchmarking for hierarchy identification

**Acceptance Criteria**:
- Correctly identifies root run in 100% of test traces
- Child runs properly separated from root run
- No performance degradation >5% for hierarchy identification

#### Phase 15.2: Priority Extraction Logic `M`
**Deliverables**:
- [ ] `_extract_with_priority()` method implementation
- [ ] Root run data extraction with highest priority
- [ ] Child run gap-filling logic that preserves root run authority
- [ ] Integration with existing `_build_example_from_runs()` method

**Acceptance Criteria**:
- Root run data never overridden by child run data for critical fields
- Missing root run fields correctly supplemented by child runs
- Availability eval_type uses priority extraction, others maintain existing logic

#### Phase 15.3: Protected Merge Implementation `M`
**Deliverables**:
- [ ] `_merge_with_protection()` method implementation
- [ ] Protected field definition system
- [ ] Deep merge logic that respects field protection
- [ ] Comprehensive test suite for merge protection

**Acceptance Criteria**:
- Protected fields maintain root run values regardless of child run data
- Non-protected fields can be supplemented by child runs
- Deep merge works correctly for nested data structures

#### Phase 15.4: Availability Field Protection `M`
**Deliverables**:
- [ ] `_get_critical_fields()` method for eval_type-specific protection
- [ ] Availability-specific field protection for `is_available` and `notes`
- [ ] Updated `_extract_availability_notes()` to use root run priority
- [ ] End-to-end testing with Foo trace example

**Acceptance Criteria**:
- Availability datasets show correct root run `is_available` status
- Foo URL correctly shows `is_available: true` in generated datasets
- Notes field reflects root run availability assessment

### Testing Strategy

#### Critical Test Cases

**Test Case 1: Foo URL Fix Validation**
```python
def test_foo_url_availability_fix():
    """Verify Foo URL shows correct availability from root run."""
    trace_id = "49751c71-4b79-469e-90cb-b83241e3afa1"
    
    # Generate availability dataset for trace
    dataset = generate_dataset_for_trace(trace_id, eval_type="availability")
    
    # Find Foo URL example
    foo_example = find_example_by_url(dataset, "https://x.com/FooExample")
    
    # Verify correct availability status from root run
    assert foo_example is not None
    assert foo_example["outputs"]["is_available"] == True  # Root run value
    assert "is_available" in foo_example["outputs"]
```

**Test Case 2: Root Run Priority Enforcement**
```python
def test_root_run_priority_enforcement():
    """Test that root run data takes priority over child run data."""
    
    # Mock trace with conflicting availability data
    root_run = {
        'trace_id': 'test-trace-123',
        'run_id': 'test-trace-123',
        'outputs': {'website_analysis': {'is_available': True}}
    }
    
    child_run = {
        'trace_id': 'test-trace-123', 
        'run_id': 'child-run-456',
        'outputs': {'website_analysis': {'is_available': False}}
    }
    
    builder = DatasetBuilder()
    inputs, outputs, reference = builder._extract_with_priority(
        root_run, [child_run], "availability"
    )
    
    # Root run value should prevail
    assert outputs['is_available'] == True
```

#### Regression Test Suite
- [ ] **Token Name Eval Type**: Ensure existing functionality unchanged
- [ ] **Website Eval Type**: Verify no regression in website evaluation
- [ ] **Empty Root Run**: Test fallback to child runs when root run missing
- [ ] **Multiple Child Runs**: Test priority handling with many child runs
- [ ] **Performance Benchmarks**: Verify <10% performance impact

#### Integration Tests
- [ ] **End-to-End Dataset Creation**: Full workflow from database to JSONL output
- [ ] **Upload Compatibility**: Generated datasets work with existing upload workflow
- [ ] **Format Compliance**: Output format matches availability specification exactly

### Risk Assessment

#### High-Risk Areas
1. **Regression Risk**: Changes could break token_name and website eval_types
2. **Performance Risk**: Root run identification might slow dataset creation
3. **Edge Cases**: Traces without clear root/child hierarchy
4. **Data Structure Variations**: Different trace structures might break hierarchy detection

#### Mitigation Strategies
1. **Selective Application**: Apply root run priority logic only to availability eval_type
2. **Comprehensive Testing**: Test all eval_types before deployment
3. **Performance Monitoring**: Benchmark dataset creation times
4. **Graceful Degradation**: Fall back to existing logic if hierarchy unclear

### Success Metrics

#### Data Accuracy Metrics
- **Correct Availability Status**: 100% of datasets reflect root run `is_available` values
- **Foo Test Case**: Foo URL shows `is_available: true` in all generated datasets
- **No False Negatives**: Elimination of child run contamination causing false unavailability

#### Quality Metrics  
- **Test Coverage**: >95% coverage for all new root run priority logic
- **No Regressions**: Token name and website eval_types maintain 100% existing functionality
- **Performance**: Dataset creation time impact <10%

#### Business Metrics
- **Dataset Reliability**: Availability datasets suitable for ML evaluation workflows
- **Consistency**: Same trace produces same availability status across multiple generations
- **User Confidence**: Stakeholders can trust availability evaluation results

### File Modifications

#### Primary Implementation Files
```
/lse/evaluation.py:
  - _build_example_from_runs() method (~line 691)
  - New _identify_trace_hierarchy() method
  - New _extract_with_priority() method  
  - New _merge_with_protection() method
  - New _get_critical_fields() method
  - Updated _extract_availability_notes() method (~line 1002)
```

#### Test Files
```
/tests/test_evaluation.py:
  - New TestRootRunPriority class with comprehensive test suite
  - Foo URL specific test cases
  - Root run priority enforcement tests
  
/tests/test_eval_command.py:
  - Integration tests for availability eval_type with root run priority
  - Regression tests for existing eval_types
```

#### Configuration Files
```
/tests/fixtures/root_run_test_data.json:
  - Mock trace data for testing root run priority logic
  - Foo URL example trace structure
  - Edge case trace structures for comprehensive testing
```

### Dependencies

#### Required Completions
- Phase 14 (Availability Evaluation Type) ✅ **COMPLETED**
- Database populated with trace hierarchy data ✅ **AVAILABLE**
- Access to Foo trace for testing ✅ **AVAILABLE**

#### Optional Enhancements
- Performance monitoring infrastructure for dataset creation benchmarking
- Automated regression testing pipeline for all eval_types
- Enhanced logging for debugging trace hierarchy issues

### Deployment Strategy

#### Phase 1: Development and Testing
1. Implement root run identification logic
2. Add comprehensive test suite with Foo test case
3. Verify no regressions in existing eval_types

#### Phase 2: Validation and Benchmarking
1. Test with problematic traces from production data
2. Benchmark performance impact
3. Validate data accuracy improvements

#### Phase 3: Production Rollout  
1. Deploy to staging environment
2. Generate test datasets and validate quality
3. Roll out to production with monitoring

### Monitoring and Validation

#### Post-Deploy Validation
- [ ] **Foo URL Verification**: Manually verify Foo shows `is_available: true`
- [ ] **Sample Dataset Review**: Review sample availability datasets for accuracy
- [ ] **Performance Monitoring**: Track dataset creation time metrics
- [ ] **Error Rate Monitoring**: Monitor for any new errors or exceptions

#### Ongoing Monitoring
- [ ] **Data Quality Checks**: Regular validation of availability dataset accuracy
- [ ] **Performance Metrics**: Ongoing tracking of dataset creation performance
- [ ] **User Feedback**: Monitor stakeholder feedback on dataset reliability

This specification provides a comprehensive plan to fix the root run priority bug while maintaining system stability and ensuring data accuracy for availability evaluations.
