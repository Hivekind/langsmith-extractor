# Phase 13: Dataset Format Fix - Detailed Specification

## Overview
Fix critical dataset format generation bug where `lse eval create-dataset` produces incorrect JSONL format that doesn't match expected structure for evaluation workflows.

## Problem Statement

### Current Format Issues
1. **Complex Input Structure**: Outputs LangChain message objects instead of clean input fields
2. **Raw Output Data**: Outputs LangChain generation objects instead of clean boolean results  
3. **Unusable for Evaluation**: Generated datasets can't be used with evaluation systems due to format mismatch

### Impact Assessment
- **Severity**: Critical - Blocks evaluation workflows completely
- **Scope**: All evaluation dataset generation (`lse eval create-dataset`)
- **Users Affected**: All users creating evaluation datasets
- **Business Impact**: Cannot perform automated evaluations with generated datasets

## Technical Analysis

### Current Implementation Problems

#### Input Extraction (`_extract_inputs()` - lines 806-823)
**Current behavior**: Extracts raw LangChain message structures
```python
def _extract_inputs(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
    inputs = {}
    trace = trace_data.get("trace", {})
    if "inputs" in trace:
        inputs.update(trace["inputs"])  # This includes LangChain messages
    return inputs
```

**Problem**: Returns complex nested structures like:
```json
{
  "messages": [
    {
      "id": ["langchain", "schema", "messages", "SystemMessage"],
      "type": "constructor",
      "kwargs": {"content": "system prompt..."}
    }
  ],
  "input_data": {"name": "Token", "symbol": "TKN"}
}
```

**Required behavior**: Extract only clean input fields:
```json
{
  "name": "Token Name",
  "symbol": "TKN", 
  "description": "Token description"
}
```

#### Output Extraction (`_extract_outputs()` - lines 825-846)
**Current behavior**: Extracts raw LangChain output structures
```python
def _extract_outputs(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
    outputs = {}
    trace = trace_data.get("trace", {})
    if "outputs" in trace and trace["outputs"] is not None:
        outputs.update(trace["outputs"])  # This includes LangChain generations
    return outputs
```

**Problem**: Returns complex nested structures like:
```json
{
  "run": {...},
  "type": "LLMResult", 
  "llm_output": {...},
  "generations": [...],
  "final_decision": "PASS",
  "name_analysis": {
    "meme_check": {"is_meme": true},
    "explicit_check": {"is_explicit": false}
  }
}
```

**Required behavior**: Extract only clean boolean fields:
```json
{
  "is_meme": true,
  "is_explicit": false,
  "has_conflict": false
}
```

#### Format Transformation Issues
The `_format_token_name()` and `_format_website()` methods (lines 897-1071) are not correctly extracting data from the nested structures because the input extraction provides the wrong data structure.

### Root Cause Analysis
1. **Extraction Methods**: `_extract_inputs()` and `_extract_outputs()` extract all raw data instead of processing it
2. **Data Navigation**: Methods don't navigate properly through the nested LangChain output structure
3. **Format Methods**: `_format_*()` methods expect cleaner input than what they receive

## Solution Design

### 1. Fix Input Data Extraction

#### Updated `_extract_inputs()` Method
```python
def _extract_inputs(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract clean input fields from trace data."""
    inputs = {}
    
    # Handle both database format (direct) and file format (wrapped)
    if "trace" in trace_data:
        trace = trace_data["trace"]
    else:
        trace = trace_data
    
    # Extract from input_data (primary location)
    trace_inputs = trace.get("inputs", {})
    input_data = trace_inputs.get("input_data", {})
    
    if isinstance(input_data, dict):
        # Extract standard fields that appear in both eval types
        for field in ["name", "description"]:
            if field in input_data:
                inputs[field] = input_data[field]
                
        # Extract crypto_symbol as symbol
        if "crypto_symbol" in input_data:
            inputs["symbol"] = input_data["crypto_symbol"]
        elif "symbol" in input_data:
            inputs["symbol"] = input_data["symbol"]
            
        # Extract website-specific fields  
        for field in ["website_url", "network", "contract_address", "social_profiles"]:
            if field in input_data:
                inputs[field] = input_data[field]
    
    return inputs
```

### 2. Fix Output Data Extraction

