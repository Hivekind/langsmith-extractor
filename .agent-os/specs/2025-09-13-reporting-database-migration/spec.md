# Phase 11: Reporting Database Migration Specification ✅ COMPLETED

## Overview
Migrate all reporting commands from file-based storage to database queries while maintaining identical output formats and command interfaces. This phase completes the database migration by switching the final component from file operations to database operations.

**Status**: COMPLETED ✅ - Successfully migrated all reporting to database backend with identical functionality and improved performance.

## Problem Statement
Current reporting limitations with file-based storage:
1. **Local File Dependency**: Requires all trace data to be available locally
2. **File System Performance**: File scanning becomes slow with large datasets
3. **Limited Query Capabilities**: Cannot leverage database query optimizations
4. **Storage Requirements**: Must maintain complete local file copies
5. **Scalability Issues**: File operations don't scale well with dataset growth

Target improvements:
1. **Database-Driven**: All reports query Postgres directly
2. **Maintained Compatibility**: Identical output format and command interface
3. **Performance Gains**: Database queries faster than file scanning
4. **Query Optimization**: Leverage database indexes and aggregation
5. **Reduced Dependencies**: No requirement for local file storage

## Current Reporting Architecture

### Current Commands
```bash
# Zenrows error aggregation report
lse report zenrows-errors --date 2025-09-13 --project my-project

# Zenrows detailed error analysis
lse report zenrows-detail --date 2025-09-13 --project my-project
```

### Current Data Flow
```
Local Files → File Scanner → TraceAnalyzer → Report Formatter → Output
     ↓              ↓              ↓              ↓           ↓
JSON files    find_trace_files  extract_*     format_*    CSV/Text
```

### Target Data Flow
```
Database → Run Aggregation → Trace Reconstruction → Report Formatter → Output
    ↓              ↓                ↓                   ↓           ↓
Run docs    GROUP BY trace_id   Aggregated traces    format_*    CSV/Text
```

## Solution Design

### Database-Driven Reporting Architecture

#### Enhanced TraceAnalyzer
```python
class TraceAnalyzer:
    """Analyze trace data from database for reporting by aggregating runs."""
    
    def __init__(self, database_manager: DatabaseManager):
        self.db = database_manager
    
    async def analyze_zenrows_errors_from_db(
        self,
        project_name: Optional[str] = None,
        single_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Analyze zenrows errors from database by aggregating runs into traces.
        
        Args:
            project_name: Project to analyze (None for all projects)
            single_date: Date to analyze (required)
            
        Returns:
            Analysis results with same format as file-based version
        """
        date_str = single_date.strftime("%Y-%m-%d")
        
        async with self.db.get_session() as session:
            # Aggregate runs by trace_id and analyze for zenrows errors
            query = """
            WITH trace_analysis AS (
                SELECT 
                    trace_id,
                    project,
                    array_agg(data ORDER BY run_id) as run_data_array,
                    COUNT(*) as run_count
                FROM runs 
                WHERE run_date = :date
                AND (:project IS NULL OR project = :project)
                GROUP BY trace_id, project
            ),
            trace_errors AS (
                SELECT 
                    trace_id,
                    project,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM unnest(run_data_array) as run_data
                            WHERE 
                                -- Check if this run is zenrows_scraper with error
                                (run_data->'trace'->>'name' = 'zenrows_scraper' 
                                 AND run_data->'trace'->>'status' != 'success')
                                OR
                                -- Check if this run has child runs with zenrows errors
                                jsonb_path_exists(
                                    run_data->'trace', 
                                    '$.child_runs[*] ? (@.name == "zenrows_scraper" && @.status != "success")'
                                )
                        ) THEN 1 
                        ELSE 0 
                    END as has_zenrows_error
                FROM trace_analysis
            )
            SELECT 
                COUNT(*) as total_traces,
                SUM(has_zenrows_error) as zenrows_errors,
                ROUND(
                    CASE 
                        WHEN COUNT(*) > 0 THEN (SUM(has_zenrows_error)::float / COUNT(*)) * 100
                        ELSE 0 
                    END, 
                    1
                ) as error_rate
            FROM trace_errors
            """
            
            result = await session.execute(
                query, 
                {"date": date_str, "project": project_name}
            )
            row = result.fetchone()
            
            return {
                "date": date_str,
                "total_traces": row.total_traces or 0,
                "zenrows_errors": row.zenrows_errors or 0,
                "error_rate": row.error_rate or 0.0
            }
```

