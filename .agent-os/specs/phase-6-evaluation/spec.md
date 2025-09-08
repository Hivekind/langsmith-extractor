# Phase 6: LangSmith Evaluation Capabilities Specification

## Overview
Add evaluation capabilities to integrate with external evaluation APIs for running evaluations on LangSmith datasets. This feature enables dataset creation from historical traces and automated evaluation workflows via external API integration.

## Problem Statement
Currently, there's no automated way to:
1. Extract suitable traces for evaluation dataset creation
2. Create LangSmith datasets from historical trace data
3. Upload datasets to LangSmith for external evaluation
4. Integrate with external evaluation APIs for running evaluations

## Solution Design

### Command Structure
New command group `lse eval` with four subcommands:

#### 1. Extract Traces Command
```bash
lse eval extract-traces --date YYYY-MM-DD --project PROJECT --output traces.json
```

**Purpose**: Extract trace IDs from local storage that contain both AI outputs and human feedback

**Parameters**:
- `--date`: Single date in YYYY-MM-DD format (UTC) (required)
- `--project`: Project name to extract traces from (required)
- `--output`: Output JSON file path for trace IDs (defaults to traces.json)

**Logic**:
1. Load traces from `data/{project}/{date}/` directory
2. Filter traces that have:
   - AI recommendation/output fields
   - Human feedback/verdict in Feedback objects
3. Extract trace IDs and metadata
4. Save to JSON file

**Output Format**:
```json
{
  "date": "2025-09-01",
  "project": "my-project",
  "trace_count": 150,
  "trace_ids": ["trace-id-1", "trace-id-2", ...]
}
```

#### 2. Create Dataset Command
```bash
lse eval create-dataset --traces traces.json --output dataset.json
```

**Purpose**: Transform extracted traces into LangSmith dataset format

**Parameters**:
- `--traces`: Input JSON file from extract-traces command
- `--output`: Output dataset JSON file

**Logic**:
1. Load trace IDs from input file
2. For each trace ID:
   - Load full trace data from local storage
   - Extract inputs (query, context, etc.)
   - Extract AI outputs (recommendations, responses)
   - Extract human feedback as reference (final verdict)
   - Format as LangSmith example
3. Create dataset structure with examples
4. Save to JSON file

**Dataset Format**:
```json
{
  "name": "ai_vs_human_eval",
  "description": "AI recommendations compared to human verdicts",
  "examples": [
    {
      "inputs": {
        "query": "...",
        "context": "...",
        "crypto_symbol": "BTC"
      },
      "outputs": {
        "ai_recommendation": "...",
        "confidence": 0.85
      },
      "reference": {
        "human_verdict": "...",
        "feedback_score": 1.0
      },
      "metadata": {
        "trace_id": "...",
        "date": "2025-09-01",
        "project": "my-project"
      }
    }
  ]
}
```

#### 3. Upload Dataset Command
```bash
lse eval upload --dataset dataset.json --name "dataset_name" [--description "..."]
```

**Purpose**: Upload dataset to LangSmith via SDK

**Parameters**:
- `--dataset`: Input dataset JSON file
- `--name`: Dataset name in LangSmith
- `--description`: Optional dataset description

**Logic**:
1. Load dataset from JSON file
2. Initialize LangSmith client
3. Create dataset via SDK:
   ```python
   from langsmith import Client
   client = Client()
   dataset = client.create_dataset(
       dataset_name=name,
       description=description
   )
   ```
4. Upload examples to dataset
5. Return dataset ID

**Output**:
```
Dataset uploaded successfully!
Dataset ID: ds-abc123
Dataset Name: dataset_name
Examples: 150
```

#### 4. Run Evaluation Command
```bash
lse eval run --dataset-name "dataset_name" --experiment-prefix "exp_20250909" --eval-type "accuracy"
```

**Purpose**: Initiate evaluation via external evaluation API