#### Updated `_extract_outputs()` Method
```python  
def _extract_outputs(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract clean evaluation outputs from trace data."""
    outputs = {}
    
    # Handle both database format (direct) and file format (wrapped)
    if "trace" in trace_data:
        trace = trace_data["trace"]
    else:
        trace = trace_data
        
    # Get outputs from trace level
    trace_outputs = trace.get("outputs", {})
    if not trace_outputs:
        # Fallback to top-level outputs
        trace_outputs = trace_data.get("outputs", {})
    
    # Navigate through nested analysis structures
    name_analysis = trace_outputs.get("name_analysis", {})
    website_analysis = trace_outputs.get("website_analysis", {})
    
    # Extract boolean evaluation results
    self._extract_boolean_results(outputs, name_analysis, website_analysis, trace_outputs)
    
    return outputs

def _extract_boolean_results(self, outputs: dict, name_analysis: dict, 
                           website_analysis: dict, trace_outputs: dict):
    """Extract boolean evaluation results from nested structures."""
    
    # Extract is_meme
    meme_check = (name_analysis.get("meme_check") or 
                 website_analysis.get("meme_check") or 
                 trace_outputs.get("meme_check", {}))
    if isinstance(meme_check, dict):
        outputs["is_meme"] = bool(meme_check.get("is_meme", False))
    else:
        outputs["is_meme"] = bool(trace_outputs.get("is_meme", False))
    
    # Extract is_explicit  
    explicit_check = (name_analysis.get("explicit_check") or
                     website_analysis.get("explicit_check") or
                     trace_outputs.get("explicit_check", {}))
    if isinstance(explicit_check, dict):
        outputs["is_explicit"] = bool(explicit_check.get("is_explicit", False))
    else:
        outputs["is_explicit"] = bool(trace_outputs.get("is_explicit", False))
        
    # Extract trademark/conflict info
    trademark_check = (name_analysis.get("trademark_check") or
                      website_analysis.get("trademark_check") or 
                      trace_outputs.get("trademark_check", {}))
    if isinstance(trademark_check, dict):
        outputs["has_conflict"] = bool(trademark_check.get("has_conflict", False))
        outputs["has_trademark_conflict"] = bool(trademark_check.get("has_conflict", False))
    else:
        outputs["has_conflict"] = bool(trace_outputs.get("has_conflict", False))
        outputs["has_trademark_conflict"] = bool(trace_outputs.get("has_trademark_conflict", False))
        
    # Website-specific fields
    if website_analysis:
        outputs["is_available"] = bool(website_analysis.get("is_available", True))
        
        malicious_check = website_analysis.get("malicious_check", {})
        if isinstance(malicious_check, dict):
            outputs["is_malicious"] = bool(malicious_check.get("is_dangerous", False))
        else:
            outputs["is_malicious"] = bool(trace_outputs.get("is_malicious", False))
```

### 3. Enhanced Format Methods

Since the extraction methods now provide clean data, the format methods need to be updated to work with the cleaner input structure.

#### Update `_format_token_name()` Method  
```python
def _format_token_name(self, inputs: Dict[str, Any], outputs: Dict[str, Any], 
                      reference: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Format data for token_name evaluation type with proper field extraction."""
    
    # Format inputs - extract clean fields only
    formatted_inputs = {
        "name": inputs.get("name", ""),
        "symbol": inputs.get("symbol", ""), 
        "description": inputs.get("description", "")
    }
    
    # Format outputs - extract clean booleans only
    formatted_outputs = {
        "is_meme": outputs.get("is_meme", False),
        "is_explicit": outputs.get("is_explicit", False),
        "has_conflict": outputs.get("has_conflict", False)
    }
    
    return formatted_inputs, formatted_outputs, reference
```

#### Update `_format_website()` Method
```python  
def _format_website(self, inputs: Dict[str, Any], outputs: Dict[str, Any],
                   reference: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Format data for website evaluation type with proper field extraction."""
    
    # Format inputs - include all website fields
    formatted_inputs = {
        "name": inputs.get("name", ""),
        "symbol": inputs.get("symbol", ""),
        "network": inputs.get("network", ""),
        "description": inputs.get("description", ""),
        "website_url": inputs.get("website_url", ""),
        "social_profiles": inputs.get("social_profiles", []), 
        "contract_address": inputs.get("contract_address", "")
    }
    
    # Format outputs - include all website evaluation fields
    formatted_outputs = {
        "is_meme": outputs.get("is_meme", False),
        "is_explicit": outputs.get("is_explicit", False),
        "is_available": outputs.get("is_available", True),
        "is_malicious": outputs.get("is_malicious", False),
        "has_trademark_conflict": outputs.get("has_trademark_conflict", False)
    }
    
    return formatted_inputs, formatted_outputs, reference
```