#### Database Query Patterns for Reporting
```sql
-- Zenrows error detection with run aggregation
WITH trace_analysis AS (
    SELECT 
        trace_id,
        project,
        array_agg(data ORDER BY run_id) as run_data_array
    FROM runs 
    WHERE project = $1 AND run_date = $2
    GROUP BY trace_id, project
)
SELECT 
    trace_id,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM unnest(run_data_array) as run_data
            WHERE 
                (run_data->'trace'->>'name' = 'zenrows_scraper' 
                 AND run_data->'trace'->>'status' != 'success')
                OR
                jsonb_path_exists(
                    run_data->'trace', 
                    '$.child_runs[*] ? (@.name == "zenrows_scraper" && @.status != "success")'
                )
        ) THEN true 
        ELSE false 
    END as has_zenrows_error
FROM trace_analysis;

-- Detailed zenrows error analysis with run aggregation
WITH trace_reconstruction AS (
    SELECT 
        trace_id,
        array_agg(data ORDER BY run_id) as run_data_array
    FROM runs 
    WHERE project = $1 AND run_date = $2
    GROUP BY trace_id
),
trace_details AS (
    SELECT 
        trace_id,
        -- Extract crypto symbol from any run in the trace (typically root run)
        (SELECT run_data->'trace'->'inputs'->>'crypto_symbol' 
         FROM unnest(run_data_array) as run_data 
         WHERE run_data->'trace'->'inputs' ? 'crypto_symbol' 
         LIMIT 1) as crypto_symbol,
        -- Extract zenrows errors from all runs
        (SELECT array_agg(
            jsonb_build_object(
                'run_id', run_data->'trace'->>'id',
                'name', run_data->'trace'->>'name',
                'status', run_data->'trace'->>'status',
                'error', run_data->'trace'->'error',
                'start_time', run_data->'trace'->>'start_time'
            )
         )
         FROM unnest(run_data_array) as run_data
         WHERE 
            (run_data->'trace'->>'name' = 'zenrows_scraper' 
             AND run_data->'trace'->>'status' != 'success')
            OR
            jsonb_path_exists(
                run_data->'trace', 
                '$.child_runs[*] ? (@.name == "zenrows_scraper" && @.status != "success")'
            )
        ) as zenrows_errors
    FROM trace_reconstruction
)
SELECT trace_id, crypto_symbol, zenrows_errors
FROM trace_details
WHERE zenrows_errors IS NOT NULL AND array_length(zenrows_errors, 1) > 0;
```

### Enhanced Report Commands

#### Database-Driven zenrows-errors Command
```python
@report_app.command("zenrows-errors")
def zenrows_errors(
    date: str = typer.Option(
        ..., "--date", help="Date in YYYY-MM-DD format (UTC)", show_default=False
    ),
    project: Optional[str] = typer.Option(
        None, "--project", help="Project name to analyze (omit for all projects)"
    ),
):
    """Generate zenrows error report for specified date using database."""
    
    # Validate date
    try:
        parsed_date = validate_date(date)
    except ValidationError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    
    # Generate report from database
    try:
        report = asyncio.run(generate_zenrows_report_from_db(
            project_name=project,
            single_date=parsed_date
        ))
        console.print(report)
    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        raise typer.Exit(1)

async def generate_zenrows_report_from_db(
    project_name: Optional[str] = None,
    single_date: Optional[datetime] = None,
) -> str:
    """Generate zenrows error report from database.
    
    Args:
        project_name: Project to analyze (None for all projects)
        single_date: Date to analyze (required)
        
    Returns:
        CSV formatted report string (identical to file-based version)
    """
    settings = get_settings()
    database_manager = DatabaseManager(settings.database.database_url)
    analyzer = TraceAnalyzer(database_manager)
    
    try:
        analysis_results = await analyzer.analyze_zenrows_errors_from_db(
            project_name=project_name,
            single_date=single_date
        )
        
        # Format results using existing formatter (unchanged)
        formatter = ReportFormatter()
        return formatter.format_zenrows_errors_csv([analysis_results])
        
    finally:
        await database_manager.engine.dispose()
```

