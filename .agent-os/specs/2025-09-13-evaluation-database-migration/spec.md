# Phase 10: Evaluation Dataset Database Migration Specification ✅ COMPLETED

## Overview
Migrate evaluation dataset creation from file-based storage to database queries, enabling date range support and eliminating the separate extract-traces step. This phase transforms evaluation commands to query Postgres directly while maintaining dataset format compatibility.

**Status**: COMPLETED ✅ - Successfully implemented database-based evaluation with full feedback_stats preservation and Decimal serialization fixes.

## Problem Statement
Current evaluation workflow limitations:
1. **File Dependency**: Requires local JSON files for all operations
2. **Single Date Limitation**: Cannot create datasets spanning multiple days
3. **Multi-Step Process**: Manual extract-traces step adds complexity
4. **Performance Issues**: File scanning becomes slow with large datasets
5. **Storage Requirements**: Must have all data available locally

Target improvements:
1. **Database Queries**: Direct database access for trace extraction
2. **Date Range Support**: Create datasets spanning multiple days
3. **Simplified Workflow**: Direct dataset creation without extraction step
4. **Better Performance**: Database queries faster than file scanning
5. **Reduced Dependencies**: No requirement for local file storage

## Current vs Target Architecture

### Current Workflow
```bash
# Step 1: Extract suitable traces from files
lse eval extract-traces --date 2025-09-13 --project my-project --output traces.json

# Step 2: Create dataset from extracted trace IDs
lse eval create-dataset --traces traces.json --eval-type accuracy --output dataset.json

# Step 3: Upload dataset to LangSmith
lse eval upload --dataset dataset.json --name eval_dataset_2025_09

# Step 4: Run evaluation via external API
lse eval run --dataset-name eval_dataset_2025_09 --experiment-prefix exp_20250913 --eval-type accuracy
```

### Target Workflow  
```bash
# Single date - direct dataset creation
lse eval create-dataset --date 2025-09-13 --project my-project --eval-type accuracy --output dataset.json

# Date range - span multiple days
lse eval create-dataset --start-date 2025-09-01 --end-date 2025-09-13 --project my-project --eval-type accuracy

# Upload and run (unchanged)
lse eval upload --dataset dataset.json --name eval_dataset_2025_09
lse eval run --dataset-name eval_dataset_2025_09 --experiment-prefix exp_20250913 --eval-type accuracy
```

## Solution Design

### Database Integration Architecture

#### Enhanced TraceExtractor
```python
class TraceExtractor:
    """Extract suitable traces for evaluation from database by aggregating runs."""
    
    def __init__(self, database_manager: DatabaseManager):
        self.db = database_manager
    
    async def extract_traces_from_db(
        self, 
        project: str, 
        start_date: str, 
        end_date: Optional[str] = None
    ) -> List[TraceMetadata]:
        """Extract traces from database that meet evaluation criteria.
        
        This method queries runs and aggregates them by trace_id to reconstruct traces.
        
        Args:
            project: Project name to extract traces from
            start_date: Start date in YYYY-MM-DD format (UTC)
            end_date: End date in YYYY-MM-DD format (UTC), defaults to start_date
            
        Returns:
            List of trace metadata meeting evaluation criteria
        """
        end_date = end_date or start_date
        
        async with self.db.get_session() as session:
            # Query all runs for the date range, grouped by trace_id
            result = await session.execute(
                """
                SELECT 
                    trace_id, 
                    project, 
                    run_date,
                    array_agg(data ORDER BY run_id) as run_data_array,
                    COUNT(*) as run_count
                FROM runs 
                WHERE project = :project 
                  AND run_date BETWEEN :start_date AND :end_date
                GROUP BY trace_id, project, run_date
                """,
                {
                    "project": project,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            traces = []
            for row in result.fetchall():
                # Aggregate run data to evaluate trace-level criteria
                trace_evaluation = self._evaluate_trace_from_runs(row.run_data_array)
                
                if trace_evaluation["meets_criteria"]:
                    trace_metadata = TraceMetadata(
                        trace_id=row.trace_id,
                        project=row.project,
                        date=row.run_date.strftime("%Y-%m-%d"),
                        has_ai_output=trace_evaluation["has_ai_output"],
                        has_human_feedback=trace_evaluation["has_human_feedback"]
                    )
                    traces.append(trace_metadata)
            
            return traces
    
    def _evaluate_trace_from_runs(self, run_data_array: List[dict]) -> dict:
        """Evaluate a trace based on aggregated run data.
        
        Args:
            run_data_array: List of run data JSONB objects belonging to same trace
            
        Returns:
            Dict with evaluation results for the trace
        """
        has_ai_output = False
        has_human_feedback = False
        meets_criteria = False
        
        # Aggregate evaluation criteria across all runs in the trace
        for run_data in run_data_array:
            if self._has_ai_output(run_data):
                has_ai_output = True
            
            if self._has_human_feedback(run_data):
                has_human_feedback = True
            
            # Check if any run in this trace meets filtering criteria
            if self._meets_evaluation_criteria(run_data):
                meets_criteria = True
        
        return {
            "has_ai_output": has_ai_output,
            "has_human_feedback": has_human_feedback,
            "meets_criteria": meets_criteria
        }
```