## Test Strategy

### 1. Format Validation Tests

#### Test File: `/tests/test_dataset_format.py`
```python
import json
import pytest
from lse.evaluation import DatasetBuilder
from tests.fixtures.evaluation_data import EXPECTED_TOKEN_NAME_EXAMPLE, EXPECTED_WEBSITE_EXAMPLE

class TestDatasetFormatCompliance:
    """Test dataset format compliance with expected structure."""
    
    def test_token_name_format_compliance(self):
        """Test that token_name dataset matches expected format exactly."""
        # Setup database with test data
        builder = DatasetBuilder(database=test_db)
        dataset = await builder.create_dataset_from_db(
            project="test-project",
            start_date="2025-01-15", 
            end_date="2025-01-15",
            eval_type="token_name"
        )
        
        assert len(dataset.examples) > 0
        example = dataset.examples[0]
        
        # Validate structure
        assert hasattr(example, 'inputs')
        assert hasattr(example, 'outputs')
        
        # Validate input fields
        required_input_fields = {"name", "symbol", "description"}
        assert set(example.inputs.keys()) == required_input_fields
        assert all(isinstance(example.inputs[field], str) for field in required_input_fields)
        
        # Validate output fields
        required_output_fields = {"is_meme", "is_explicit", "has_conflict"}
        assert set(example.outputs.keys()) == required_output_fields
        assert all(isinstance(example.outputs[field], bool) for field in required_output_fields)
        
    def test_website_format_compliance(self):
        """Test that website dataset matches expected format exactly."""
        builder = DatasetBuilder(database=test_db)
        dataset = await builder.create_dataset_from_db(
            project="test-project",
            start_date="2025-01-15",
            end_date="2025-01-15", 
            eval_type="website"
        )
        
        assert len(dataset.examples) > 0
        example = dataset.examples[0]
        
        # Validate input fields
        required_input_fields = {"name", "symbol", "network", "description", 
                               "website_url", "social_profiles", "contract_address"}
        assert set(example.inputs.keys()) == required_input_fields
        
        # Validate output fields
        required_output_fields = {"is_meme", "is_explicit", "is_available", 
                                "is_malicious", "has_trademark_conflict"}
        assert set(example.outputs.keys()) == required_output_fields
        assert all(isinstance(example.outputs[field], bool) for field in required_output_fields)
        
    def test_jsonl_output_format(self):
        """Test that JSONL output format matches expected structure."""
        # Create dataset and save to JSONL
        output_path = "/tmp/test_dataset.jsonl"
        
        # Run create-dataset command
        result = runner.invoke(app, [
            "eval", "create-dataset", 
            "--project", "test-project",
            "--date", "2025-01-15",
            "--eval-type", "token_name",
            "--output", output_path
        ])
        
        assert result.exit_code == 0
        assert Path(output_path).exists()
        
        # Validate JSONL format
        with open(output_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0
            
            for line in lines:
                example_data = json.loads(line.strip())
                
                # Check structure matches expected format
                assert "inputs" in example_data
                assert "outputs" in example_data
                
                # Check no LangChain artifacts
                assert "messages" not in example_data["inputs"]
                assert "run" not in example_data["outputs"]
                assert "llm_output" not in example_data["outputs"]
                assert "generations" not in example_data["outputs"]
                
                # Check clean boolean outputs
                for field, value in example_data["outputs"].items():
                    assert isinstance(value, bool), f"Field {field} should be boolean, got {type(value)}"
                    
    def test_no_langchain_artifacts(self):
        """Test that no LangChain artifacts appear in output."""
        builder = DatasetBuilder(database=test_db)
        dataset = await builder.create_dataset_from_db(
            project="test-project", 
            start_date="2025-01-15",
            end_date="2025-01-15",
            eval_type="token_name"
        )
        
        for example in dataset.examples:
            # Check inputs don't contain LangChain artifacts
            forbidden_input_keys = {"messages", "id", "lc", "type", "kwargs"}
            assert not any(key in example.inputs for key in forbidden_input_keys)
            
            # Check outputs don't contain LangChain artifacts  
            forbidden_output_keys = {"run", "llm_output", "generations", "type"}
            assert not any(key in example.outputs for key in forbidden_output_keys)
```

### 2. Data Extraction Tests

