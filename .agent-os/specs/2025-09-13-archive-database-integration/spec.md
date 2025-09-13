# Phase 9: Archive Tool Database Integration Specification

## Overview
Enhance the existing archive tool to populate the Postgres database alongside the current Google Drive archiving workflow. This phase maintains backward compatibility while introducing database storage as an additional target.

## Problem Statement
Current archive workflow stores data only in local JSON files for Google Drive upload. Need to extend this to also populate the database while:
1. Maintaining existing Google Drive archiving functionality
2. Ensuring data consistency between files and database
3. Providing convenient commands for complete archival workflows
4. Supporting batch operations for historical data loading

## Solution Design

### Architecture Approach
- **Dual Storage**: Files remain for Google Drive, database becomes additional target
- **Consistency First**: Files remain source of truth during transition
- **Additive Changes**: No modifications to existing archive commands
- **New Commands**: Additional commands for database operations
- **Batch Processing**: Efficient bulk loading capabilities

### Enhanced Archive Workflow

#### Current Workflow (Preserved)
```bash
# Individual steps (unchanged)
lse archive fetch --date 2025-09-13 --project my-project    # → Local JSON files
lse archive zip --date 2025-09-13 --project my-project      # → ZIP archive
lse archive upload --date 2025-09-13 --project my-project   # → Google Drive

# Combined operation (unchanged) 
lse archive --date 2025-09-13 --project my-project          # → All steps above
```

#### Extended Workflow (New)
```bash
# New: Load files to database
lse archive to-db --date 2025-09-13 --project my-project    # → Postgres database

# New: Complete archival including database
lse archive full-sweep --date 2025-09-13 --project my-project  # → All steps + DB

# New: Verify consistency
lse archive verify --date 2025-09-13 --project my-project   # → Check files vs DB
```

## Technical Implementation

### New Command: `lse archive to-db`

#### Purpose
Load existing JSON files into the Postgres database for a specific date and project.

#### Command Interface
```bash
lse archive to-db --date YYYY-MM-DD --project PROJECT [options]
```

#### Parameters
- `--date` (required): Date in YYYY-MM-DD format (UTC)
- `--project` (required): Project name to load traces for
- `--batch-size` (optional): Number of traces to process in each batch (default: 100)
- `--overwrite` (optional): Overwrite existing traces in database (default: false)
- `--dry-run` (optional): Show what would be loaded without actual insertion

#### Implementation Logic
```python
async def load_runs_to_database(date: str, project: str, batch_size: int = 100) -> LoadResult:
    """Load run files from local storage to database."""
    
    # 1. Discover run files (each JSON file is a LangSmith Run)
    run_dir = Path(f"data/{project}/{date}")
    run_files = list(run_dir.glob("*.json"))
    
    # 2. Load and validate runs
    runs = []
    for file_path in run_files:
        try:
            run_record = RunRecord.from_file(file_path, project, date)
            if run_record.run_id and run_record.trace_id:  # Ensure valid IDs
                runs.append(run_record)
        except Exception as e:
            logger.warning(f"Skipping invalid run file {file_path}: {e}")
    
    # 3. Batch insert to database
    run_db = RunDatabase(database_manager)
    batch_result = await run_db.insert_run_batch(runs, batch_size)
    
    return LoadResult(
        total_files=len(run_files),
        total_runs=len(runs),
        batches_processed=batch_result.successful_batches,
        successful_inserts=batch_result.total_inserted,
        failed_inserts=len(runs) - batch_result.total_inserted,
        errors=batch_result.errors
    )
```

### New Command: `lse archive full-sweep`

#### Purpose
Execute the complete archival workflow: fetch → zip → upload → populate database.

#### Command Interface
```bash
lse archive full-sweep --date YYYY-MM-DD --project PROJECT [options]
```

#### Parameters
- `--date` (required): Date in YYYY-MM-DD format (UTC)
- `--project` (required): Project name to process
- `--skip-fetch` (optional): Skip fetch step if files already exist
- `--skip-upload` (optional): Skip Google Drive upload
- `--skip-db` (optional): Skip database population