#### Database Query Optimization
```sql
-- Optimized query for evaluation trace extraction with run aggregation
SELECT 
    trace_id, 
    project, 
    run_date,
    array_agg(data ORDER BY run_id) as run_data_array,
    COUNT(*) as run_count
FROM runs 
WHERE project = $1 
  AND run_date BETWEEN $2 AND $3
  -- Pre-filter runs that might contribute to evaluation criteria
  AND (
      data->'trace' ? 'outputs' OR  -- Has AI outputs
      data->'trace' ? 'feedback_stats' OR -- Has feedback stats
      data ? 'feedback' -- Has feedback
  )
GROUP BY trace_id, project, run_date
HAVING COUNT(*) >= 1
ORDER BY run_date, trace_id;

-- Index to support evaluation queries on runs table
CREATE INDEX idx_runs_eval_criteria 
ON runs(project, run_date, trace_id) 
WHERE (
    data->'trace' ? 'outputs' OR 
    data->'trace' ? 'feedback_stats' OR 
    data ? 'feedback'
);

-- Additional indexes for trace reconstruction
CREATE INDEX idx_runs_trace_reconstruction 
ON runs(trace_id, run_date, run_id)
WHERE project IS NOT NULL;
```

### Updated Command Interfaces

#### Enhanced create-dataset Command
```python
@app.command()
def create_dataset(
    project: str = typer.Option(
        ..., "--project", help="Project name to create dataset from"
    ),
    eval_type: str = typer.Option(
        ..., "--eval-type", help="Evaluation type (accuracy, relevance, etc.)"
    ),
    date: Optional[str] = typer.Option(
        None, "--date", help="Single date in YYYY-MM-DD format (UTC)"
    ),
    start_date: Optional[str] = typer.Option(
        None, "--start-date", help="Start date for range in YYYY-MM-DD format (UTC)"
    ),
    end_date: Optional[str] = typer.Option(
        None, "--end-date", help="End date for range in YYYY-MM-DD format (UTC)"
    ),
    output: str = typer.Option(
        "/tmp/dataset.json", "--output", help="Output dataset JSON file path"
    ),
    name: Optional[str] = typer.Option(
        None, "--name", help="Dataset name (auto-generated if not provided)"
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", help="Maximum number of traces to include"
    ),
):
    """Create evaluation dataset directly from database traces."""
    
    # Validate date parameters
    if date and (start_date or end_date):
        console.print("[red]Cannot specify both --date and date range options[/red]")
        raise typer.Exit(1)
    
    if not date and not start_date:
        console.print("[red]Must specify either --date or --start-date[/red]")
        raise typer.Exit(1)
    
    # Set date range
    if date:
        start_date = end_date = date
    elif start_date and not end_date:
        end_date = start_date
    
    # Create dataset from database
    asyncio.run(create_dataset_from_db(
        project=project,
        start_date=start_date,
        end_date=end_date,
        eval_type=eval_type,
        output=output,
        name=name,
        limit=limit
    ))
```

#### Removed extract-traces Command
The separate `extract-traces` command will be removed as trace extraction becomes integrated into `create-dataset`.

### Enhanced DatasetBuilder