#### Test File: `/tests/test_evaluation_extraction.py`
```python
class TestDataExtraction:
    """Test data extraction methods."""
    
    def test_extract_inputs_token_name(self):
        """Test input extraction for token_name eval type."""
        trace_data = {
            "trace": {
                "inputs": {
                    "input_data": {
                        "name": "Test Token",
                        "crypto_symbol": "TEST", 
                        "description": "Test description"
                    },
                    "messages": [{"id": ["langchain"], "type": "constructor"}]
                }
            }
        }
        
        builder = DatasetBuilder()
        inputs = builder._extract_inputs(trace_data)
        
        expected = {
            "name": "Test Token",
            "symbol": "TEST",
            "description": "Test description"
        }
        assert inputs == expected
        
    def test_extract_outputs_boolean_conversion(self):
        """Test output extraction converts nested results to booleans."""
        trace_data = {
            "trace": {
                "outputs": {
                    "name_analysis": {
                        "meme_check": {"is_meme": True},
                        "explicit_check": {"is_explicit": False},
                        "trademark_check": {"has_conflict": True}
                    },
                    "final_decision": "PASS",
                    "run": {...},  # Should be ignored
                    "generations": [...]  # Should be ignored  
                }
            }
        }
        
        builder = DatasetBuilder()
        outputs = builder._extract_outputs(trace_data)
        
        expected = {
            "is_meme": True,
            "is_explicit": False, 
            "has_conflict": True
        }
        assert outputs == expected
        
    def test_format_method_integration(self):
        """Test format methods work correctly with clean extracted data."""
        builder = DatasetBuilder()
        
        # Clean input data (as would be produced by updated _extract_inputs)
        inputs = {
            "name": "Test Token",
            "symbol": "TEST",
            "description": "Test description"
        }
        
        # Clean output data (as would be produced by updated _extract_outputs) 
        outputs = {
            "is_meme": True,
            "is_explicit": False,
            "has_conflict": False
        }
        
        formatted_inputs, formatted_outputs, reference = builder._format_token_name(
            inputs, outputs, {}
        )
        
        # Should return clean data unchanged
        assert formatted_inputs == inputs
        assert formatted_outputs == outputs
```

### 3. Integration Tests

#### Test File: `/tests/test_eval_command_integration.py`
```python
class TestEvalCommandIntegration:
    """Test end-to-end evaluation command integration."""
    
    def test_create_dataset_command_output_format(self):
        """Test that create-dataset command produces correct format."""
        # Setup test database with evaluation data
        populate_test_database()
        
        output_path = "/tmp/integration_test.jsonl"
        result = runner.invoke(app, [
            "eval", "create-dataset",
            "--project", "test-project", 
            "--date", "2025-01-15",
            "--eval-type", "token_name",
            "--output", output_path
        ])
        
        assert result.exit_code == 0
        
        # Validate output matches expected format exactly
        with open(output_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                except json.JSONDecodeError as e:
                    pytest.fail(f"Line {line_num} contains invalid JSON: {e}")
                
                # Validate against expected schema
                validate_example_schema(data, "token_name")
                
    def test_dataset_upload_compatibility(self):
        """Test that generated datasets work with upload command."""
        # Create dataset
        dataset_path = "/tmp/upload_test.jsonl" 
        
        create_result = runner.invoke(app, [
            "eval", "create-dataset",
            "--project", "test-project",
            "--date", "2025-01-15", 
            "--eval-type", "token_name",
            "--output", dataset_path
        ])
        assert create_result.exit_code == 0
        
        # Test upload command can process the dataset
        upload_result = runner.invoke(app, [
            "eval", "upload",
            "--dataset", dataset_path,
            "--name", "test_dataset"
        ])
        # Should not fail due to format issues
        assert "format" not in upload_result.output.lower()
        assert "error" not in upload_result.output.lower()

def validate_example_schema(data: dict, eval_type: str):
    """Validate example data against expected schema."""
    # Must have these top-level keys
    assert "inputs" in data
    assert "outputs" in data
    
    if eval_type == "token_name":
        # Token name inputs
        expected_inputs = {"name", "symbol", "description"}
        assert set(data["inputs"].keys()) == expected_inputs
        
        # Token name outputs
        expected_outputs = {"is_meme", "is_explicit", "has_conflict"}
        assert set(data["outputs"].keys()) == expected_outputs
        
    elif eval_type == "website":
        # Website inputs
        expected_inputs = {"name", "symbol", "network", "description", 
                          "website_url", "social_profiles", "contract_address"}
        assert set(data["inputs"].keys()) == expected_inputs
        
        # Website outputs
        expected_outputs = {"is_meme", "is_explicit", "is_available", 
                           "is_malicious", "has_trademark_conflict"}
        assert set(data["outputs"].keys()) == expected_outputs
        
    # All outputs must be boolean
    for field, value in data["outputs"].items():
        assert isinstance(value, bool), f"Output field {field} must be boolean, got {type(value)}"
```