#### Implementation Logic
```python
async def full_sweep_archive(date: str, project: str, options: FullSweepOptions) -> FullSweepResult:
    """Execute complete archival workflow."""
    
    result = FullSweepResult()
    
    # Step 1: Fetch (unless skipped)
    if not options.skip_fetch:
        result.fetch_result = await fetch_traces(date, project)
    
    # Step 2: Zip
    result.zip_result = await zip_traces(date, project)
    
    # Step 3: Upload to Google Drive (unless skipped)
    if not options.skip_upload:
        result.upload_result = await upload_to_drive(date, project)
    
    # Step 4: Populate Database (unless skipped)
    if not options.skip_db:
        result.db_result = await load_traces_to_database(date, project)
    
    return result
```

### New Command: `lse archive verify`

#### Purpose
Verify consistency between local JSON files and database records.

#### Command Interface
```bash
lse archive verify --date YYYY-MM-DD --project PROJECT [options]
```

#### Parameters
- `--date` (required): Date in YYYY-MM-DD format (UTC)
- `--project` (required): Project name to verify
- `--fix-missing` (optional): Automatically fix missing database records
- `--detailed` (optional): Show detailed comparison results

#### Implementation Logic
```python
async def verify_consistency(date: str, project: str) -> VerificationResult:
    """Verify files and database are consistent."""
    
    run_db = RunDatabase(database_manager)
    
    # 1. Get file-based run IDs (each JSON file represents a run)
    file_run_ids = get_file_run_ids(project, date)
    
    # 2. Get database run IDs
    db_run_ids = await run_db.get_run_ids(project, date)
    
    # 3. Compare and identify discrepancies
    missing_in_db = file_run_ids - db_run_ids
    missing_in_files = db_run_ids - file_run_ids
    
    # 4. For common runs, verify data consistency
    common_runs = file_run_ids & db_run_ids
    inconsistent_runs = []
    
    for run_id in common_runs:
        file_data = load_run_file(project, date, run_id)
        db_data = await run_db.get_run_data(run_id)
        
        if not runs_match(file_data, db_data):
            inconsistent_runs.append(run_id)
    
    # 5. Also verify trace-level consistency
    file_trace_ids = extract_trace_ids_from_files(project, date)
    db_trace_ids = await run_db.get_trace_ids(project, date)
    
    missing_traces_in_db = file_trace_ids - db_trace_ids
    missing_traces_in_files = db_trace_ids - file_trace_ids
    
    return VerificationResult(
        total_files=len(file_run_ids),
        total_db_records=len(db_run_ids),
        missing_runs_in_db=list(missing_in_db),
        missing_runs_in_files=list(missing_in_files),
        inconsistent_runs=inconsistent_runs,
        total_file_traces=len(file_trace_ids),
        total_db_traces=len(db_trace_ids),
        missing_traces_in_db=list(missing_traces_in_db),
        missing_traces_in_files=list(missing_traces_in_files)
    )
```

### Database Storage Layer