#### Database-Aware Dataset Creation
```python
class DatasetBuilder:
    """Build evaluation datasets from database traces."""
    
    def __init__(self, database_manager: DatabaseManager):
        self.db = database_manager
        self.extractor = TraceExtractor(database_manager)
    
    async def create_dataset_from_db(
        self,
        project: str,
        start_date: str,
        end_date: str,
        eval_type: str,
        limit: Optional[int] = None
    ) -> EvaluationDataset:
        """Create evaluation dataset directly from database.
        
        Args:
            project: Project name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD) 
            eval_type: Evaluation type for formatting
            limit: Maximum number of traces to include
            
        Returns:
            Complete evaluation dataset ready for upload
        """
        # Extract suitable traces from database
        trace_metadata = await self.extractor.extract_traces_from_db(
            project=project,
            start_date=start_date,
            end_date=end_date
        )
        
        if limit:
            trace_metadata = trace_metadata[:limit]
        
        # Build dataset examples
        examples = []
        async with self.db.get_session() as session:
            for metadata in trace_metadata:
                # Get full trace data from database
                result = await session.execute(
                    """
                    SELECT data FROM traces 
                    WHERE trace_id = :trace_id 
                      AND project = :project 
                      AND trace_date = :date
                    """,
                    {
                        "trace_id": metadata.trace_id,
                        "project": metadata.project,
                        "date": metadata.date
                    }
                )
                
                row = result.fetchone()
                if row:
                    example = self._build_dataset_example(
                        trace_data=row.data,
                        eval_type=eval_type,
                        metadata=metadata
                    )
                    examples.append(example)
        
        # Create dataset
        dataset_name = f"{project}_{eval_type}_{start_date}_{end_date}"
        return EvaluationDataset(
            name=dataset_name,
            description=f"Evaluation dataset for {project} from {start_date} to {end_date}",
            examples=examples
        )
```

### Query Optimization Strategies

#### JSONB Query Patterns
```sql
-- Check for AI output in nested structure
SELECT trace_id FROM traces 
WHERE data->'outputs' IS NOT NULL
  AND data->'outputs' != 'null'::jsonb;

-- Find traces with specific feedback types
SELECT trace_id FROM traces
WHERE data->'feedback' @> '[{"key": "human_verdict"}]'::jsonb;

-- Extract specific fields for evaluation
SELECT 
    trace_id,
    data->'inputs'->>'query' as query,
    data->'outputs'->>'recommendation' as ai_output,
    data->'feedback'->0->>'value' as human_verdict
FROM traces 
WHERE project = 'my-project' 
  AND trace_date BETWEEN '2025-09-01' AND '2025-09-13';
```

#### Performance Indexes
```sql
-- Composite index for common evaluation queries
CREATE INDEX idx_traces_eval_composite 
ON traces(project, trace_date, (data->'outputs' IS NOT NULL))
WHERE data ? 'feedback';

-- GIN index for complex JSONB queries
CREATE INDEX idx_traces_data_feedback 
ON traces USING gin((data->'feedback'));

-- Specific path indexes for common extractions
CREATE INDEX idx_traces_data_verdict 
ON traces USING gin((data->'feedback'->0->>'value'));
```

## Implementation Plan

### Phase 1: Database Integration (Week 1)
- [ ] Add DatabaseManager dependency to evaluation module
- [ ] Create async methods in TraceExtractor for database queries
- [ ] Implement JSONB query patterns for evaluation criteria
- [ ] Add database connection handling to evaluation commands
- [ ] Create database schema indexes for evaluation queries

### Phase 2: Enhanced create-dataset Command (Week 1)
- [ ] Update create-dataset command to accept date range parameters
- [ ] Add database query integration to DatasetBuilder
- [ ] Implement streaming dataset creation for large date ranges
- [ ] Add parameter validation and error handling
- [ ] Create comprehensive progress reporting

### Phase 3: Remove extract-traces Command (Week 2)
- [ ] Remove extract-traces command from CLI
- [ ] Update help text and documentation
- [ ] Migrate tests to use new create-dataset interface
- [ ] Update error messages and suggestions
- [ ] Clean up unused TraceExtractor methods

### Phase 4: Performance Optimization (Week 2)
- [ ] Add database indexes for evaluation queries
- [ ] Optimize JSONB query patterns
- [ ] Implement query result caching where appropriate
- [ ] Add query performance monitoring
- [ ] Tune batch processing for large datasets

### Phase 5: Testing and Validation (Week 3)
- [ ] Write comprehensive database query tests
- [ ] Create date range functionality tests
- [ ] Add performance regression tests
- [ ] Validate dataset format compatibility
- [ ] Test with real-world data sets

## Testing Strategy