#### Database-Driven zenrows-detail Command
```python
@report_app.command("zenrows-detail")
def zenrows_detail(
    date: str = typer.Option(
        ..., "--date", help="Date in YYYY-MM-DD format (UTC)", show_default=False
    ),
    project: Optional[str] = typer.Option(
        None, "--project", help="Project name to analyze (omit for all projects)"
    ),
    format_type: str = typer.Option(
        "text", "--format", help="Output format (text or json)"
    ),
):
    """Generate detailed zenrows error report using database."""
    
    # Validate parameters
    try:
        parsed_date = validate_date(date)
    except ValidationError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    
    if format_type not in ["text", "json"]:
        console.print("[red]Error: Format must be 'text' or 'json'[/red]")
        raise typer.Exit(1)
    
    # Generate detailed report from database
    try:
        report = asyncio.run(generate_zenrows_detail_from_db(
            project_name=project,
            single_date=parsed_date,
            format_type=format_type
        ))
        console.print(report)
    except Exception as e:
        console.print(f"[red]Error generating detailed report: {e}[/red]")
        raise typer.Exit(1)
```

### Database Aggregation Utilities

#### Zenrows Error Aggregation
```python
class DatabaseReportAggregator:
    """Database-specific aggregation utilities for reporting."""
    
    def __init__(self, database_manager: DatabaseManager):
        self.db = database_manager
    
    async def aggregate_zenrows_errors(
        self, 
        project: Optional[str], 
        date: str
    ) -> Dict[str, Any]:
        """Aggregate zenrows errors for a specific date and project."""
        
        async with self.db.get_session() as session:
            query = """
            WITH error_analysis AS (
                SELECT 
                    trace_id,
                    project,
                    data,
                    -- Check root trace for zenrows errors
                    CASE 
                        WHEN data->'name' = '"zenrows_scraper"' 
                             AND data->'status' != '"success"' 
                        THEN 1 ELSE 0 
                    END as root_zenrows_error,
                    -- Check child runs for zenrows errors
                    CASE 
                        WHEN jsonb_path_exists(
                            data, 
                            '$.child_runs[*] ? (@.name == "zenrows_scraper" && @.status != "success")'
                        ) THEN 1 ELSE 0
                    END as child_zenrows_error
                FROM traces 
                WHERE trace_date = :date
                AND (:project IS NULL OR project = :project)
            )
            SELECT 
                COUNT(*) as total_traces,
                SUM(GREATEST(root_zenrows_error, child_zenrows_error)) as zenrows_errors
            FROM error_analysis
            """
            
            result = await session.execute(
                query,
                {"date": date, "project": project}
            )
            
            row = result.fetchone()
            total = row.total_traces or 0
            errors = row.zenrows_errors or 0
            
            return {
                "total_traces": total,
                "zenrows_errors": errors,
                "error_rate": round((errors / total * 100) if total > 0 else 0.0, 1)
            }
    
    async def get_detailed_zenrows_errors(
        self, 
        project: Optional[str], 
        date: str
    ) -> List[Dict[str, Any]]:
        """Get detailed zenrows error information."""
        
        async with self.db.get_session() as session:
            query = """
            SELECT 
                trace_id,
                data->'inputs'->>'crypto_symbol' as crypto_symbol,
                data->'name' as trace_name,
                data->'start_time' as start_time,
                -- Extract zenrows errors from root or child runs
                CASE 
                    WHEN data->'name' = '"zenrows_scraper"' AND data->'status' != '"success"'
                    THEN jsonb_build_array(
                        jsonb_build_object(
                            'name', data->'name',
                            'status', data->'status',
                            'error', data->'error',
                            'inputs', data->'inputs'
                        )
                    )
                    ELSE jsonb_path_query_array(
                        data, 
                        '$.child_runs[*] ? (@.name == "zenrows_scraper" && @.status != "success")'
                    )
                END as zenrows_errors
            FROM traces 
            WHERE trace_date = :date
            AND (:project IS NULL OR project = :project)
            AND (
                (data->'name' = '"zenrows_scraper"' AND data->'status' != '"success"')
                OR jsonb_path_exists(
                    data, 
                    '$.child_runs[*] ? (@.name == "zenrows_scraper" && @.status != "success")'
                )
            )
            ORDER BY data->'inputs'->>'crypto_symbol', trace_id
            """
            
            result = await session.execute(
                query,
                {"date": date, "project": project}
            )
            
            errors = []
            for row in result.fetchall():
                errors.append({
                    "trace_id": row.trace_id,
                    "crypto_symbol": row.crypto_symbol,
                    "trace_name": row.trace_name,
                    "start_time": row.start_time,
                    "zenrows_errors": row.zenrows_errors
                })
            
            return errors
```