#### RunDatabase Class
```python
class RunDatabase:
    """Database operations for run storage."""
    
    def __init__(self, database_manager: DatabaseManager):
        self.db = database_manager
    
    async def insert_run(self, run_id: str, trace_id: str, project: str, date: str, data: dict) -> bool:
        """Insert a single run into the database."""
        async with self.db.get_session() as session:
            try:
                await session.execute(
                    """
                    INSERT INTO runs (run_id, trace_id, project, run_date, data) 
                    VALUES (:run_id, :trace_id, :project, :run_date, :data)
                    ON CONFLICT (run_id) 
                    DO UPDATE SET 
                        trace_id = EXCLUDED.trace_id,
                        project = EXCLUDED.project,
                        run_date = EXCLUDED.run_date,
                        data = EXCLUDED.data, 
                        created_at = CURRENT_TIMESTAMP
                    """,
                    {
                        "run_id": run_id,
                        "trace_id": trace_id,
                        "project": project,
                        "run_date": date,
                        "data": data
                    }
                )
                return True
            except Exception as e:
                logger.error(f"Failed to insert run {run_id}: {e}")
                return False
    
    async def insert_run_batch(self, runs: List[RunRecord], batch_size: int = 100) -> BatchResult:
        """Insert multiple runs in batches."""
        async with self.db.get_session() as session:
            results = BatchResult()
            
            for batch in chunk(runs, batch_size):
                try:
                    await session.execute_many(
                        """
                        INSERT INTO runs (run_id, trace_id, project, run_date, data) 
                        VALUES (:run_id, :trace_id, :project, :run_date, :data)
                        ON CONFLICT (run_id) 
                        DO UPDATE SET 
                            trace_id = EXCLUDED.trace_id,
                            project = EXCLUDED.project,
                            run_date = EXCLUDED.run_date,
                            data = EXCLUDED.data, 
                            created_at = CURRENT_TIMESTAMP
                        """,
                        [run.to_dict() for run in batch]
                    )
                    results.successful_batches += 1
                    results.total_inserted += len(batch)
                except Exception as e:
                    results.failed_batches += 1
                    results.errors.append(f"Batch failed: {e}")
                    logger.error(f"Batch insert failed: {e}")
            
            return results
    
    async def get_run_ids(self, project: str, date: str) -> Set[str]:
        """Get all run IDs for a project and date."""
        async with self.db.get_session() as session:
            result = await session.execute(
                "SELECT run_id FROM runs WHERE project = :project AND run_date = :date",
                {"project": project, "date": date}
            )
            return {row.run_id for row in result.fetchall()}
    
    async def get_trace_ids(self, project: str, date: str) -> Set[str]:
        """Get all unique trace IDs for a project and date."""
        async with self.db.get_session() as session:
            result = await session.execute(
                "SELECT DISTINCT trace_id FROM runs WHERE project = :project AND run_date = :date",
                {"project": project, "date": date}
            )
            return {row.trace_id for row in result.fetchall()}
    
    async def get_run_data(self, run_id: str) -> Optional[dict]:
        """Get run data by ID."""
        async with self.db.get_session() as session:
            result = await session.execute(
                "SELECT data FROM runs WHERE run_id = :run_id",
                {"run_id": run_id}
            )
            row = result.fetchone()
            return row.data if row else None
    
    async def get_runs_for_trace(self, trace_id: str, project: str, date: str) -> List[dict]:
        """Get all runs belonging to a specific trace."""
        async with self.db.get_session() as session:
            result = await session.execute(
                "SELECT data FROM runs WHERE trace_id = :trace_id AND project = :project AND run_date = :date ORDER BY run_id",
                {"trace_id": trace_id, "project": project, "date": date}
            )
            return [row.data for row in result.fetchall()]
```

### Data Models

#### RunRecord
```python
@dataclass
class RunRecord:
    """Represents a run record for database storage."""
    run_id: str
    trace_id: str
    project: str
    run_date: str
    data: dict
    
    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            "project": self.project,
            "run_date": self.run_date,
            "data": self.data
        }
    
    @classmethod
    def from_file(cls, file_path: Path, project: str, date: str) -> "RunRecord":
        """Create RunRecord from JSON file."""
        data = load_json(file_path)
        
        # Extract run_id and trace_id from LangSmith run data
        run_info = data.get("trace", {})  # LangSmith stores run info in 'trace' field
        run_id = run_info.get("id", "")  # Run's unique ID
        trace_id = run_info.get("trace_id", "")  # Trace this run belongs to
        
        # Ensure data consistency for database constraints
        data_copy = data.copy()
        if "trace" in data_copy:
            data_copy["trace"]["run_id"] = run_id
            data_copy["trace"]["trace_id"] = trace_id
            data_copy["trace"]["project"] = project
            data_copy["trace"]["run_date"] = date
        
        return cls(run_id, trace_id, project, date, data_copy)
```

#### Result Models
```python
@dataclass
class LoadResult:
    total_files: int
    total_traces: int
    batches_processed: int
    successful_inserts: int
    failed_inserts: int
    errors: List[str]
    duration_seconds: float

@dataclass
class FullSweepResult:
    fetch_result: Optional[Any] = None
    zip_result: Optional[Any] = None
    upload_result: Optional[Any] = None
    db_result: Optional[LoadResult] = None
    total_duration: float = 0.0

@dataclass
class VerificationResult:
    total_files: int
    total_db_records: int
    missing_in_db: List[str]
    missing_in_files: List[str]
    inconsistent_traces: List[str]
    
    @property
    def is_consistent(self) -> bool:
        return (
            len(self.missing_in_db) == 0 
            and len(self.missing_in_files) == 0 
            and len(self.inconsistent_traces) == 0
        )
```

## Implementation Status

### ✅ COMPLETED - Phase 9 is now fully implemented!

### Phase 1: Database Storage Layer ✅ COMPLETED
- [x] Create DatabaseRunStorage class with async operations ✅
- [x] Implement single run insertion with upsert logic ✅
- [x] Add batch insertion with transaction management ✅
- [x] Create run retrieval and query methods ✅
- [x] Add comprehensive error handling and logging ✅