### Unit Tests
```python
# tests/test_evaluation_database.py
@pytest.mark.asyncio
async def test_extract_traces_from_db():
    db_manager = get_test_database_manager()
    extractor = TraceExtractor(db_manager)
    
    # Insert test traces
    await insert_test_traces_with_evaluation_data()
    
    # Extract traces
    traces = await extractor.extract_traces_from_db(
        project="test-project",
        start_date="2025-09-13",
        end_date="2025-09-13"
    )
    
    # Validate results
    assert len(traces) > 0
    assert all(t.has_ai_output for t in traces)
    assert all(t.has_human_feedback for t in traces)

@pytest.mark.asyncio
async def test_create_dataset_from_db():
    builder = DatasetBuilder(get_test_database_manager())
    
    dataset = await builder.create_dataset_from_db(
        project="test-project",
        start_date="2025-09-13",
        end_date="2025-09-13",
        eval_type="accuracy"
    )
    
    assert dataset.name.startswith("test-project_accuracy")
    assert len(dataset.examples) > 0
    assert all(ex.inputs is not None for ex in dataset.examples)
```

### Integration Tests
```python
# tests/test_eval_command_database.py
@pytest.mark.asyncio
async def test_create_dataset_command_date_range():
    # Setup test database with traces across multiple dates
    await populate_test_database_with_date_range()
    
    # Execute command
    runner = CliRunner()
    result = runner.invoke(
        create_dataset,
        [
            "--project", "test-project",
            "--start-date", "2025-09-01",
            "--end-date", "2025-09-13",
            "--eval-type", "accuracy",
            "--output", "/tmp/test_dataset.json"
        ]
    )
    
    # Validate results
    assert result.exit_code == 0
    assert Path("/tmp/test_dataset.json").exists()
    
    # Validate dataset content
    with open("/tmp/test_dataset.json") as f:
        dataset = json.load(f)
    
    assert len(dataset["examples"]) > 0
    assert dataset["name"].endswith("2025-09-01_2025-09-13")
```

### Performance Tests
```python
# tests/test_evaluation_performance.py
@pytest.mark.asyncio
async def test_large_date_range_performance():
    # Setup database with 30 days of data
    await populate_database_with_large_dataset(days=30, traces_per_day=100)
    
    builder = DatasetBuilder(get_test_database_manager())
    
    start_time = time.time()
    dataset = await builder.create_dataset_from_db(
        project="large-project",
        start_date="2025-09-01",
        end_date="2025-09-30",
        eval_type="accuracy"
    )
    duration = time.time() - start_time
    
    # Performance assertions
    assert duration < 60.0  # Should complete within 60 seconds
    assert len(dataset.examples) > 0
    assert len(dataset.examples) <= 3000  # 30 days * 100 traces
```

## Migration Strategy

### Backward Compatibility
- **Command Interface**: New parameters added, existing ones preserved
- **Dataset Format**: Identical output format to maintain LangSmith compatibility
- **API Integration**: No changes to upload and run commands
- **Error Handling**: Consistent error messages and exit codes

### Deployment Approach
1. **Feature Flag**: Add database-vs-file mode selection
2. **Parallel Testing**: Run both implementations for validation
3. **Gradual Rollout**: Enable database mode for specific projects
4. **Full Migration**: Remove file-based implementation after validation
5. **Cleanup**: Remove deprecated extract-traces command

### Rollback Plan
- **File Fallback**: Ability to revert to file-based implementation
- **Command Preservation**: Keep old command interface available
- **Data Recovery**: Ensure database contains all necessary data
- **Performance Monitoring**: Track query performance vs file scanning

## Performance Considerations

### Query Optimization
- **Index Strategy**: Composite indexes for common query patterns
- **Query Planning**: Use EXPLAIN ANALYZE for query optimization
- **Connection Pooling**: Reuse database connections efficiently
- **Batch Processing**: Process traces in batches to manage memory

### Memory Management
- **Streaming**: Process large datasets without loading all in memory
- **Garbage Collection**: Explicit cleanup of large objects
- **Connection Limits**: Respect database connection pool limits
- **Progress Reporting**: Provide feedback during long operations

### Scalability
- **Date Range Limits**: Reasonable limits on date range size
- **Result Pagination**: Handle very large result sets efficiently
- **Concurrent Access**: Support multiple users accessing database
- **Resource Monitoring**: Track CPU and memory usage during operations

## Data Model Considerations