### Performance Optimization

#### Specialized Indexes for Reporting
```sql
-- Index for zenrows error detection on runs
CREATE INDEX idx_runs_zenrows_errors 
ON runs(project, run_date, trace_id) 
WHERE data->'trace'->>'name' = 'zenrows_scraper' 
   OR jsonb_path_exists(data->'trace', '$.child_runs[*] ? (@.name == "zenrows_scraper")');

-- Index for crypto symbol grouping from runs
CREATE INDEX idx_runs_crypto_symbol 
ON runs USING gin((data->'trace'->'inputs'->>'crypto_symbol'))
WHERE data->'trace'->'inputs'->>'crypto_symbol' IS NOT NULL;

-- Index for timestamp-based queries on runs
CREATE INDEX idx_runs_start_time 
ON runs USING gin((data->'trace'->>'start_time'))
WHERE data->'trace'->>'start_time' IS NOT NULL;

-- Composite index for trace aggregation in reporting
CREATE INDEX idx_runs_trace_aggregation 
ON runs(trace_id, project, run_date, run_id)
WHERE data->'trace' IS NOT NULL;

-- Partial index for runs with zenrows activity
CREATE INDEX idx_runs_zenrows_activity
ON runs(project, run_date, trace_id)
WHERE data->'trace'->>'name' LIKE '%zenrows%' 
   OR jsonb_path_exists(data->'trace', '$.child_runs[*] ? (@.name like_regex ".*zenrows.*")');

-- GIN index for efficient JSONB path queries
CREATE INDEX idx_runs_trace_gin 
ON runs USING gin((data->'trace'))
WHERE data->'trace' IS NOT NULL;
```

#### Query Optimization Strategies
```python
class QueryOptimizer:
    """Optimize database queries for reporting performance."""
    
    @staticmethod
    def get_optimized_zenrows_query(project: Optional[str] = None) -> str:
        """Get optimized query for zenrows error detection."""
        
        base_query = """
        SELECT 
            trace_id,
            project,
            trace_date,
            data->'inputs'->>'crypto_symbol' as crypto_symbol,
            data->'start_time' as start_time,
            CASE 
                WHEN data->'name' = '"zenrows_scraper"' AND data->'status' != '"success"' THEN 1
                WHEN jsonb_path_exists(
                    data, 
                    '$.child_runs[*] ? (@.name == "zenrows_scraper" && @.status != "success")'
                ) THEN 1
                ELSE 0
            END as has_error
        FROM traces 
        WHERE trace_date = :date
        """
        
        if project:
            base_query += " AND project = :project"
        
        # Add index hints for better performance
        base_query += """
        AND (
            data->'name' = '"zenrows_scraper"' 
            OR data ? 'child_runs'
        )
        ORDER BY project, trace_date, trace_id
        """
        
        return base_query
```

## Implementation Plan

### Phase 1: Database Integration Foundation (Week 1)
- [ ] Add DatabaseManager integration to TraceAnalyzer
- [ ] Create database aggregation utilities
- [ ] Implement async report generation functions
- [ ] Add database connection management for report commands
- [ ] Create specialized indexes for reporting queries

### Phase 2: zenrows-errors Migration (Week 1)
- [ ] Implement database-driven zenrows error analysis
- [ ] Update zenrows-errors command to use database
- [ ] Add comprehensive error handling for database operations
- [ ] Validate identical output format with file-based version
- [ ] Add performance optimization for aggregation queries

### Phase 3: zenrows-detail Migration (Week 2)
- [ ] Implement database-driven detailed error analysis
- [ ] Update zenrows-detail command to use database
- [ ] Add crypto symbol grouping via database queries
- [ ] Implement hierarchical formatting from database results
- [ ] Add query optimization for complex JSONB operations