## Implementation Checklist

### Phase 13.1: Input Data Extraction ✅
- [ ] Update `_extract_inputs()` method to extract clean fields only
- [ ] Add logic to extract from `input_data` nested structure  
- [ ] Map `crypto_symbol` to `symbol` field
- [ ] Remove all LangChain message artifacts from inputs
- [ ] Add tests for input extraction with 100% coverage

### Phase 13.2: Output Data Extraction ✅  
- [ ] Update `_extract_outputs()` method to extract clean boolean results
- [ ] Add navigation through nested analysis structures
- [ ] Convert all evaluation results to boolean types
- [ ] Remove all LangChain generation artifacts from outputs
- [ ] Add tests for output extraction with 100% coverage

### Phase 13.3: Format Methods Update ✅
- [ ] Update `_format_token_name()` to work with clean extracted data
- [ ] Update `_format_website()` to work with clean extracted data
- [ ] Ensure format methods produce expected output structure
- [ ] Remove redundant processing now that extraction is clean
- [ ] Add tests for format methods with 100% coverage

### Phase 13.4: Integration Testing ✅
- [ ] Add end-to-end tests for complete dataset generation
- [ ] Add JSONL output format validation tests
- [ ] Add upload compatibility tests  
- [ ] Add format compliance tests against expected examples
- [ ] Achieve >95% test coverage for all dataset generation paths

## Success Criteria

### Functional Requirements ✅
- [ ] `lse eval create-dataset` produces JSONL matching expected format exactly
- [ ] No LangChain artifacts in generated datasets
- [ ] All evaluation fields are clean booleans as expected
- [ ] Generated datasets work with existing upload command
- [ ] Command interface remains unchanged

### Quality Requirements ✅  
- [ ] >95% test coverage for all modified code
- [ ] Format validation tests catch any structural deviations
- [ ] Integration tests validate end-to-end workflow
- [ ] Performance remains within acceptable bounds
- [ ] No breaking changes to existing evaluation workflow

### Documentation Requirements ✅
- [ ] Update format examples in documentation
- [ ] Add troubleshooting guide for format issues
- [ ] Document expected vs current format differences  
- [ ] Provide migration guide if needed
- [ ] Update test documentation

## Risk Mitigation

### Testing Strategy
- **Unit Tests**: Test each extraction method in isolation
- **Integration Tests**: Test complete command workflow  
- **Format Validation**: Validate against known good examples
- **Regression Tests**: Ensure no existing functionality breaks

### Rollback Plan
- Keep original format methods as `_format_*_legacy()` 
- Add feature flag to switch between old/new format if needed
- Maintain backward compatibility during transition period
- Document rollback procedure in case of critical issues

### Performance Monitoring
- Benchmark dataset generation performance before/after changes
- Monitor memory usage during large dataset creation
- Track any performance degradation in database queries
- Set performance regression alerts

## Dependencies

### Technical Dependencies ✅
- Phase 10 (Evaluation Database Migration) completed
- Database populated with trace data for testing  
- Test framework setup for format validation
- Access to expected format examples for comparison

### Resource Dependencies
- Development time allocation for implementation and testing
- Test data setup for comprehensive format validation
- Code review and QA validation resources
- Documentation update resources

## Timeline

### Week 1: Analysis and Design ✅
- Complete format analysis and root cause identification  
- Design extraction method improvements
- Create comprehensive test plan
- Set up test fixtures and expected format examples

### Week 2: Implementation ✅
- Implement updated extraction methods
- Add metadata generation logic
- Update format transformation methods
- Create comprehensive test suite

### Week 3: Testing and Validation ✅
- Run full test suite and achieve >95% coverage
- Perform integration testing with real data
- Validate format compliance against expected examples
- Performance testing and optimization

### Week 4: Documentation and Release ✅  
- Update documentation with new format examples
- Create troubleshooting guides
- Conduct final code review
- Deploy to production with monitoring