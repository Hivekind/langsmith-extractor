# Phase 6: Evaluation Feature - Task Breakdown (Revised)

## Task List

### 1. Setup & Infrastructure
- [ ] Add langsmith SDK dependencies to pyproject.toml
- [ ] Add HTTP client dependencies for external API integration
- [ ] Create lse/evaluation.py module with base classes
- [ ] Create lse/commands/eval.py for CLI commands
- [ ] Register eval command group in lse/cli.py

### 2. Extract Traces Command
- [ ] Implement TraceExtractor class in evaluation.py
- [ ] Add logic to identify traces with AI outputs
- [ ] Add logic to identify traces with human feedback
- [ ] Create extract_traces CLI command
- [ ] Add JSON output formatting for trace IDs
- [ ] Add required project parameter (consistent with archive commands)
- [ ] Write unit tests for extraction logic

### 3. Create Dataset Command
- [ ] Implement DatasetBuilder class in evaluation.py
- [ ] Add trace data loading from local storage
- [ ] Extract inputs from trace data (query, context, etc.)
- [ ] Extract AI outputs (recommendations, responses)
- [ ] Extract human feedback as reference data
- [ ] Format as LangSmith dataset structure
- [ ] Create create_dataset CLI command
- [ ] Write unit tests for dataset creation

### 4. Upload Dataset Command
- [ ] Implement LangSmithUploader class in evaluation.py
- [ ] Add LangSmith client initialization
- [ ] Implement dataset creation via SDK
- [ ] Add example upload logic
- [ ] Create upload CLI command
- [ ] Add error handling for network issues
- [ ] Write unit tests with mocked API calls

### 5. Run External API Command
- [ ] Implement EvaluationAPIClient class in evaluation.py
- [ ] Add external API endpoint configuration loading
- [ ] Implement signature-based authentication logic
- [ ] Create payload builder for external API requests
- [ ] Add HTTP POST request handling
- [ ] Create run CLI command with new parameters
- [ ] Add error handling for external API responses
- [ ] Write unit tests for external API integration

### 6. Format-Specific Dataset Generation
- [ ] Research eval_type format requirements
- [ ] Implement format-specific dataset builders
- [ ] Add eval_type validation logic
- [ ] Update DatasetBuilder to support multiple formats
- [ ] Add format selection logic based on eval_type
- [ ] Write unit tests for format-specific generation
- [ ] Document supported eval_type values and formats

### 7. External API Integration & Testing
- [ ] Create comprehensive integration tests with mocked external API
- [ ] Test signature authentication with sample payloads
- [ ] Test with sample trace data and various eval_types
- [ ] Verify all commands work together in workflow
- [ ] Add error handling for external API failures
- [ ] Test network error recovery
- [ ] Update documentation with external API details

### 8. Documentation & Polish
- [ ] Update README with revised eval commands
- [ ] Add external API integration examples to CLAUDE.md
- [ ] Create eval command help text for all 4 commands
- [ ] Document EVAL_API_ENDPOINT environment variable
- [ ] Document signature authentication requirements
- [ ] Run full test suite
- [ ] Run linting and formatting

## Implementation Order

### Phase 1: Foundation
1. Setup & Infrastructure
2. Extract Traces Command
3. Create Dataset Command

### Phase 2: Integration
1. Upload Dataset Command
2. Run External API Command
3. Format-Specific Dataset Generation

### Phase 3: Testing & Documentation
1. External API Integration & Testing
2. Documentation & Polish
3. Final testing and validation

## Code Organization

### New Files
```
lse/
├── evaluation.py          # Core evaluation logic
│   ├── TraceExtractor    # Extract suitable traces
│   ├── DatasetBuilder    # Build LangSmith datasets (format-aware)
│   ├── LangSmithUploader # Upload to LangSmith
│   └── EvaluationAPIClient # External API communication & authentication
├── commands/
│   └── eval.py           # CLI commands (4 commands)
│       ├── extract_traces()
│       ├── create_dataset()
│       ├── upload()
│       └── run()         # External API integration
tests/
├── test_evaluation.py    # Unit tests for evaluation.py
├── test_eval_command.py  # Tests for CLI commands
└── test_external_api.py # Tests for external API integration
```

### Modified Files
```
lse/cli.py               # Register eval command group
lse/config.py            # Add EVAL_API_ENDPOINT configuration
pyproject.toml           # Add langsmith and HTTP client dependencies
```

## Testing Checklist

### Unit Tests
- [ ] TraceExtractor filters traces correctly for evaluation
- [ ] DatasetBuilder formats data for different eval_types
- [ ] LangSmithUploader handles API errors gracefully
- [ ] EvaluationAPIClient generates signatures correctly
- [ ] EvaluationAPIClient handles HTTP errors and retries

### Integration Tests
- [ ] Full workflow from extraction to external API call
- [ ] Error handling for missing trace data
- [ ] Network error recovery for both LangSmith and external APIs
- [ ] Large dataset handling and upload
- [ ] External API authentication and payload validation

### Manual Testing
- [ ] Test with real trace data from various projects
- [ ] Verify LangSmith dataset upload integration
- [ ] Test external API integration with different eval_types
- [ ] Validate command help text for all 4 commands
- [ ] Test signature authentication with external API

## Definition of Done

- [ ] All 4 eval commands implemented (extract-traces, create-dataset, upload, run)
- [ ] External API integration with signature authentication working
- [ ] Format-specific dataset generation for different eval_types
- [ ] Comprehensive test coverage (>90%)
- [ ] All tests passing
- [ ] Code linted and formatted
- [ ] Documentation updated with external API details
- [ ] Successfully created and uploaded sample dataset
- [ ] Successfully initiated external API evaluation
- [ ] PR ready for review