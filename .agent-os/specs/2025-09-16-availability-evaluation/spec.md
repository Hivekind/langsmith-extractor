# Phase 14: Availability Evaluation Type Specification 

## Overview
Add support for "availability" evaluation type to create datasets for URL availability checking. This phase extends existing evaluation capabilities to support simplified website availability evaluation without high-confidence filtering, processing every trace that contains website_url parameters.

## Problem Statement
Current evaluation system limitations for availability checking:
1. **Limited Eval Types**: Only supports "token_name" and "website" evaluation types
2. **High-Confidence Filtering**: Existing eval_types use strict filtering that excludes many traces
3. **Complex Analysis Focus**: Current eval_types designed for AI vs human comparison tasks
4. **Missing URL Availability**: No dedicated evaluation type for simple website availability checking
5. **Due Diligence Gaps**: Cannot create datasets specifically for /due-diligence URL validation workflows

Target improvements:
1. **New Eval Type**: Add "availability" as supported eval_type option
2. **All-Trace Processing**: Include every trace with website_url (no high-confidence filtering)
3. **Simplified Format**: Focus on website_url inputs and boolean is_available outputs
4. **Due Diligence Integration**: Extract website_url from /due-diligence API request parameters
5. **Comprehensive Coverage**: Generate datasets for complete date ranges without trace exclusions

## Solution Design

### Dataset Format Specification

**Input Structure**:
```json
{
  "inputs": {
    "website_url": "https://ethereum.org"
  }
}
```

**Output Structure**:
```json
{
  "outputs": {
    "is_available": true,
    "notes": "Official Ethereum website - should always be accessible"
  }
}
```

**Complete Example Dataset**:
```json
{
  "name": "availability_evaluation_2025_09_16",
  "description": "Website availability checking evaluation dataset",
  "examples": [
    {
      "inputs": {
        "website_url": "https://ethereum.org"
      },
      "outputs": {
        "is_available": true,
        "notes": "Official Ethereum website - should always be accessible"
      }
    },
    {
      "inputs": {
        "website_url": "https://nonexistent-crypto-site-xyz123.com"
      },
      "outputs": {
        "is_available": false,
        "notes": "Non-existent domain - should fail DNS resolution"
      }
    }
  ]
}
```

### Command Interface

**New eval_type option**:
```bash
# Create availability evaluation dataset (single date)
lse eval create-dataset --project my-project --date 2025-01-15 --eval-type availability

# Create availability evaluation dataset (date range)
lse eval create-dataset --project my-project --start-date 2025-01-01 --end-date 2025-01-15 --eval-type availability

# Upload availability dataset to LangSmith
lse eval upload --dataset availability_dataset.json --name availability_eval_2025_01

# Run availability evaluation via external API
lse eval run --dataset-name availability_eval_2025_01 --experiment-prefix avail_check --eval-type availability
```

**Help text update**:
```bash
lse eval create-dataset --help
# --eval-type: Evaluation type: 'token_name', 'website', or 'availability' (required)
```

### Technical Implementation

#### 1. CLI Validation Update
**File**: `/lse/commands/eval.py`

Update eval_type validation:
```python
# Current validation
if eval_type not in ["token_name", "website"]:
    console.print(f"[red]Error: --eval-type must be either 'token_name' or 'website', got '{eval_type}'[/red]")
    raise typer.Exit(1)

# Enhanced validation  
if eval_type not in ["token_name", "website", "availability"]:
    console.print(f"[red]Error: --eval-type must be 'token_name', 'website', or 'availability', got '{eval_type}'[/red]")
    raise typer.Exit(1)
```

#### 2. Dataset Format Method
**File**: `/lse/evaluation.py`

Add `_format_availability()` method:
```python
def _format_availability(
    self,
    inputs: Dict[str, Any],
    outputs: Dict[str, Any], 
    reference: Dict[str, Any],
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Format data for availability evaluation type.
    
    Args:
      inputs: Clean input data (already extracted by _extract_inputs)
      outputs: Clean output data (already extracted by _extract_outputs)  
      reference: Reference data
      
    Returns:
      Formatted inputs, outputs, and reference for availability evaluation
    """
    # Format inputs - extract website_url only
    formatted_inputs = {
        "website_url": inputs.get("website_url", "")
    }
    
    # Format outputs - boolean availability with notes
    formatted_outputs = {
        "is_available": outputs.get("is_available", False),
        "notes": outputs.get("notes", "")
    }
    
    # Reference data minimal (availability doesn't use complex feedback)
    formatted_reference = reference
    
    return formatted_inputs, formatted_outputs, formatted_reference
```