### Phase 4: Performance Optimization (Week 2)
- [ ] Add specialized database indexes for reporting
- [ ] Optimize JSONB query patterns for performance
- [ ] Implement query result caching where appropriate
- [ ] Add query performance monitoring and logging
- [ ] Tune aggregation queries for large datasets

### Phase 5: Testing and Validation (Week 3)
- [ ] Write comprehensive database reporting tests
- [ ] Create performance regression tests
- [ ] Validate output format compatibility
- [ ] Add integration tests with real database
- [ ] Test with large datasets for performance validation

## Testing Strategy

### Unit Tests
```python
# tests/test_database_reporting.py
@pytest.mark.asyncio
async def test_zenrows_error_aggregation():
    # Setup test database with known zenrows errors
    await setup_test_traces_with_zenrows_errors()
    
    analyzer = TraceAnalyzer(get_test_database_manager())
    
    result = await analyzer.analyze_zenrows_errors_from_db(
        project_name="test-project",
        single_date=datetime(2025, 9, 13)
    )
    
    # Validate aggregation results
    assert result["total_traces"] == 100
    assert result["zenrows_errors"] == 15
    assert result["error_rate"] == 15.0

@pytest.mark.asyncio
async def test_detailed_error_extraction():
    await setup_test_traces_with_detailed_errors()
    
    aggregator = DatabaseReportAggregator(get_test_database_manager())
    
    errors = await aggregator.get_detailed_zenrows_errors(
        project="test-project",
        date="2025-09-13"
    )
    
    # Validate detailed error structure
    assert len(errors) > 0
    assert all("trace_id" in error for error in errors)
    assert all("crypto_symbol" in error for error in errors)
    assert all("zenrows_errors" in error for error in errors)
```

### Output Compatibility Tests
```python
# tests/test_report_output_compatibility.py
@pytest.mark.asyncio
async def test_zenrows_errors_output_format():
    # Generate report using database
    db_report = await generate_zenrows_report_from_db(
        project_name="test-project",
        single_date=datetime(2025, 9, 13)
    )
    
    # Generate report using files (for comparison)
    file_report = generate_zenrows_report_from_files(
        project_name="test-project", 
        single_date=datetime(2025, 9, 13)
    )
    
    # Validate identical format
    assert db_report.split('\n')[0] == file_report.split('\n')[0]  # Header
    assert len(db_report.split('\n')) == len(file_report.split('\n'))  # Line count
    
    # Parse and compare data
    db_lines = [line.split(',') for line in db_report.strip().split('\n')[1:]]
    file_lines = [line.split(',') for line in file_report.strip().split('\n')[1:]]
    
    assert db_lines == file_lines
```

### Performance Tests
```python
# tests/test_reporting_performance.py
@pytest.mark.asyncio
async def test_large_dataset_reporting_performance():
    # Setup database with 30 days of data
    await populate_database_for_performance_test(days=30, traces_per_day=500)
    
    analyzer = TraceAnalyzer(get_test_database_manager())
    
    start_time = time.time()
    result = await analyzer.analyze_zenrows_errors_from_db(
        project_name="large-project",
        single_date=datetime(2025, 9, 13)
    )
    duration = time.time() - start_time
    
    # Performance assertions
    assert duration < 5.0  # Should complete within 5 seconds
    assert result["total_traces"] == 500
    assert "error_rate" in result

@pytest.mark.asyncio
async def test_query_optimization_effectiveness():
    # Test with and without indexes
    await create_large_test_dataset()
    
    # Test without indexes
    await drop_reporting_indexes()
    start_time = time.time()
    await run_zenrows_analysis()
    slow_duration = time.time() - start_time
    
    # Test with indexes
    await create_reporting_indexes()
    start_time = time.time()
    await run_zenrows_analysis()
    fast_duration = time.time() - start_time
    
    # Validate performance improvement
    assert fast_duration < slow_duration * 0.5  # At least 50% improvement
```

## Migration Strategy

### Backward Compatibility
- **Command Interface**: Identical parameter names and help text
- **Output Format**: Exact same CSV/text format as file-based version
- **Error Handling**: Consistent error messages and exit codes
- **Performance**: Database version should be faster than file version

### Deployment Strategy
1. **Parallel Implementation**: Maintain both file and database versions initially
2. **Feature Flag**: Environment variable to switch between implementations
3. **A/B Testing**: Compare outputs between file and database versions
4. **Gradual Rollout**: Enable database version for specific projects first
5. **Full Migration**: Remove file-based implementation after validation