### JSONB Structure Queries
```python
# Common evaluation filtering patterns
EVALUATION_CRITERIA_QUERIES = {
    "has_ai_output": "data->'outputs' IS NOT NULL",
    "has_feedback": "data ? 'feedback'",
    "has_human_verdict": "data->'feedback'->0 ? 'value'",
    "verdict_matches_output": """
        (data->'outputs'->>'final_decision' = 'PASS' AND data->'feedback'->0->>'value' = 'PASS')
        OR 
        (data->'outputs'->>'final_decision' = 'FAIL' AND data->'feedback'->0->>'value' = 'FAIL')
    """
}
```

### Data Extraction Patterns
```python
def extract_evaluation_fields(trace_data: dict) -> dict:
    """Extract fields needed for evaluation from trace data."""
    return {
        "query": get_nested_value(trace_data, ["inputs", "query"]),
        "context": get_nested_value(trace_data, ["inputs", "context"]),
        "ai_recommendation": get_nested_value(trace_data, ["outputs", "recommendation"]),
        "ai_confidence": get_nested_value(trace_data, ["outputs", "confidence"]),
        "human_verdict": get_nested_value(trace_data, ["feedback", 0, "value"]),
        "feedback_score": get_nested_value(trace_data, ["feedback", 0, "score"]),
    }
```

## Security Considerations

### Query Security
- **Parameterized Queries**: All database queries use parameters to prevent injection
- **Input Validation**: Validate all date and project parameters
- **Access Control**: Database queries limited to application schema
- **Query Limits**: Reasonable limits on result set sizes

### Data Protection
- **Sensitive Data**: Handle trace data containing sensitive information securely
- **Logging**: Avoid logging sensitive trace content
- **Error Messages**: Don't expose internal data in error messages
- **Audit Trail**: Log evaluation dataset creation operations

## Success Criteria

### Functional Requirements
- [ ] create-dataset command works with single dates and date ranges
- [ ] Database queries return identical results to file-based approach
- [ ] Dataset format maintains compatibility with existing upload/run commands
- [ ] extract-traces command successfully removed without breaking functionality
- [ ] All evaluation workflows complete successfully

### Performance Requirements
- [ ] Date range queries complete within 2 minutes for 30-day ranges
- [ ] Single date datasets create within 30 seconds
- [ ] Memory usage stays within 1GB for typical operations
- [ ] Database queries utilize indexes efficiently
- [ ] Large datasets (1000+ traces) process successfully

### Quality Requirements
- [ ] Test coverage maintains 95%+ for evaluation module
- [ ] All integration tests pass with database backend
- [ ] Performance regression tests validate acceptable execution times
- [ ] Documentation updated for new command interfaces
- [ ] Real-world datasets process without errors

## Dependencies

### External Dependencies
- **Phase 9 Completion**: Database must be populated with trace data
- **Postgres Database**: Running instance with proper indexes
- **Database Connectivity**: Reliable connection to database
- **Sufficient Data**: Historical traces available in database

### Internal Dependencies
- **LangSmith Integration**: Upload and run commands must continue working
- **Configuration System**: Database connection settings properly configured
- **Error Handling**: Consistent error handling across all commands
- **CLI Framework**: Integration with existing Typer-based CLI

## Risks and Mitigation

### Technical Risks
- **Query Performance**: Complex JSONB queries may be slower than expected
  - *Mitigation*: Comprehensive indexing and query optimization
- **Data Inconsistency**: Database data may not match file-based results
  - *Mitigation*: Extensive validation and comparison testing
- **Memory Usage**: Large date ranges may consume excessive memory
  - *Mitigation*: Streaming processing and memory monitoring

### Operational Risks
- **Migration Complexity**: Changing evaluation workflow may confuse users
  - *Mitigation*: Clear documentation and gradual rollout
- **Data Dependencies**: Evaluation depends on database population
  - *Mitigation*: Verification tools and clear dependency documentation
- **Backward Compatibility**: Existing workflows may break
  - *Mitigation*: Maintain dataset format and API compatibility

## Future Enhancements

### Advanced Features
- **Caching**: Cache evaluation queries for frequently accessed data
- **Filtering**: Advanced filtering options for trace selection
- **Sampling**: Statistical sampling for very large datasets
- **Streaming**: Real-time dataset creation for continuous evaluation

### Integration Opportunities
- **Monitoring**: Integration with monitoring systems for evaluation metrics
- **Scheduling**: Automated dataset creation and evaluation workflows
- **APIs**: REST API for external evaluation dataset requests
- **Visualization**: Dashboard for evaluation dataset statistics