Update `_apply_format()` method:
```python
def _apply_format(
    self,
    inputs: Dict[str, Any],
    outputs: Dict[str, Any],
    reference: Dict[str, Any],
    eval_type: str,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Apply format-specific transformations based on eval_type."""
    if eval_type == "token_name":
        return self._format_token_name(inputs, outputs, reference)
    elif eval_type == "website":
        return self._format_website(inputs, outputs, reference)
    elif eval_type == "availability":  # NEW
        return self._format_availability(inputs, outputs, reference)
    else:
        return inputs, outputs, reference
```

#### 3. Trace Filtering Logic
**File**: `/lse/evaluation.py`

Update `_meets_filtering_criteria()` method:
```python
def _meets_filtering_criteria(self, run_data: Dict[str, Any], eval_type: Optional[str] = None) -> bool:
    """Check if trace meets filtering criteria for dataset inclusion.
    
    Availability eval_type uses simplified filtering - just needs website_url.
    Other eval_types use existing strict criteria.
    """
    if eval_type == "availability":
        # Simplified criteria for availability: just needs website_url
        return self._has_website_url(run_data)
    else:
        # Existing strict criteria for token_name and website eval_types
        return (
            self._has_final_verdict(run_data) and 
            self._has_matching_verdicts(run_data)
        )

def _has_website_url(self, run_data: Dict[str, Any]) -> bool:
    """Check if run_data contains website_url parameter."""
    # Extract website_url from /due-diligence request parameters
    # Implementation depends on trace data structure
    inputs = run_data.get("inputs", {})
    return "website_url" in inputs or self._extract_website_url_from_nested(inputs)
```

#### 4. Data Extraction Updates
**File**: `/lse/evaluation.py`

Update input/output extraction for availability:
```python
def _extract_inputs(self, all_runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract input data from trace runs."""
    # ... existing logic for other eval_types ...
    
    # For availability, focus on website_url extraction
    for run in all_runs:
        inputs = run.get("inputs", {})
        if "website_url" in inputs:
            return {"website_url": inputs["website_url"]}
    
    return {}

def _extract_outputs(self, all_runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract output data from trace runs."""
    # ... existing logic for other eval_types ...
    
    # For availability, extract availability status from outputs
    for run in all_runs:
        outputs = run.get("outputs", {})
        if "is_available" in outputs:
            return {
                "is_available": outputs["is_available"],
                "notes": outputs.get("notes", "")
            }
    
    return {}
```

## Implementation Plan

### Phase 14.1: Core Infrastructure (M)
1. **CLI Validation Update** - Add "availability" to supported eval_type options in commands/eval.py
2. **Format Method** - Implement `_format_availability()` method in evaluation.py
3. **Integration Update** - Update `_apply_format()` to handle availability eval_type
4. **Basic Testing** - Unit tests for new format method and CLI validation

### Phase 14.2: Data Extraction Logic (M)  
1. **Filtering Criteria** - Update `_meets_filtering_criteria()` for availability logic
2. **Input Extraction** - Implement website_url extraction from /due-diligence parameters
3. **Output Extraction** - Implement availability status extraction from outputs
4. **All-Trace Processing** - Ensure no high-confidence filtering for availability eval_type

### Phase 14.3: Integration & Testing (M)
1. **End-to-End Testing** - Test complete workflow from dataset creation to external API
2. **Database Integration** - Verify availability eval_type works with database queries
3. **Format Validation** - Ensure output matches expected dataset format exactly
4. **Performance Testing** - Validate performance with all-trace processing