### Rollback Plan
- **File Fallback**: Ability to revert to file-based reporting if needed
- **Data Verification**: Ensure database contains all necessary historical data
- **Performance Monitoring**: Track query performance vs file scanning times
- **User Communication**: Clear communication about any changes in behavior

## Performance Considerations

### Query Performance
- **Index Utilization**: Ensure all queries use appropriate indexes
- **Query Planning**: Use EXPLAIN ANALYZE for optimization
- **Connection Pooling**: Reuse database connections efficiently
- **Aggregation Optimization**: Use database aggregation functions

### Memory Management
- **Streaming Results**: Process large result sets without loading all in memory
- **Connection Cleanup**: Proper cleanup of database connections
- **Garbage Collection**: Explicit cleanup of large result objects
- **Resource Monitoring**: Track memory usage during report generation

### Scalability
- **Large Datasets**: Handle projects with millions of traces
- **Concurrent Reports**: Support multiple users generating reports simultaneously
- **Query Timeouts**: Reasonable timeouts for complex queries
- **Resource Limits**: Respect database connection and CPU limits

## Security Considerations

### Query Security
- **Parameterized Queries**: All database queries use parameters
- **Input Validation**: Validate all date and project parameters
- **SQL Injection Prevention**: No dynamic SQL construction
- **Access Control**: Reports only access authorized project data

### Data Protection
- **Sensitive Data**: Handle trace data containing sensitive information securely
- **Audit Logging**: Log report generation operations
- **Error Messages**: Don't expose internal database structure in errors
- **Data Masking**: Consider masking sensitive data in error reports

## Success Criteria

### Functional Requirements
- [ ] All report commands work with database backend
- [ ] Output format identical to file-based version
- [ ] All existing command parameters work unchanged
- [ ] Error handling provides clear feedback
- [ ] Reports complete successfully for all project sizes

### Performance Requirements
- [ ] Database reports faster than file-based equivalents
- [ ] Single date reports complete within 30 seconds
- [ ] Large project reports complete within 2 minutes
- [ ] Memory usage stays within 512MB for typical operations
- [ ] Database queries utilize indexes efficiently

### Quality Requirements
- [ ] Test coverage maintains 95%+ for all reporting code
- [ ] Output compatibility validated with extensive test suites
- [ ] Performance regression tests validate acceptable execution times
- [ ] Documentation updated for any behavioral changes
- [ ] Real-world datasets process successfully

## Dependencies

### External Dependencies
- **Phase 9 Completion**: Database must be populated with comprehensive trace data
- **Database Performance**: Postgres properly tuned for reporting queries
- **Network Connectivity**: Reliable database connection for report generation
- **Historical Data**: All required historical trace data available in database

### Internal Dependencies
- **Report Formatters**: Existing formatting code must remain compatible
- **CLI Framework**: Integration with existing Typer-based command structure
- **Configuration System**: Database connection settings properly configured
- **Error Handling**: Consistent error handling across all commands

## Risks and Mitigation

### Technical Risks
- **Query Performance**: Complex JSONB queries may perform poorly
  - *Mitigation*: Comprehensive indexing and query optimization
- **Output Differences**: Database results may differ slightly from file results
  - *Mitigation*: Extensive validation and comparison testing
- **Database Dependency**: Reports become dependent on database availability
  - *Mitigation*: Robust error handling and connection retry logic

### Operational Risks
- **User Experience**: Changes in report generation speed or behavior
  - *Mitigation*: Performance improvements and clear communication
- **Data Consistency**: Reports may show different results if database is incomplete
  - *Mitigation*: Data validation tools and verification procedures
- **Rollback Complexity**: Difficulty reverting to file-based system
  - *Mitigation*: Maintain file-based fallback during transition period

## Future Enhancements

### Advanced Features
- **Caching**: Cache report results for frequently requested data
- **Real-time Reports**: Live reporting as new data arrives
- **Custom Reports**: User-defined report templates and queries
- **Export Formats**: Additional output formats (Excel, PDF, etc.)

### Integration Opportunities
- **Dashboards**: Integration with monitoring dashboards
- **APIs**: REST APIs for external report requests
- **Scheduling**: Automated report generation and delivery
- **Visualization**: Charts and graphs for report data