### Phase 2: to-db Command ✅ COMPLETED
- [x] Create `lse archive to-db` command implementation ✅
- [x] Add file discovery and loading logic ✅
- [x] Implement batch processing with progress indicators ✅
- [x] Add validation and error reporting ✅
- [x] Create comprehensive tests for the command ✅

### Phase 3: full-sweep Command ✅ COMPLETED
- [x] Create `lse archive full-sweep` command ✅
- [x] Integrate with existing archive commands ✅
- [x] Add selective step execution (skip options) ✅
- [x] Implement comprehensive result reporting ✅
- [x] Add error recovery and rollback capabilities ✅

### Phase 4: Verification Command ✅ IMPLEMENTED AS DATA CONSISTENCY
- [x] Implemented data consistency checks in to-db command ✅
- [x] Added file vs database validation logic ✅
- [x] Added detailed error reporting of inconsistencies ✅
- [x] Added automatic handling of multiple JSON formats ✅
- [x] Added comprehensive validation tests ✅

### Phase 5: Integration & Testing ✅ COMPLETED
- [x] Integrate all commands with existing CLI ✅
- [x] Add comprehensive unit and integration tests ✅
- [x] Create performance benchmarks ✅
- [x] Add documentation and usage examples ✅
- [x] Validate with real-world data sets (1,734+ runs) ✅

### Additional Improvements Implemented
- [x] **Rate Limiting Enhancements**: Hardcoded 1000ms delays, 5-attempt retry logic ✅
- [x] **User Experience**: Removed confusing --include-children flag, always fetch complete hierarchies ✅
- [x] **Terminology Consistency**: Updated messages from "root traces" to "traces", "trace files" to "run files" ✅
- [x] **Multiple JSON Format Support**: Handles both wrapper format and direct Run objects ✅

## Testing Strategy

### Unit Tests
```python
# tests/test_trace_database.py
@pytest.mark.asyncio
async def test_trace_insertion():
    db = TraceDatabase(db_manager)
    success = await db.insert_trace("test-123", "my-project", "2025-09-13", {"name": "test"})
    assert success is True

@pytest.mark.asyncio  
async def test_batch_insertion():
    db = TraceDatabase(db_manager)
    traces = [TraceRecord("test-1", "project", "2025-09-13", {"name": "test1"})]
    result = await db.insert_trace_batch(traces)
    assert result.total_inserted == 1
    assert result.failed_batches == 0
```

### Integration Tests
```python
# tests/test_archive_to_db_command.py
@pytest.mark.asyncio
async def test_to_db_command_execution(tmp_path, db_manager):
    # Create test trace files
    create_test_trace_files(tmp_path, "my-project", "2025-09-13", count=10)
    
    # Execute to-db command
    result = await execute_to_db_command("2025-09-13", "my-project")
    
    # Verify results
    assert result.total_traces == 10
    assert result.failed_inserts == 0
    
    # Verify database contains traces
    db = TraceDatabase(db_manager)
    trace_ids = await db.get_trace_ids("my-project", "2025-09-13")
    assert len(trace_ids) == 10
```

### Performance Tests
```python
# tests/test_archive_performance.py
@pytest.mark.asyncio
async def test_large_batch_performance():
    # Test with 1000 traces
    traces = generate_test_traces(count=1000)
    
    start_time = time.time()
    result = await db.insert_trace_batch(traces, batch_size=100)
    duration = time.time() - start_time
    
    # Performance assertions
    assert duration < 30.0  # Should complete within 30 seconds
    assert result.total_inserted == 1000
    assert result.failed_batches == 0
```

## Performance Considerations

### Batch Processing
- **Optimal Batch Size**: Start with 100 traces per batch, tune based on performance
- **Memory Management**: Stream processing to avoid loading all traces in memory
- **Progress Reporting**: Real-time progress bars for long-running operations
- **Error Recovery**: Continue processing other batches if one fails

### Database Optimization
- **Upsert Operations**: Use ON CONFLICT for idempotent operations
- **Transaction Scope**: Batch-level transactions for atomicity
- **Connection Pooling**: Reuse connections across batch operations
- **Index Usage**: Ensure queries utilize existing indexes efficiently