### Phase 14.4: Documentation & Polish (S)
1. **Help Text Updates** - Update all CLI help messages to include availability
2. **Usage Examples** - Add availability examples to documentation  
3. **Error Handling** - Comprehensive error handling for availability-specific cases
4. **Integration Documentation** - Document availability eval_type in specs and roadmap

## File Structure

```
lse/
├── evaluation.py                    # Enhanced with availability support
│   ├── _format_availability()      # NEW: Format method for availability
│   ├── _apply_format()             # UPDATED: Include availability case
│   ├── _meets_filtering_criteria() # UPDATED: Simplified availability logic
│   ├── _has_website_url()          # NEW: Check for website_url presence
│   ├── _extract_inputs()           # UPDATED: website_url extraction
│   └── _extract_outputs()          # UPDATED: availability status extraction
├── commands/
│   └── eval.py                     # UPDATED: eval_type validation
└── tests/
    ├── test_availability_eval.py   # NEW: Dedicated availability tests
    └── test_eval_command.py        # UPDATED: Include availability test cases
```

## Quality Gates

### Phase 14.1 Completion Criteria
- [ ] CLI accepts "availability" as valid eval_type without errors
- [ ] `_format_availability()` method implemented and returns correct format
- [ ] Unit tests pass for format method and CLI validation
- [ ] Help text updated to include availability option

### Phase 14.2 Completion Criteria  
- [ ] All traces with website_url included in availability datasets (no high-confidence filtering)
- [ ] website_url correctly extracted from /due-diligence API request parameters
- [ ] Availability status correctly extracted from trace outputs
- [ ] Integration tests pass for availability-specific filtering logic

### Phase 14.3 Completion Criteria
- [ ] Complete end-to-end workflow working: create-dataset → upload → run
- [ ] Database queries successfully process availability eval_type
- [ ] Generated datasets match expected format specification exactly
- [ ] Performance acceptable for all-trace processing

### Phase 14.4 Completion Criteria
- [ ] All CLI help messages include availability option
- [ ] Documentation updated with availability examples and usage
- [ ] Error handling covers availability-specific edge cases  
- [ ] Test coverage exceeds 95% for availability-related code

## Success Criteria
- [x] "availability" eval_type supported alongside token_name and website
- [ ] Dataset creation processes ALL traces with website_url (no filtering)
- [ ] Output format matches specification: inputs{website_url}, outputs{is_available, notes}  
- [ ] Integration with existing upload and run commands works seamlessly
- [ ] Performance maintains acceptable levels with expanded trace processing
- [ ] Comprehensive test coverage (>95%) for all availability functionality
- [ ] Documentation and help text updated to reflect new capability

## Testing Strategy

### Unit Tests
- Format method testing with various input/output structures
- CLI validation testing for all eval_type combinations
- Filtering criteria testing for availability vs other eval_types
- Data extraction testing for website_url and availability status

### Integration Tests  
- End-to-end dataset creation with availability eval_type
- Database query integration for availability traces
- Upload and external API integration with availability datasets
- Date range processing with availability eval_type

### Performance Tests
- Large dataset processing with all-trace inclusion
- Database query performance for availability filtering
- Memory usage with expanded trace processing

## Risk Assessment

### Technical Risks
- **Data Structure Variance**: website_url may be nested differently across trace types
- **Availability Detection**: Complex logic needed to determine availability from various response patterns  
- **Performance Impact**: Processing all traces (no filtering) may increase dataset creation time
- **Format Consistency**: Need to ensure availability format matches expected structure exactly

### Mitigation Strategies  
- **Flexible Extraction**: Implement robust website_url extraction from multiple potential locations
- **Pattern Recognition**: Define clear availability detection rules based on response codes and error patterns
- **Performance Optimization**: Use existing database batching for efficient processing
- **Format Validation**: Comprehensive tests to ensure exact format compliance

## Dependencies
- Phase 10 (Evaluation Database Migration) completed ✅
- Phase 13 (Dataset Format Fix) completion recommended for consistency  
- Database populated with traces containing website_url parameters
- External evaluation API supports availability eval_type

## Future Enhancements
- Advanced availability checking patterns (response codes, content validation, SSL verification)
- Batch availability testing with parallel requests
- Historical availability tracking and trend analysis
- Integration with external URL monitoring services