**Parameters**:
- `--dataset-name`: Name of dataset in LangSmith (required)
- `--experiment-prefix`: Experiment prefix for naming (required)
- `--eval-type`: Type of evaluation to run (required)

**Logic**:
1. Load external API endpoint from `EVAL_API_ENDPOINT` environment variable
2. Build payload with dataset_name, experiment_prefix, and eval_type
3. Generate signature-based authentication from payload contents
4. Make POST request to external API endpoint
5. Handle response and return status

**External API Integration**:
- **Endpoint**: Configured via `EVAL_API_ENDPOINT` (e.g., `https://example.com/api/run_eval`)
- **Authentication**: Signature-based authentication generated from payload
- **Payload**: JSON with dataset_name, experiment_prefix, and eval_type
- **Response**: External API initiates evaluation and uploads results to LangSmith

**Output**:
```
Evaluation request sent to external API!
Endpoint: https://example.com/api/run_eval
Dataset: dataset_name
Experiment Prefix: exp_20250909
Eval Type: accuracy
Status: Initiated
```

**Note**: Report functionality is no longer needed as the external API handles evaluation execution and uploads results directly to LangSmith.

## Implementation Plan

### Phase 1: Core Infrastructure
1. Create `lse/evaluation.py` module with core logic
2. Add `lse/commands/eval.py` for CLI commands
3. Implement trace extraction logic
4. Add dataset builder functionality

### Phase 2: LangSmith & External API Integration
1. Add langsmith dependency to pyproject.toml
2. Implement LangSmith upload functionality
3. Create external API client with signature authentication
4. Build external API communication logic

### Phase 3: Testing & Polish
1. Add comprehensive error handling
2. Write unit tests for all components
3. Add integration tests with mocked APIs
4. Update documentation and help text

## File Structure
```
lse/
├── evaluation.py          # Core evaluation logic
│   ├── TraceExtractor    # Extract suitable traces
│   ├── DatasetBuilder    # Build LangSmith datasets
│   ├── LangSmithUploader # Upload to LangSmith
│   └── EvaluationAPIClient # External API communication
├── commands/
│   └── eval.py           # CLI commands for eval
│       ├── extract_traces()
│       ├── create_dataset()
│       ├── upload()
│       └── run()         # External API integration
└── cli.py               # Register eval command group
```

## Dependencies
- langsmith SDK (add to pyproject.toml)
- Existing trace storage structure
- LangSmith API key configuration

## Testing Strategy
1. Unit tests for each component
2. Mock LangSmith API calls
3. Test with sample trace data
4. Integration test with real LangSmith (optional)

## Success Criteria
- All 4 commands implemented and working
- Comprehensive test coverage (>90%)
- Clear documentation and help text
- Successful dataset creation and upload to LangSmith
- Successful external API integration with signature authentication
- Proper format-specific dataset generation for eval_type

## Error Handling
- Missing trace data gracefully handled
- Network errors with retry logic
- Invalid dataset format validation
- Clear error messages for users

## External API Integration Details

### Authentication
- **Method**: Signature-based authentication
- **Implementation**: Generate signature from payload contents
- **Headers**: Include signature in request headers
- **Security**: Payload integrity verification

### Dataset Format Requirements
- **Format Dependency**: Dataset format must be acceptable to specified eval_type
- **Dynamic Formatting**: Different eval_type values may require different dataset structures
- **Implementation Guidance**: Format specifications to be provided during implementation

### Error Handling
- **Network Errors**: Retry logic for API communication
- **Authentication Failures**: Clear error messages for signature issues
- **Invalid Parameters**: Validation for dataset_name, experiment_prefix, and eval_type
- **External API Errors**: Parse and display API error responses

## Future Enhancements
- Support for additional eval_type values
- Batch processing for large datasets
- Incremental dataset updates
- Automated scheduled evaluations
- Integration with LangSmith evaluation results viewing