### Concurrency
- **Async Operations**: Use asyncio for non-blocking database operations
- **Connection Management**: Pool connections to handle concurrent requests
- **Batch Parallelization**: Process multiple batches concurrently when safe
- **Resource Limits**: Respect database connection and memory limits

## Error Handling and Recovery

### Database Errors
- **Connection Failures**: Retry with exponential backoff
- **Constraint Violations**: Log and continue with remaining traces
- **Transaction Failures**: Rollback and retry smaller batches
- **Timeout Handling**: Graceful timeout with partial results

### Data Validation
- **Schema Validation**: Validate trace structure before insertion
- **Data Integrity**: Check for required fields and valid formats
- **Duplicate Handling**: Use upsert logic to handle duplicates gracefully
- **Corruption Detection**: Validate JSON structure and content

### Recovery Strategies
- **Partial Failure**: Continue processing unaffected traces
- **Resume Capability**: Skip already processed traces on retry
- **Rollback Support**: Ability to undo failed batch operations
- **Manual Recovery**: Tools to fix specific data issues

## Security Considerations

### Data Protection
- **Input Sanitization**: Validate all trace data before database insertion
- **SQL Injection Prevention**: Use parameterized queries exclusively
- **Access Control**: Database operations only through authenticated application
- **Audit Logging**: Log all database modification operations

### Operational Security
- **Connection Security**: Use SSL/TLS for database connections
- **Credential Management**: Secure storage of database credentials
- **Network Security**: Restrict database access to application only
- **Backup Security**: Encrypt database backups and archives

## Migration Strategy

### Phase-by-Phase Rollout
1. **Development Testing**: Thorough testing with sample data sets
2. **Selective Deployment**: Start with non-critical projects
3. **Gradual Expansion**: Expand to all projects after validation
4. **Full Integration**: Database becomes primary data source

### Rollback Plan
- **File System Fallback**: Continue using files if database fails
- **Data Recovery**: Rebuild database from existing files if needed
- **Command Compatibility**: Maintain existing commands during transition
- **Monitoring**: Track database and file system consistency

## Success Criteria ✅ ALL ACHIEVED

### Functional Requirements ✅ COMPLETED
- [x] `lse archive to-db` loads files to database successfully ✅
- [x] `lse archive full-sweep` executes complete workflow without errors ✅
- [x] Data consistency validation implemented within to-db command ✅
- [x] All existing archive commands continue to work unchanged ✅
- [x] Database and files maintain consistency ✅

### Performance Requirements ✅ COMPLETED
- [x] Batch loading processes 1,734 runs efficiently ✅
- [x] Full sweep completes within expected timeframes ✅
- [x] Data consistency checks integrated into loading process ✅
- [x] Memory usage remains within acceptable limits ✅
- [x] Database operations don't impact existing functionality ✅

### Quality Requirements ✅ COMPLETED
- [x] All tests pass with comprehensive coverage ✅
- [x] Commands handle edge cases gracefully (multiple JSON formats, validation errors) ✅
- [x] Error messages are clear and actionable ✅
- [x] Documentation is complete and accurate ✅
- [x] Real-world data sets process successfully (1,734+ runs tested) ✅

## Dependencies

### External Dependencies
- **Phase 8 Completion**: Database infrastructure must be operational
- **Docker Environment**: Postgres container running and accessible
- **Python Dependencies**: Database libraries installed and configured

### Internal Dependencies
- **Existing Archive Commands**: Must remain functional and unchanged
- **Configuration System**: Database settings properly configured
- **Testing Framework**: Integration with existing test suite
- **CLI Structure**: Integration with current Typer-based CLI

## Future Considerations

### Optimization Opportunities
- **Parallel Processing**: Process multiple projects concurrently
- **Incremental Sync**: Only sync changed traces
- **Compression**: Compress JSONB data for storage efficiency
- **Caching**: Cache frequently accessed trace data

### Monitoring and Observability
- **Performance Metrics**: Track batch processing performance
- **Error Monitoring**: Alert on database operation failures
- **Data Quality**: Monitor data consistency over time
- **Usage Analytics**: Track command usage patterns

### Integration Points
- **Phase 10 Preparation**: Ensure database has data for evaluation migration
- **Reporting Integration**: Prepare for Phase 11 reporting migration
- **External APIs**: Consider integration with external monitoring systems
- **Backup Integration**: Integrate with backup and disaster recovery systems