#!/usr/bin/env python3
# LangSmith Extractor - Product Roadmap

This is a comprehensive product roadmap for the LangSmith Extractor (LSE) project, maintained as a living document within the codebase following Agent-OS principles.

## Quick Navigation
- [Phase 1: MVP Data Extraction](#phase-1-mvp-data-extraction-) ✅ **COMPLETED**
- [Phase 2: Automated archival to Google Drive](#phase-2-automated-archival-to-google-drive-) ✅ **COMPLETED**
- [Phase 3: Standardized reporting](#phase-3-standardized-reporting-) ✅ **COMPLETED** 
- [Phase 4: Advanced analysis capabilities](#phase-4-advanced-analysis-capabilities-) ✅ **COMPLETED**
- [Phase 5: Automated integration](#phase-5-automated-integration-) ⚠️ **IN DEVELOPMENT**
- [Phase 6: Evaluation capabilities](#phase-6-evaluation-capabilities-) ✅ **COMPLETED**
- [Phase 7: Tracing capabilities](#phase-7-tracing-capabilities-) 🔄 **PLANNED**
- [Phase 8: Database Infrastructure Setup](#phase-8-database-infrastructure-setup-) ✅ **COMPLETED**
- [Phase 9: Archive Tool Database Integration](#phase-9-archive-tool-database-integration-) ✅ **COMPLETED**
- [Phase 10: Evaluation Dataset Database Migration](#phase-10-evaluation-dataset-database-migration-) ✅ **COMPLETED**
- [Phase 11: Reporting Database Migration](#phase-11-reporting-database-migration-) ✅ **COMPLETED**
- [**Phase 12: Critical Feedback Data Loss Fix**](#phase-12-critical-feedback-data-loss-fix--urgent) 🚨 **URGENT**
- [**Phase 13: Dataset Format Fix**](#phase-13-dataset-format-fix--urgent) 🚨 **URGENT**
- [**Phase 15: Availability Dataset Root Run Priority Bug**](#phase-15-availability-dataset-root-run-priority-bug--urgent) ✅ **COMPLETED**
- [**Phase 16: Availability Dataset Curation (Best 100)**](#phase-16-availability-dataset-curation-best-100-) 🎯 **NEXT**
- [**Phase 17: Is_Available Report Feature**](#phase-17-is_available-report-feature-) 🔄 **PLANNED**

---

## Project Mission
LangSmith Extractor enables teams to extract, analyze, and archive LangSmith trace data efficiently, providing comprehensive local analysis capabilities, automated reporting, and secure archival workflows.

## Current Status

### ✅ Production Ready Features
- **Archive System**: Full workflow (fetch → zip → upload → database storage)
- **Database Integration**: PostgreSQL with JSONB storage for scalable trace analysis
- **Reporting System**: Database-driven zenrows error analysis with CSV export
- **Evaluation System**: Dataset creation, LangSmith upload, external API integration
- **Google Drive Integration**: Automated secure archival with OAuth2 authentication

### 🚨 Critical Issues
- **Phase 12**: **Critical feedback data loss** - detailed feedback rationale missing from extraction
- **Phase 13**: **Dataset format generation** - eval create-dataset producing wrong output format

### 🎯 Next Priority
- **Phase 16**: **Availability dataset curation** - implement --best-100 feature for curated representative datasets

---

## Phase 1: MVP Data Extraction ✅ **COMPLETED**

**Goal:** Basic CLI tool for extracting LangSmith trace data
**Success Criteria:** Can extract traces for specific date/project combinations and save locally

### Features
- [x] **Basic CLI structure** - Typer-based command interface `M`
- [x] **LangSmith API integration** - Reliable API client with authentication `M`
- [x] **Date-based extraction** - Extract traces for specific dates in UTC `M`
- [x] **Project filtering** - Filter traces by project name `M`
- [x] **Local storage** - Save traces as JSON files with organized directory structure `M`
- [x] **Basic error handling** - Graceful handling of API failures and network issues `S`
- [x] **Progress tracking** - Show progress during long extraction operations `S`

### Technical Implementation
- **CLI Framework**: Typer for command-line interface
- **API Client**: langsmith SDK with custom retry logic
- **Storage**: Local JSON files organized by project/date
- **Configuration**: Environment-based settings using Pydantic

### Dependencies
- LangSmith account with API access
- Python 3.13+ development environment
- Basic project structure and dependencies

---

## Phase 2: Automated archival to Google Drive ✅ **COMPLETED**

**Goal:** Secure archival of extracted trace data to Google Drive
**Success Criteria:** Extracted traces automatically compressed and uploaded to designated Google Drive folder

### Features
- [x] **ZIP compression** - Compress trace data for efficient storage and transfer `M`
- [x] **Google Drive integration** - Upload compressed archives to specified folder `M`
- [x] **OAuth2 authentication** - Secure Google Drive access using OAuth2 flow `M`
- [x] **Flexible folder targets** - Support both personal and shared Drive folders `M`
- [x] **Upload verification** - Verify successful upload and provide confirmation `S`
- [x] **Duplicate handling** - Avoid re-uploading existing archives `S`
- [x] **Progress tracking** - Show upload progress for large files `S`

### Technical Implementation
- **Compression**: Python zipfile for efficient archive creation
- **Google Drive API**: google-api-python-client with OAuth2 authentication
- **Authentication**: Token caching for seamless re-authentication
- **Configuration**: Environment variables for Drive folder URLs and credentials

### Dependencies
- Google Cloud Console project with Drive API enabled
- OAuth2 client credentials (client ID and secret)
- Designated Google Drive folder for archives

---

## Phase 3: Standardized reporting ✅ **COMPLETED**

**Goal:** Generate standardized analysis reports from archived trace data
**Success Criteria:** Automated report generation with consistent formats for stakeholder consumption

### Features
- [x] **CSV report generation** - Structured data reports for spreadsheet analysis `M`
- [x] **Multiple report types** - Support various analysis perspectives and metrics `M`
- [x] **Date range support** - Generate reports across multiple days/periods `M`
- [x] **Project aggregation** - Combine data across multiple projects for comprehensive analysis `M`
- [x] **Error analysis** - Specific reports for error patterns and failure analysis `S`
- [x] **Summary statistics** - High-level metrics and trends in reports `S`
- [x] **Export flexibility** - Multiple output formats and destinations `S`

### Technical Implementation
- **Report Engine**: Modular reporting system with pluggable analyzers
- **Data Processing**: Pandas-like analysis capabilities for trace data
- **Output Formats**: CSV, JSON, and plain text report generation
- **Aggregation**: Statistical analysis across multiple trace files

### Dependencies  
- Phase 1 (MVP extraction) completed
- Local trace data storage established
- Analysis requirements defined

---

## Phase 4: Advanced analysis capabilities ✅ **COMPLETED**

**Goal:** Deep analysis capabilities for complex trace pattern detection
**Success Criteria:** Automated detection of specific error patterns and performance insights

### Features
- [x] **Zenrows error detection** - Specialized analysis for zenrows-related failures `M`
- [x] **Pattern recognition** - Automated detection of recurring issues and anomalies `M`
- [x] **Performance metrics** - Analysis of response times, costs, and resource usage `M`
- [x] **Detailed reporting** - Granular analysis with specific error categorization `M`
- [x] **Trend analysis** - Historical pattern detection and alerting `S`
- [x] **Custom filters** - Flexible filtering for focused analysis `S`
- [x] **Data export** - Export analysis results for further processing `S`

### Technical Implementation
- **Analysis Engine**: Specialized analyzers for different error types and patterns
- **Pattern Detection**: Regular expression and heuristic-based pattern matching
- **Metrics Calculation**: Statistical analysis of performance and error data
- **Report Formatting**: Rich text and structured output for different audiences

### Dependencies
- Phase 3 (Standardized reporting) completed
- Historical trace data for trend analysis
- Specific analysis requirements and patterns defined

---

## Phase 5: Automated integration ⚠️ **IN DEVELOPMENT**

**Goal:** Automated daily extraction and analysis workflows
**Success Criteria:** Scheduled daily operations with error notifications and stakeholder alerts

### Features
- [ ] **Scheduled execution** - Automated daily trace extraction and analysis `M`
- [ ] **Error notifications** - Automated alerts for extraction failures or anomalies `M` 
- [ ] **Stakeholder reporting** - Automated report distribution to relevant teams `M`
- [ ] **Health monitoring** - System health checks and performance monitoring `M`
- [ ] **Failure recovery** - Automated retry logic and graceful degradation `S`
- [ ] **Configuration management** - Centralized configuration for automated workflows `S`
- [ ] **Audit logging** - Comprehensive logging of all automated operations `S`

### Technical Implementation
- **Scheduler**: Cron-based or cloud-based scheduling for daily operations
- **Monitoring**: Health checks and performance metrics collection
- **Notifications**: Email, Slack, or webhook-based alerting systems
- **Recovery**: Automatic retry logic with exponential backoff

### Dependencies
- Phases 1-4 completed and stable
- Production deployment environment established
- Notification channels and stakeholders identified
- Monitoring infrastructure in place

---

## Phase 6: Evaluation capabilities ✅ **COMPLETED**

**Goal:** Create evaluation datasets from trace data and integrate with external evaluation APIs
**Success Criteria:** Automated dataset generation with external evaluation system integration

### Features

- [x] **Dataset creation** - Generate evaluation datasets from trace data with AI/human feedback filtering `M` ✅
- [x] **LangSmith upload** - Upload datasets to LangSmith for evaluation workflows `M` ✅
- [x] **External API integration** - Integration with external evaluation APIs for automated testing `M` ✅  
- [x] **Data validation** - Ensure dataset quality and completeness before evaluation `S` ✅
- [x] **Format standardization** - Support multiple dataset formats (JSON, JSONL) `S` ✅
- [x] **Batch processing** - Efficient processing of large trace datasets `S` ✅
- [x] **Progress tracking** - Real-time progress reporting during dataset creation `S` ✅

### Completed Implementation

#### Dataset Creation from Traces
- **TraceExtractor**: Filters traces with both AI output and human feedback
- **DatasetBuilder**: Converts filtered traces into evaluation dataset format
- **Format Support**: JSON and JSONL output formats with configurable structure
- **Quality Validation**: Ensures proper inputs, outputs, and reference data

#### LangSmith Integration  
- **LangSmithUploader**: Direct upload to LangSmith with dataset management
- **Overwrite Support**: Handle existing datasets with configurable overwrite behavior
- **Error Handling**: Comprehensive error handling for upload failures
- **Progress Tracking**: Real-time upload progress with Rich progress bars

#### External API Integration
- **EvaluationAPIClient**: HTTP client for external evaluation system integration
- **Authentication**: Signature-based authentication using SHA-256 payload signing
- **Error Handling**: Robust HTTP error handling with retry mechanisms
- **Response Processing**: Structured response handling and validation

### Command Interface
```bash
# Create dataset from traces
lse eval create-dataset --traces traces.json --eval-type accuracy --name my_dataset

# Upload dataset to LangSmith  
lse eval upload --dataset dataset.json --name eval_dataset_2025_09

# Run evaluation via external API
lse eval run --dataset-name eval_dataset_2025_09 --experiment-prefix exp_20250913 --eval-type accuracy
```

### External Evaluation API Integration

#### API Endpoint
- **URL**: Configured via `EVAL_API_ENDPOINT` environment variable
- **Example**: `https://example.com/api/run_eval`
- **Method**: POST request with payload

#### Authentication & Security
- **Signature-based Authentication**: SHA-256 HMAC signatures for request validation
- **Payload Signing**: Complete request payload used for signature generation
- **Environment Configuration**: API endpoint and credentials via environment variables

#### Request/Response Format
```json
// Request Payload
{
  "dataset_name": "eval_dataset_2025_09",
  "experiment_prefix": "exp_20250913", 
  "eval_type": "accuracy",
  "signature": "sha256_hmac_signature",
  "timestamp": "2025-09-13T10:30:00Z"
}

// Response Format
{
  "status": "success",
  "message": "Evaluation initiated successfully",
  "experiment_id": "exp_20250913_001",
  "estimated_completion": "2025-09-13T11:00:00Z"
}
```

### Quality Assurance

#### Core Components Built
- `/lse/evaluation.py`: Complete evaluation module with all classes
- `/lse/commands/eval.py`: CLI command implementations for all evaluation operations  
- **Test Coverage**: Comprehensive test suite covering all evaluation workflows
- **Error Handling**: Graceful handling of API failures, invalid data, and network issues

#### Production Ready Features
✅ **Dataset Creation**: `lse eval create-dataset --traces traces.json --eval-type accuracy`  
✅ **LangSmith Upload**: `lse eval upload --dataset dataset.json --overwrite`  
✅ **External API Integration**: `lse eval run --dataset-name ds --experiment-prefix exp --eval-type accuracy`  
✅ **Format Flexibility**: Support for JSON, JSONL, and custom dataset formats  
✅ **Progress Tracking**: Rich progress bars and status indicators  
✅ **Error Recovery**: Comprehensive error handling and retry logic  

**Modified Files:**
- `/Users/calum/code/cg/langsmith-extractor/lse/cli.py`: Added eval command group registration
- `/Users/calum/code/cg/langsmith-extractor/lse/config.py`: Added EVAL_API_ENDPOINT configuration setting
- `/Users/calum/code/cg/langsmith-extractor/pyproject.toml`: Added langsmith and httpx dependencies
- `/Users/calum/code/cg/langsmith-extractor/uv.lock`: Updated dependency lock file

### Dependencies
- Historical trace data with both AI outputs and human feedback
- LangSmith account with dataset upload permissions
- External evaluation API endpoint and authentication credentials
- Phase 3 (Standardized reporting) for trace analysis capabilities

## Phase 7: Tracing capabilities 🔄 **PLANNED**

**Goal:** Advanced tracing analysis and visualization capabilities
**Success Criteria:** Comprehensive trace analysis with dependency mapping and performance insights

### Features
- [ ] **Trace visualization** - Visual representation of trace hierarchies and dependencies `M`
- [ ] **Performance analysis** - Detailed analysis of execution times and bottlenecks `M`
- [ ] **Dependency mapping** - Mapping of trace relationships and data flow `M`
- [ ] **Interactive exploration** - Web-based interface for trace exploration `M`
- [ ] **Export capabilities** - Export trace visualizations and analysis results `S`
- [ ] **Comparison tools** - Compare traces across different time periods or configurations `S`
- [ ] **Alerting system** - Automated alerts for performance degradation or anomalies `S`

### Technical Implementation
- **Visualization Engine**: D3.js or similar for interactive trace visualization
- **Web Interface**: Flask or FastAPI-based web application for interactive exploration
- **Analysis Engine**: Advanced algorithms for performance analysis and bottleneck detection
- **Export System**: PDF, PNG, and interactive HTML export capabilities

### Dependencies
- Phases 1-4 completed with comprehensive trace data collection
- Web development framework and visualization libraries
- User interface design and user experience requirements defined

---

## Usage Examples

### Complete Daily Workflow
```bash
# Extract traces for yesterday
lse archive fetch --project my-project --date $(date -d "yesterday" +%Y-%m-%d)

# Generate error analysis report
lse report zenrows-errors --project my-project --date $(date -d "yesterday" +%Y-%m-%d)

# Create evaluation dataset
lse eval create-dataset --traces traces.json --eval-type accuracy --name daily_eval_$(date +%Y%m%d)

# Upload and run evaluation
lse eval upload --dataset dataset.json
lse eval run --dataset-name daily_eval_$(date +%Y%m%d) --experiment-prefix daily --eval-type accuracy
```

### Multi-Project Analysis
```bash
# Generate comprehensive report across projects
lse report zenrows-errors --start-date 2025-09-01 --end-date 2025-09-13

# Archive multiple projects
for project in proj1 proj2 proj3; do
    lse archive --project $project --date 2025-09-13
done
```

### Automated Integration Example
```bash
#!/bin/bash
# Daily automation script
DATE=$(date -d "yesterday" +%Y-%m-%d)
PROJECT="production-project"

# Extract and archive
lse archive --project $PROJECT --date $DATE

# Generate and email report
lse report zenrows-errors --project $PROJECT --date $DATE --output daily_report.csv
mail -s "Daily Trace Report $DATE" stakeholders@company.com < daily_report.csv

# Create evaluation dataset if sufficient data
lse eval create-dataset --traces traces_${DATE}.json --eval-type accuracy --name eval_${DATE}
lse eval upload --dataset dataset_${DATE}.json
lse eval run --dataset-name eval_${DATE} --experiment-prefix daily_${DATE} --eval-type accuracy
```

### Dependencies
- Usage feedback from zenrows error reporting
- Additional stakeholder report requirements

## Phase 8: Database Infrastructure Setup ✅ COMPLETED

**Goal:** Establish Postgres database with JSONB document storage for LangSmith trace data
**Success Criteria:** Working Postgres instance with proper schema and application connectivity

### Problem Statement
Current file-based storage has limitations for querying and analyzing trace data. Need to migrate to a database that:
1. Supports complex queries across trace data
2. Enables date range operations for evaluation datasets
3. Provides better performance for reporting
4. Correctly models LangSmith's Run-based architecture

### LangSmith Data Model Clarification
**Corrected Understanding**:
- **Run**: Individual execution unit with unique run_id
- **Trace**: Collection of runs sharing the same trace_id
- **Root Run**: Top-level run where run_id = trace_id
- **Child Runs**: Runs with different run_ids but same trace_id

**Database Approach**:
- Store individual **Runs** (not aggregated traces)
- Reconstruct traces by grouping runs with same trace_id
- Enable trace-level analysis through SQL aggregation

### Features

- [ ] **Docker Postgres setup** - Dockerized Postgres instance for local development `M`
- [ ] **Database schema design** - JSONB-based schema supporting LangSmith trace model `M`
- [ ] **Python database connectivity** - SQLAlchemy/asyncpg integration with connection pooling `S`
- [ ] **Schema migration system** - Alembic for database schema management `S`
- [ ] **Database configuration** - Environment-based DB connection management `S`
- [ ] **Index optimization** - Indexes for date-based and project-based queries `S`
- [ ] **Connection testing** - Health checks and connectivity validation `S`

### Database Schema Design
```sql
-- Run-based storage (correctly models LangSmith's architecture)
CREATE TABLE runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(255) UNIQUE NOT NULL,
    trace_id VARCHAR(255) NOT NULL,
    project VARCHAR(255) NOT NULL,
    run_date DATE NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure consistency between table fields and JSONB data
    CONSTRAINT check_run_id_matches CHECK (data->>'run_id' = run_id),
    CONSTRAINT check_trace_id_matches CHECK (data->>'trace_id' = trace_id),
    CONSTRAINT check_project_matches CHECK (data->>'project' = project),
    CONSTRAINT check_date_matches CHECK ((data->>'run_date')::date = run_date)
);

-- Indexes optimized for run aggregation and trace reconstruction
CREATE INDEX idx_runs_project_date ON runs(project, run_date);
CREATE INDEX idx_runs_trace_id ON runs(trace_id);
CREATE INDEX idx_runs_run_date ON runs(run_date);
CREATE INDEX idx_runs_data_gin ON runs USING gin(data);
CREATE INDEX idx_runs_trace_aggregation ON runs(trace_id, project, run_date, run_id);
```

### Docker Configuration
- **Local Development**: Docker Compose with Postgres 16
- **Volume Management**: Persistent data storage
- **Environment Variables**: Database credentials and connection strings
- **Port Configuration**: Standard Postgres port mapping

### Dependencies
- Docker and Docker Compose installed
- Python database libraries (asyncpg, SQLAlchemy)
- Database migration tools (Alembic)

## Phase 9: Archive Tool Database Integration ✅ COMPLETED

**Goal:** Add run storage to database alongside existing Google Drive archiving workflow
**Success Criteria:** Archive commands store individual runs in Postgres with trace aggregation capabilities

### Problem Statement
Need to maintain existing Google Drive archiving while adding run-based database storage:
1. Local JSON files remain necessary for Google Drive uploads
2. Database stores individual runs (each JSON file = one run)
3. Traces reconstructed via SQL aggregation by trace_id
4. Data consistency between files and database maintained

### Features

- [x] **Archive to database command** - `lse archive to-db` for loading files to database `M` ✅
- [x] **Database storage layer** - DatabaseRunStorage class for JSONB operations `M` ✅
- [x] **Data consistency checks** - Validate file and database consistency `S` ✅
- [x] **Full sweep command** - `lse archive full-sweep` for complete workflow `M` ✅
- [x] **Batch insert optimization** - Efficient bulk data loading `S` ✅
- [x] **Duplicate handling** - Upsert logic for trace updates `S` ✅
- [x] **Progress tracking** - Progress bars for database operations `S` ✅

### New Command Interfaces
```bash
# Load existing files to database
lse archive to-db --date 2025-09-13 --project my-project

# Complete archival workflow (fetch → zip → upload → populate DB)
lse archive full-sweep --date 2025-09-13 --project my-project

# Verify consistency between files and database
lse archive verify --date 2025-09-13 --project my-project
```

### Workflow Integration
1. **Fetch**: `lse archive fetch` (unchanged) → Local JSON files
2. **Zip**: `lse archive zip` (unchanged) → Archive files
3. **Upload**: `lse archive upload` (unchanged) → Google Drive
4. **Populate**: `lse archive to-db` (new) → Postgres database
5. **Full Sweep**: `lse archive full-sweep` (new) → All steps combined

### Technical Implementation
- **TraceDatabase Class**: Async database operations with connection pooling
- **Batch Processing**: Chunked inserts for large datasets
- **Transaction Management**: Atomic operations with rollback capability
- **Error Recovery**: Graceful handling of database connectivity issues

### Completed Implementation

**Status**: Phase 9 is now COMPLETE! ✅

#### Core Components Built
- **LangSmithDataFetcher**: Unified API client + database storage operations
- **RunDataTransformer**: Convert LangSmith Run objects to database format with validation
- **DatabaseRunStorage**: CRUD operations with batch processing and upsert logic
- **Archive Command Extensions**: Added `to-db` and `full-sweep` subcommands to existing archive workflow

#### Production Ready Features

✅ **Archive to Database**: `lse archive to-db --project my-project --date 2024-01-15`  
✅ **Full Sweep Workflow**: `lse archive full-sweep --project my-project --date 2024-01-15`  
✅ **Batch Processing**: Efficient bulk inserts with transaction management  
✅ **Duplicate Handling**: Upsert logic prevents duplicate runs, handles updates gracefully  
✅ **Multiple JSON Formats**: Handles both wrapper format and direct Run object formats  
✅ **Progress Tracking**: Rich progress bars for database operations  
✅ **Error Recovery**: Robust error handling with detailed failure reporting  

#### Technical Implementation Highlights

**Database Integration**:
- **Individual Run Storage**: Each JSON file represents one run stored in database
- **Trace Reconstruction**: Traces assembled via SQL aggregation by trace_id
- **JSONB Performance**: Optimized database schema with proper indexing
- **Connection Pooling**: Async database operations with configurable connection pools

**Workflow Enhancement**:
- **Backward Compatibility**: All existing archive functionality preserved
- **Google Drive Integration**: No changes to existing zip/upload workflow
- **Command Interface**: Natural extension of existing `lse archive` commands
- **Data Consistency**: JSON files and database remain synchronized

**Rate Limiting Improvements**:
- **Hardcoded 1000ms Delays**: Eliminated manual tuning of delay parameters
- **Enhanced Retry Logic**: Increased from 3 to 5 attempts with exponential backoff
- **Comprehensive Child Fetching**: Always fetch complete trace hierarchies
- **Simplified User Experience**: Removed confusing `--include-children` flag

#### Quality Assurance
- **Enhanced Database Tests**: Comprehensive test coverage for all database operations
- **Integration Testing**: Full workflow testing from API to database storage
- **Real Data Validation**: Successfully tested with 1,734+ runs from production data
- **Error Handling**: Graceful handling of malformed JSON, network issues, and database errors

#### Files Created/Modified

**New Files:**
- `/Users/calum/code/cg/langsmith-extractor/lse/data_fetcher.py`: LangSmith API + database integration
- `/Users/calum/code/cg/langsmith-extractor/lse/data_storage.py`: Database storage layer with JSONB operations

**Modified Files:**
- `/Users/calum/code/cg/langsmith-extractor/lse/commands/archive.py`: Added `to-db` and `full-sweep` subcommands
- `/Users/calum/code/cg/langsmith-extractor/lse/exceptions.py`: Added database-specific exception types
- `/Users/calum/code/cg/langsmith-extractor/lse/retry.py`: Enhanced retry logic (3→5 attempts)
- `/Users/calum/code/cg/langsmith-extractor/tests/test_database.py`: Comprehensive database test coverage

### Dependencies
- Phase 8 (Database Infrastructure) completed ✅
- Existing archive functionality preserved ✅
- Google Drive integration unchanged ✅

## Phase 10: Evaluation Dataset Database Migration ✅ COMPLETED

**Goal:** Update evaluation to query runs and aggregate into traces from database
**Success Criteria:** Evaluation commands reconstruct traces from runs with date range support

### Problem Statement
Current evaluation dataset creation required:
1. Reading individual run files from local storage
2. Single-date operations only
3. Manual trace extraction step
4. File-based workflow dependencies

Completed improvements:
1. Database queries aggregate runs by trace_id to reconstruct traces
2. Date range support for dataset creation across multiple days
3. Eliminated separate extract-traces step
4. Maintained dataset format compatibility while improving performance

### Features

- [x] **Database query integration** - Updated TraceExtractor to query Postgres `M` ✅
- [x] **Date range support** - Support --start-date and --end-date parameters `M` ✅
- [x] **Direct dataset creation** - Query database directly without extract-traces step `M` ✅
- [x] **Query optimization** - Efficient database queries for trace filtering `S` ✅
- [x] **Backward compatibility** - Maintain existing dataset format and API `S` ✅
- [x] **Enhanced filtering** - Database-level filtering for evaluation criteria `S` ✅
- [x] **Performance improvements** - Faster dataset creation via database queries `S` ✅
- [x] **Feedback stats preservation** - Fixed missing feedback_stats in database storage `M` ✅
- [x] **Decimal serialization** - Handle Decimal cost fields in JSON serialization `S` ✅

### Updated Command Interfaces
```bash
# Create dataset directly from database (single date)
lse eval create-dataset --date 2025-09-13 --project my-project --eval-type accuracy

# Create dataset from date range
lse eval create-dataset --start-date 2025-09-01 --end-date 2025-09-13 --project my-project --eval-type accuracy

# Upload and run evaluation (unchanged)
lse eval upload --dataset dataset.json --name eval_dataset_2025_09
lse eval run --dataset-name eval_dataset_2025_09 --experiment-prefix exp_20250913 --eval-type accuracy
```

### Completed Implementation

**Status**: Phase 10 is now COMPLETE! ✅

#### Core Components Built
- **Database-based TraceExtractor**: Query runs and aggregate by trace_id to reconstruct complete traces
- **Enhanced DatasetBuilder**: Create evaluation datasets directly from database with date range support
- **Fixed RunDataTransformer**: Preserve feedback_stats and all LangSmith Run fields in database storage
- **DecimalJSONEncoder**: Handle Decimal serialization issues in cost fields

#### Production Ready Features

✅ **Database-based Dataset Creation**: `lse eval create-dataset --project my-project --date 2025-09-06 --eval-type token_name`  
✅ **Date Range Support**: `lse eval create-dataset --project my-project --start-date 2025-09-01 --end-date 2025-09-06 --eval-type token_name`  
✅ **Feedback Stats Preservation**: Fixed missing feedback_stats in database storage enabling proper evaluation  
✅ **Decimal Handling**: Resolved 100% of Decimal serialization errors during database storage  
✅ **Format Compatibility**: Handles both database format (direct) and file format (wrapped) seamlessly  
✅ **Eliminated extract-traces**: Direct database queries replace intermediate file extraction step  
✅ **Performance Optimization**: Database queries with proper indexing for trace aggregation  

#### Technical Implementation Highlights

**Database Query Architecture**:
- **Run Aggregation**: SQL queries group runs by trace_id to reconstruct complete traces
- **Date Range Queries**: Support single dates or date ranges with PostgreSQL date objects
- **Evaluation Filtering**: Database-level filtering for traces with AI output and human feedback
- **JSONB Operations**: Efficient JSONB queries for feedback_stats and outputs extraction

**Data Preservation Fixes**:
- **Complete Field Coverage**: Added missing LangSmith Run fields including feedback_stats, attachments, child_run_ids
- **Decimal Serialization**: Custom JSON encoder handles Decimal objects in cost fields
- **Format Compatibility**: Updated all evaluation methods to handle both database and file formats
- **100% Storage Success**: Eliminated all serialization errors during archive to-db operations

**Quality Assurance**:
- **Test Results Validation**: Successfully created 5 evaluation examples for test case (2025-09-06)
- **Data Integrity**: All 1460 runs stored successfully without errors
- **Backward Compatibility**: Existing dataset format and APIs preserved
- **Performance Verification**: Database queries significantly faster than file scanning

#### Files Created/Modified

**Enhanced Files:**
- `/Users/calum/code/cg/langsmith-extractor/lse/evaluation.py`: Added database query methods and format compatibility
- `/Users/calum/code/cg/langsmith-extractor/lse/data_storage.py`: Fixed RunDataTransformer and added DecimalJSONEncoder
- `/Users/calum/code/cg/langsmith-extractor/lse/commands/eval.py`: Updated to use database-based dataset creation

#### Migration Results
- **Extract-traces command removed**: Direct database queries replace file extraction workflow
- **Date range support added**: Create datasets spanning multiple days efficiently
- **Storage reliability**: 100% success rate for database operations (previously 70% due to Decimal errors)
- **Evaluation accuracy**: Proper feedback extraction enables accurate human/AI verdict comparison

### Dependencies
- Phase 9 (Archive Database Integration) completed ✅
- Database populated with historical trace data ✅
- LangSmith integration preserved ✅

## Phase 11: Reporting Database Migration ✅ COMPLETED

**Goal:** Switch reporting to aggregate runs into traces via database queries
**Success Criteria:** All report commands reconstruct traces from runs using SQL aggregation

### Problem Statement
Current reporting read from individual run JSON files which:
1. Required all run data to be available locally
2. Limited to single-date operations for some reports
3. Slower file scanning for large datasets
4. Could not leverage database aggregation optimizations

Completed migration goals:
1. All reports now aggregate runs by trace_id to reconstruct traces
2. Maintained existing report formats and output exactly
3. Preserved command interfaces and behavior
4. Enabled advanced SQL optimizations for better performance

### Features

- [x] **Update zenrows-errors report** - Database queries for error aggregation `M` ✅
- [x] **Update zenrows-detail report** - Database queries for detailed error analysis `M` ✅
- [x] **Query optimization** - Efficient aggregation queries with proper indexing `S` ✅
- [x] **Report caching** - Optional caching for frequently accessed reports `S` ✅
- [x] **Backward compatibility** - Maintain exact output format and behavior `S` ✅
- [x] **Performance monitoring** - Query performance tracking and optimization `S` ✅
- [x] **Error handling** - Graceful fallback for database connectivity issues `S` ✅

### Command Interface (Unchanged)
```bash
# Zenrows error reports (same interface, database backend)
lse report zenrows-errors --date 2025-09-13 --project my-project
lse report zenrows-detail --date 2025-09-13 --project my-project

# Output format unchanged
Date,Total Traces,Zenrows Errors,Error Rate
2025-09-13,220,10,4.5%
```

### Completed Implementation

**Status**: Phase 11 is now COMPLETE! ✅

#### Core Components Built
- **DatabaseTraceAnalyzer**: New database-based analyzer for trace reconstruction and error analysis
- **Database Query Engine**: SQL queries that aggregate runs by trace_id to reconstruct complete traces
- **Report Migration**: Both zenrows-errors and zenrows-detail commands now use database backend
- **Connection Management**: Robust async database connection handling with proper cleanup

#### Production Ready Features

✅ **Database-based zenrows-errors**: `lse report zenrows-errors --date 2025-09-06 --project my-project`  
✅ **Database-based zenrows-detail**: `lse report zenrows-detail --date 2025-09-06 --project my-project`  
✅ **Multi-project Aggregation**: Reports can aggregate across all projects for comprehensive analysis  
✅ **Identical Output Format**: Maintains exact CSV and text output formats for backward compatibility  
✅ **Performance Optimization**: Database queries significantly faster than file scanning  
✅ **Error Handling**: Graceful fallback and proper error reporting for database issues  
✅ **Connection Pooling**: Efficient database connection management with automatic cleanup  

#### Technical Implementation Highlights

**Database Query Architecture**:
- **Run Aggregation**: SQL queries group runs by trace_id using `array_agg(data ORDER BY created_at)`
- **Trace Reconstruction**: Intelligent merging of runs into complete trace hierarchies
- **Error Detection**: Reuse of existing `extract_zenrows_errors()` function for consistency
- **Multi-project Support**: Dynamic project discovery and aggregation across databases

**Performance Optimizations**:
- **Indexed Queries**: Leverages existing indexes on project, run_date, and trace_id
- **Streaming Processing**: Processes traces one at a time to manage memory efficiently
- **Connection Pooling**: Reuses database connections across report operations
- **Query Optimization**: Efficient GROUP BY operations with minimal data transfer

**Backward Compatibility**:
- **Identical Command Interface**: No changes to CLI parameters or options
- **Same Output Format**: CSV and text outputs match file-based implementation exactly
- **Error Message Consistency**: Maintains same error handling and user experience
- **Format Reuse**: Leverages existing ReportFormatter for consistent output

#### Files Created/Modified

**Enhanced Files:**
- `/Users/calum/code/cg/langsmith-extractor/lse/analysis.py`: Added DatabaseTraceAnalyzer class with async query methods
- `/Users/calum/code/cg/langsmith-extractor/lse/commands/report.py`: Updated both report commands to use database backend

#### Migration Results
- **File Dependency Eliminated**: Reports no longer require local JSON files
- **Performance Improvement**: Database queries faster than recursive file scanning
- **Scalability Enhanced**: Can handle larger datasets more efficiently
- **Memory Efficiency**: Streaming processing prevents memory issues with large date ranges
- **Data Consistency**: Single source of truth from PostgreSQL database

### Dependencies
- Phase 9 (Archive Database Integration) completed ✅
- Database populated with comprehensive trace data ✅
- Existing report output formats preserved ✅

## Phase 12: Critical Feedback Data Loss Fix 🚨 **URGENT**

**Goal:** Ensure complete feedback data extraction including detailed rationale from LangSmith  
**Success Criteria:** All feedback data including detailed Value field rationale is captured and stored

### 🚨 Critical Problem Statement
**Data Loss Identified**: The current archive system is failing to capture crucial feedback data from LangSmith:

1. **Missing Detailed Rationale**: The LangSmith UI shows detailed feedback in the "Value" field containing JSON with rationale data and decision factors
2. **Empty Values Field**: Current database storage shows `"values": {}` instead of the rich feedback data
3. **Business Impact**: This detailed rationale is "a key part of why we are fetching from LangSmith in the first place"
4. **Planned Resolution**: Full re-fetch of last 2 weeks of data (LangSmith retention period) once fix is implemented

### Technical Analysis
**Current State**:
- File storage shows: `"values": {}` (empty)
- Database storage shows: `"values": {}` (empty) 
- LangSmith UI shows: Detailed JSON rationale in Value field

**Root Cause Hypothesis**:
- Using `client.list_runs()` may not fetch complete feedback data
- Need to use `client.list_feedback(run_ids=[...])` for detailed feedback information
- Current `feedback_stats` aggregation may be missing the individual feedback records

### Proposed Solution Architecture

#### 1. Enhanced Feedback Extraction
```python
async def fetch_complete_feedback_data(self, run_id: str) -> Dict[str, Any]:
    """Fetch complete feedback including detailed rationale."""
    # Get run data (current method)
    run = await self.client.get_run(run_id)
    
    # Get detailed feedback data (NEW) - maintain 1000ms rate limiting
    feedback_list = list(self.client.list_feedback(run_ids=[run_id]))
    
    # Store feedback records in their native format
    enhanced_run = self._store_native_feedback(run, feedback_list)
    return enhanced_run
```

#### 2. Native Feedback Data Storage  
```python
def _store_native_feedback(self, run: Run, feedback_list: List[Feedback]) -> Dict:
    """Store feedback records in their native API format."""
    run_data = run.dict()
    
    # Store individual feedback records exactly as returned by API
    if feedback_list:
        run_data['feedback_records'] = [feedback.dict() for feedback in feedback_list]
    
    return run_data
```

#### 3. Backward Compatibility
- Preserve existing `feedback_stats` structure completely unchanged
- Store additional feedback records in new `feedback_records` field 
- Ensure evaluation/reporting systems continue working with existing data format
- Support loading and processing of both old and new data formats

### Implementation Plan

#### Phase 12.1: Investigation and Analysis `M`
- [ ] **API Investigation** - Analyze LangSmith SDK methods for complete feedback extraction
- [ ] **Data Structure Analysis** - Understand native feedback record format from API
- [ ] **Integration Planning** - Plan minimal changes to existing fetch logic

#### Phase 12.2: Enhanced Extraction Logic `M`  
- [ ] **Feedback API Integration** - Add `client.list_feedback()` calls to existing fetch workflow
- [ ] **Native Storage** - Store feedback records exactly as returned by API  
- [ ] **Rate Limiting** - Extend existing 1000ms delays to new API calls
- [ ] **Backward Compatibility** - Ensure existing data formats continue to work

#### Phase 12.3: Testing and Validation `M`
- [ ] **Data Validation** - Verify complete feedback data extraction and storage
- [ ] **Compatibility Testing** - Test with both old and new data formats
- [ ] **Integration Testing** - Ensure existing evaluation/reporting systems unaffected

### Technical Specifications

#### No Command Interface Changes
Existing commands remain unchanged:
```bash
# Standard archive workflow (enhanced internally)
lse archive fetch --project my-project --date 2025-09-06
lse archive full-sweep --project my-project --date 2025-09-06
```

#### Enhanced Database Schema  
```sql
-- Existing structure preserved completely
{
  "feedback_stats": {
    "final_verdict": {
      "n": 1,
      "avg": 1.0, 
      "values": {},  -- Existing (may remain empty from aggregation)
      "comments": ["Human verdict: PASS"],
      "sources": ["{\"type\":\"api\",\"metadata\":{}}"]
    }
  },
  
  -- NEW: Native feedback records as returned by API
  "feedback_records": [
    {
      "id": "feedback-uuid",
      "run_id": "run-uuid",
      "key": "final_verdict", 
      "score": 1.0,
      "value": {  -- Complete rationale data in native format
        "verdict": "PASS",
        "rationale": {
          "criteria_a": false,
          "criteria_b": false,
          "criteria_c": true,
          "decision_factors": ["factor1", "factor2"]
        }
      },
      "comment": "Human verdict: PASS",
      "created_at": "2025-09-06T00:22:14Z",
      "metadata": {}
    }
  ]
}
```

### Quality Gates

#### Phase 12.1 Completion Criteria
- [ ] Complete understanding of LangSmith feedback API capabilities  
- [ ] Documented mapping of missing vs available feedback data
- [ ] Quantified impact on historical data (number of affected traces)
- [ ] Database schema requirements defined

#### Phase 12.2 Completion Criteria  
- [ ] Enhanced extraction logic captures complete feedback data
- [ ] Performance benchmarks meet rate limiting requirements
- [ ] Error handling covers all feedback API failure scenarios
- [ ] Integration tests validate enhanced data extraction

#### Phase 12.3 Completion Criteria
- [ ] Database stores complete feedback data including rationale
- [ ] Migration script successfully backfills historical data
- [ ] Data validation confirms no information loss
- [ ] Test coverage exceeds 95% for feedback extraction logic

#### Phase 12.4 Completion Criteria
- [ ] Evaluation system uses enhanced feedback data for dataset creation
- [ ] Reports include access to detailed feedback rationale when relevant
- [ ] CLI tools provide feedback data verification capabilities  
- [ ] Documentation enables users to access and understand feedback structure

### Risk Assessment

#### Critical Risks
- **Historical Data Loss**: May be impossible to recover missing feedback for old traces
- **API Rate Limits**: Additional feedback API calls may hit rate limits
- **Performance Impact**: Enhanced extraction may significantly slow archive operations
- **Data Consistency**: Mixing old incomplete data with new complete data

#### Mitigation Strategies  
- **Incremental Backfill**: Process historical data in small batches to avoid rate limits
- **Graceful Degradation**: Continue operations even if feedback API calls fail
- **Data Versioning**: Track which traces have complete vs incomplete feedback data
- **Performance Monitoring**: Monitor and optimize enhanced extraction performance

### Dependencies
- Phase 9 (Archive Database Integration) completed ✅  
- Phase 10 (Evaluation Database Migration) completed ✅
- Access to LangSmith feedback APIs ✅
- Database write access for schema enhancements
- Time allocation for historical data backfill operations

### Success Metrics
- **Data Completeness**: 100% of feedback rationale data captured in new extractions
- **Historical Recovery**: Maximum possible feedback data recovered from accessible traces  
- **Performance Impact**: Enhanced extraction completes within 2x of current timing
- **Evaluation Accuracy**: Dataset creation can access detailed feedback rationale
- **System Reliability**: Enhanced extraction maintains current error rates and reliability

## Phase 13: Dataset Format Fix 🚨 **URGENT**

**Goal:** Fix evaluation dataset generation to produce correct format matching expected structure  
**Success Criteria:** `eval create-dataset` outputs clean, properly formatted JSONL matching expected format with comprehensive test coverage

### 🚨 Critical Problem Statement
**Format Mismatch Identified**: The current evaluation dataset generation produces incorrect output format:

1. **Wrong Input Structure**: Currently outputs complex LangChain message objects instead of clean input fields
2. **Wrong Output Structure**: Currently outputs raw LangChain generation data instead of clean boolean results
3. **Business Impact**: Generated datasets cannot be used for evaluation workflows as they don't match expected format
4. **Test Coverage Gap**: No tests validating output format compliance

## Phase 14: Availability Evaluation Type 🔄 **PLANNED**

**Goal:** Add support for "availability" evaluation type to create datasets for URL availability checking  
**Success Criteria:** `lse eval create-dataset --eval-type availability` creates properly formatted datasets with website_url inputs and is_available outputs

### Problem Statement
Need to expand evaluation capabilities to support URL availability checking:

1. **New Evaluation Type**: Add "availability" as a supported eval_type alongside existing "token_name" and "website" types
2. **Simplified Dataset Creation**: Create entries for every trace over the date range (not just "high confidence" traces like token_name and website)
3. **URL Focus**: Extract website_url from trace inputs and availability status from outputs
4. **Business Value**: Enable automated evaluation of website availability across due diligence workflows

### Features

- [ ] **Availability eval_type support** - Add "availability" to supported eval_type options `M`
- [ ] **All-trace inclusion logic** - Create entries for every trace (no high-confidence filtering) `M`
- [ ] **URL extraction** - Extract website_url from /due-diligence API request parameters `M`
- [ ] **Availability output format** - Format outputs with is_available boolean and notes field `M`
- [ ] **Command interface integration** - Seamless integration with existing eval create-dataset command `S`
- [ ] **Validation and testing** - Comprehensive test coverage for new eval_type `S`
- [ ] **Documentation updates** - Update help text and examples `S`

### Expected Dataset Format

**Availability Evaluation Examples**:
```json
{
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

### Command Interface (Enhanced)

```bash
# Create availability evaluation dataset
lse eval create-dataset --project my-project --date 2025-01-15 --eval-type availability

# Date range support for availability
lse eval create-dataset --project my-project --start-date 2025-01-01 --end-date 2025-01-15 --eval-type availability

# Upload and run availability evaluation
lse eval upload --dataset availability_dataset.json --name availability_eval_2025_01
lse eval run --dataset-name availability_eval_2025_01 --experiment-prefix avail_check --eval-type availability
```

### Technical Implementation

#### Data Extraction Logic
- **Input Extraction**: Extract `website_url` parameter from `/due-diligence` API request data
- **Output Extraction**: Determine availability status from API response or error patterns
- **No High-Confidence Filtering**: Include all traces that contain website_url, regardless of confidence scores
- **Notes Generation**: Provide descriptive notes about availability status or failure reasons

#### Integration Points
- **Existing eval_type validation**: Update to include "availability" as valid option
- **Format method**: Add `_format_availability()` method alongside existing format methods
- **Database queries**: Reuse existing trace extraction with availability-specific filtering
- **Command help**: Update CLI help text to include availability in examples

### Quality Gates

#### Phase 14.1 Completion Criteria
- [ ] "availability" eval_type accepted by CLI validation
- [ ] All traces with website_url parameter included in dataset creation
- [ ] Basic availability status extraction working
- [ ] Format validation tests pass for availability datasets

#### Phase 14.2 Completion Criteria
- [ ] Complete availability dataset format matches specification exactly
- [ ] Notes field provides meaningful availability context
- [ ] Integration with existing upload and run commands working
- [ ] Test coverage exceeds 95% for availability-specific code

#### Phase 14.3 Completion Criteria
- [ ] Documentation updated with availability examples
- [ ] Help text includes availability in eval_type options
- [ ] End-to-end workflow validated from dataset creation to external API
- [ ] Performance maintains current standards

### Dependencies
- Phase 10 (Evaluation Database Migration) completed ✅
- Phase 13 (Dataset Format Fix) completion recommended for consistency
- Database populated with traces containing website_url parameters
- External evaluation API supports availability eval_type

### Risk Assessment

#### Technical Risks
- **Data Structure Variance**: website_url may be nested differently across trace types
- **Availability Detection**: Complex logic needed to determine availability from various response patterns
- **Performance Impact**: Processing all traces (no filtering) may increase dataset creation time

#### Mitigation Strategies
- **Flexible Extraction**: Implement robust website_url extraction from multiple potential locations
- **Pattern Recognition**: Define clear availability detection rules based on response codes and error patterns
- **Batching**: Use existing database batching for efficient processing of larger trace volumes

### Current vs Expected Format Analysis

#### Current (Incorrect) Format
```json
{
  "inputs": {
    "messages": [
      {
        "id": ["langchain", "schema", "messages", "SystemMessage"],
        "type": "constructor", 
        "kwargs": {"content": "system prompt..."}
      }
    ]
  },
  "outputs": {
    "run": {...},
    "type": "LLMResult",
    "llm_output": {...},
    "generations": [...],
    "final_decision": "PASS"
  }
}
```

#### Expected (Correct) Format  
```json
{
  "inputs": {
    "name": "Goku Super Saiyan",
    "symbol": "Goku", 
    "description": "A meme token inspired by..."
  },
  "outputs": {
    "is_meme": true,
    "is_explicit": false,
    "has_conflict": true
  }
}
```

### Technical Root Cause Analysis

1. **Data extraction methods** in `/lse/evaluation.py` lines 806-869 are extracting raw trace data instead of processed inputs/outputs
2. **Format transformation methods** `_format_token_name()` and `_format_website()` need to extract from the actual nested structure correctly
3. **Test coverage gap** - no tests validating final JSONL output format compliance

### Implementation Plan

#### Phase 13.1: Fix Input Data Extraction `M`
- [ ] **Update `_extract_inputs()` method** - Extract clean fields from `input_data` nested structure
- [ ] **Token name inputs** - Return only name, symbol, description for token_name eval type
- [ ] **Website inputs** - Return name, symbol, network, description, website_url, social_profiles, contract_address for website eval type
- [ ] **Remove LangChain artifacts** - Eliminate messages, kwargs, and other framework-specific data

#### Phase 13.2: Fix Output Data Extraction `M`
- [ ] **Update `_extract_outputs()` method** - Extract actual evaluation results from nested output structure  
- [ ] **Boolean field extraction** - Extract is_meme, is_explicit, has_conflict/has_trademark_conflict as clean booleans
- [ ] **Nested result handling** - Navigate through name_analysis, website_analysis structures correctly
- [ ] **Remove LangChain artifacts** - Eliminate run, llm_output, generations, and other framework data

#### Phase 13.3: Update Format Methods `M`
- [ ] **Update `_format_token_name()` method** - Work with clean extracted data
- [ ] **Update `_format_website()` method** - Work with clean extracted data  
- [ ] **Remove redundant processing** - Since extraction is now clean

#### Phase 13.4: Comprehensive Test Coverage `M`
- [ ] **Format validation tests** - Tests that validate exact output format compliance
- [ ] **Field presence tests** - Verify all expected fields are present and correctly typed
- [ ] **Boolean conversion tests** - Ensure proper boolean extraction from nested structures
- [ ] **Integration tests** - End-to-end tests of create-dataset command output format

### Technical Specifications

#### Command Interface (Unchanged)
```bash
# Standard dataset creation commands (enhanced output format)
lse eval create-dataset --project my-project --date 2025-01-15 --eval-type token_name
lse eval create-dataset --project my-project --date 2025-01-15 --eval-type website  
```

#### Expected Output Format Compliance

**Token Name Evaluation**:
```json
{
  "inputs": {
    "name": "Token Name",
    "symbol": "TOKEN", 
    "description": "Token description text"
  },
  "outputs": {
    "is_meme": false,
    "is_explicit": false,
    "has_conflict": true
  }
}
```

**Website Evaluation**:
```json
{
  "inputs": {
    "name": "Token Name",
    "symbol": "TOKEN",
    "network": "ethereum", 
    "description": "Token description",
    "website_url": "https://example.com",
    "social_profiles": [],
    "contract_address": "0x123..."
  },
  "outputs": {
    "is_meme": false,
    "is_explicit": false, 
    "is_available": true,
    "is_malicious": false,
    "has_trademark_conflict": false
  }
}
```

### Quality Gates

#### Phase 13.1 Completion Criteria
- [ ] Input extraction produces clean dictionaries with only expected fields
- [ ] No LangChain message objects or framework artifacts in inputs
- [ ] Token name and website eval types produce correct input field sets
- [ ] Input extraction tests achieve 100% coverage

#### Phase 13.2 Completion Criteria  
- [ ] Output extraction produces clean boolean dictionaries matching expected format
- [ ] No raw LangChain outputs or nested generation data in results
- [ ] Boolean fields correctly extracted from nested analysis structures
- [ ] Output extraction tests achieve 100% coverage

#### Phase 13.3 Completion Criteria
- [ ] Format methods work with clean extracted data
- [ ] No redundant processing of already-clean data
- [ ] Format method tests achieve 100% coverage

#### Phase 13.4 Completion Criteria
- [ ] End-to-end tests validate complete JSONL output format
- [ ] Format compliance tests catch any deviation from expected structure  
- [ ] Test coverage exceeds 95% for all dataset generation code paths
- [ ] Generated datasets pass format validation against expected examples

### File Modifications Required

#### Core Implementation Files
- `/lse/evaluation.py` lines 806-869: Fix `_extract_inputs()` and `_extract_outputs()` methods
- `/lse/evaluation.py` lines 897-1071: Update `_format_token_name()` and `_format_website()` methods

#### Test Files  
- `/tests/test_eval_command.py`: Add comprehensive format validation tests
- New file `/tests/test_dataset_format.py`: Dedicated format compliance test suite
- `/tests/fixtures/`: Add expected format examples for test validation

### Risk Assessment

#### Critical Risks
- **Breaking Changes**: Format changes might affect downstream evaluation workflows
- **Data Structure Complexity**: Nested LangChain data extraction is complex and error-prone  
- **Test Coverage Gaps**: Insufficient testing could allow format regressions
- **Backward Compatibility**: New format might not work with existing evaluation systems

#### Mitigation Strategies
- **Gradual Rollout**: Test format changes with small datasets first
- **Format Validation**: Implement strict format validation before dataset output
- **Comprehensive Testing**: Achieve >95% test coverage with format compliance tests
- **Documentation**: Clear examples of expected vs current format for troubleshooting

### Dependencies
- Phase 10 (Evaluation Database Migration) completed ✅
- Database populated with evaluation-ready trace data ✅  
- Access to expected format examples for validation ✅
- Test framework setup for format validation testing

### Success Metrics
- **Format Compliance**: 100% of generated datasets match expected JSONL format
- **Field Accuracy**: All input/output fields correctly extracted and typed
- **Test Coverage**: >95% coverage with dedicated format validation tests  
- **Performance**: Dataset generation maintains current performance levels
- **Compatibility**: Generated datasets work correctly with existing LangSmith upload workflow

## Phase 15: Availability Dataset Root Run Priority Bug 🚨 **URGENT**

**Goal:** Fix availability dataset creation to prioritize root run data over child run data  
**Success Criteria:** Availability datasets accurately reflect root run's `is_available` status without contamination from incomplete child runs

### 🚨 Critical Problem Statement
**Data Accuracy Issue Identified**: The availability dataset creation produces incorrect availability status due to child run contamination:

1. **Root Run Data Ignored**: Root runs (where `trace_id == run_id`) contain authoritative availability status
2. **Child Run Contamination**: Child runs with incomplete or missing `is_available` data override correct root run values
3. **Data Aggregation Flaw**: `_deep_merge_dict()` allows later child runs to overwrite correct root run data
4. **Business Impact**: Datasets contain incorrect availability status, making them unreliable for evaluation workflows
5. **Scope**: Affects all availability datasets created since Phase 14 implementation

### Problem Evidence

**Database Evidence**: 
- Root run (`49751c71-4b79-469e-90cb-b83241e3afa1`): `is_available: true` ✅
- Child runs: Some have `is_available: null/undefined` ❌
- Generated dataset: `is_available: false` ❌ **WRONG**

**Expected vs Actual**:
```json
// Expected (from root run)
{"inputs": {"website_url": "https://x.com/FooExample"}, "outputs": {"is_available": true}}

// Actual (contaminated by child runs)  
{"inputs": {"website_url": "https://x.com/FooExample"}, "outputs": {"is_available": false}}
```

### Solution Design

#### Core Fix: Root Run Prioritization
**Priority Order for Data Extraction**:
1. **Root Run First**: Extract data from run where `trace_id == run_id`
2. **Child Run Fallback**: Only use child runs if root run lacks specific fields
3. **Never Override**: Child runs cannot override root run's authoritative data

#### Implementation Strategy

**Phase 15.1: Root Run Identification** `M`
- Modify `_build_example_from_runs()` to identify root run (`trace_id == run_id`)
- Extract root run data with highest priority
- Create separate extraction paths for root vs child runs

**Phase 15.2: Hierarchical Data Extraction** `M`  
- Update `_extract_outputs()` to prioritize root run availability data
- Implement fallback logic that only uses child runs for missing fields
- Ensure `is_available` status always comes from root run when available

**Phase 15.3: Deep Merge Logic Fix** `M`
- Modify data aggregation to prevent child run override of root run data
- Implement priority-based merging instead of sequential overwriting
- Add validation to ensure critical fields maintain root run values

**Phase 15.4: Availability-Specific Logic** `M`
- Update `_extract_availability_notes()` to use root run data for availability inference
- Ensure availability status determination follows root run → child run priority
- Add logging to track which run data is being used for availability decisions

### Technical Implementation

#### File Modifications Required

**Core Implementation**:
```python
# /lse/evaluation.py - _build_example_from_runs() method
def _build_example_from_runs(self, trace_metadata, run_data_list, eval_type=None):
    # 1. Identify root run (where trace_id == run_id)
    root_run = None
    child_runs = []
    
    for run_data in run_data_list:
        if run_data.get('trace_id') == run_data.get('run_id'):
            root_run = run_data
        else:
            child_runs.append(run_data)
    
    # 2. Extract data with root run priority
    if eval_type == "availability":
        # Use root-run-priority extraction for availability
        all_inputs, all_outputs, all_reference = self._extract_with_priority(
            root_run, child_runs, eval_type
        )
    else:
        # Use existing logic for other eval types
        # ... existing code ...
```

#### Root Run Priority Extraction Logic
```python
def _extract_with_priority(self, root_run, child_runs, eval_type):
    """Extract data with root run taking priority over child runs."""
    
    # Start with root run data
    primary_inputs = self._extract_inputs(root_run) if root_run else {}
    primary_outputs = self._extract_outputs(root_run) if root_run else {}
    primary_reference = self._extract_reference(root_run) if root_run else {}
    
    # Fill gaps with child run data (but never override root run critical fields)
    for child_run in child_runs:
        child_inputs = self._extract_inputs(child_run)
        child_outputs = self._extract_outputs(child_run)
        child_reference = self._extract_reference(child_run)
        
        # Merge inputs (child can fill missing fields)
        self._merge_with_priority(primary_inputs, child_inputs, priority_fields=[])
        
        # Merge outputs (root run availability data has priority)
        priority_fields = ["is_available", "notes"] if eval_type == "availability" else []
        self._merge_with_priority(primary_outputs, child_outputs, priority_fields)
        
        # Merge reference (child can fill missing fields)
        self._merge_with_priority(primary_reference, child_reference, priority_fields=[])
    
    return primary_inputs, primary_outputs, primary_reference
```

### Quality Gates

#### Phase 15.1 Completion Criteria
- [ ] Root run identification works correctly for all traces
- [ ] Root run vs child run separation logic implemented and tested
- [ ] Database queries correctly identify trace hierarchies

#### Phase 15.2 Completion Criteria
- [ ] Root run data extraction prioritizes authoritative availability status
- [ ] Child run fallback logic works for missing fields only
- [ ] Availability status never overridden by incomplete child run data

#### Phase 15.3 Completion Criteria  
- [ ] Data merging respects root run priority for critical fields
- [ ] Child runs can only supplement, not override, root run data
- [ ] Availability datasets show correct root run `is_available` status

#### Phase 15.4 Completion Criteria
- [ ] All availability-specific logic uses root run priority
- [ ] Notes generation reflects root run availability status
- [ ] End-to-end testing validates fix with problematic trace examples

### Test Cases

#### Critical Test Case (Foo Example)
```python
def test_foo_availability_fix():
    """Test that Foo trace shows correct availability from root run."""
    trace_id = "49751c71-4b79-469e-90cb-b83241e3afa1"
    
    # This should return is_available: true (from root run)
    # NOT is_available: false (from child run contamination)
    dataset = create_dataset_for_trace(trace_id, eval_type="availability")
    
    foo_example = find_example_by_url(dataset, "https://x.com/FooExample")
    assert foo_example["outputs"]["is_available"] == True
```

#### Regression Tests
- [ ] Test traces with complete root run data
- [ ] Test traces with incomplete child run data
- [ ] Test traces with conflicting availability status between runs
- [ ] Test traces with missing root run data (fallback scenarios)

### Risk Assessment

#### Critical Risks
- **Data Integrity**: Fix must not corrupt non-availability eval types
- **Performance Impact**: Root run identification might slow dataset creation
- **Edge Cases**: Complex trace hierarchies might have unexpected structures
- **Regression**: Changes could affect token_name and website eval types

#### Mitigation Strategies
- **Selective Application**: Apply root run priority only to availability eval_type
- **Comprehensive Testing**: Test all eval_types to prevent regressions
- **Performance Monitoring**: Benchmark dataset creation times before/after fix
- **Gradual Rollout**: Test fix on small datasets before full deployment

### Success Metrics
- **Data Accuracy**: 100% of availability datasets reflect correct root run status
- **No Regressions**: Other eval_types maintain current functionality
- **Test Coverage**: >95% coverage for root run priority logic
- **Performance**: Dataset creation time impact <10%

### Dependencies
- Phase 14 (Availability Evaluation Type) completed ✅
- Access to problematic trace examples for testing ✅
- Database with trace hierarchy data available ✅

## Phase 16: Availability Dataset Curation (Best 100) 🎯 **NEXT**

**Goal:** Implement intelligent dataset curation for availability evaluation with --best-100 parameter  
**Success Criteria:** Create optimally balanced 100-example availability datasets with comprehensive negative case coverage and representative positive examples

### Feature Overview
Add `--best-100` parameter to `lse eval create-dataset --eval-type availability` command to generate curated, high-quality datasets optimized for availability evaluation testing.

**⚠️ Important Constraint**: The `--best-100` parameter is **ONLY supported for `--eval-type availability`**. It will not work with `token_name` or `website` eval types and will show an error if attempted.

### Technical Requirements

#### Phase 16.1: Dataset Curation Framework `M`
**Objective**: Implement core dataset curation logic with configurable size limits

**Key Features:**
- Add `--best-100` CLI parameter to availability dataset creation
- Implement intelligent example selection algorithm
- Ensure comprehensive negative case coverage
- Optimize positive case representation with domain diversity

**Implementation Details:**
```python
def create_curated_dataset(self, traces: List[TraceMetadata], target_size: int = 100) -> EvaluationDataset:
    """Create curated dataset with optimal example distribution."""
    negative_examples = self._extract_negative_examples(traces)
    positive_examples = self._select_representative_positive_examples(
        traces, remaining_slots=target_size - len(negative_examples)
    )
    return self._build_curated_dataset(negative_examples + positive_examples)
```

#### Phase 16.2: Negative Case Prioritization `M`
**Objective**: Ensure all false availability cases are captured with deduplication

**Requirements:**
- **Complete Coverage**: Include ALL traces with `is_available: false`
- **URL Uniqueness**: Deduplicate by website_url for negative cases
- **Priority Ordering**: Most recent examples preferred when deduplicating
- **Validation**: Ensure no false negatives are missed

**Algorithm Design:**
1. Extract all examples with `is_available: false` from date range
2. Deduplicate by website_url (keeping most recent)
3. Validate negative examples meet quality criteria
4. Add all unique negative examples to curated dataset

#### Phase 16.3: Positive Case Optimization `M` 
**Objective**: Select representative positive examples with domain diversity

**Strategy:**
- **Domain Diversity**: Prefer unique domains/subdomains for variety
- **URL Uniqueness**: No duplicate website_urls across entire dataset
- **Quality Scoring**: Prioritize examples with comprehensive data
- **Balanced Representation**: Cover different types of positive availability

**Selection Algorithm:**
1. Group positive examples by domain
2. Select best example from each domain (quality scoring)
3. Fill remaining slots with high-quality examples from any domain
4. Ensure final dataset reaches target size (100 examples)

#### Phase 16.4: Quality Validation `M`
**Objective**: Validate curated dataset meets quality and balance requirements

**Validation Criteria:**
- **Size Compliance**: Exactly 100 examples (or justify if fewer)
- **Negative Coverage**: All available false cases included
- **URL Uniqueness**: No duplicate website_urls across dataset
- **Domain Diversity**: Reasonable domain distribution for positive cases
- **Data Completeness**: All examples have required fields (website_url, is_available, notes)

### CLI Integration

#### New Parameter
```bash
# ✅ VALID: --best-100 with availability eval_type
lse eval create-dataset --project my-project --eval-type availability --date 2025-09-10 --best-100 --output curated_100.jsonl --name curated_availability

# ❌ INVALID: --best-100 with other eval_types (will show error)
lse eval create-dataset --project my-project --eval-type token_name --date 2025-09-10 --best-100 --output error.jsonl --name error
lse eval create-dataset --project my-project --eval-type website --date 2025-09-10 --best-100 --output error.jsonl --name error
```

#### Behavior Changes
- **Default Mode**: Without `--best-100`, maintain existing behavior (all examples)
- **Curated Mode**: With `--best-100`, enable intelligent curation to ~100 examples
- **Validation**: Warn if fewer than 100 examples available from date range
- **Reporting**: Show curation statistics (negative count, positive count, domains covered)

### Expected Output Format

#### Example Output Statistics
```
✓ Created curated dataset 'curated_availability' with 97 examples
  - Negative examples (is_available: false): 12 unique URLs
  - Positive examples (is_available: true): 85 examples across 67 domains  
  - Total examples: 97 (limited by available data)
  - Saved to: curated_100.jsonl
```

#### Dataset Quality Metrics
- **Negative Coverage**: 100% of false availability cases included
- **URL Uniqueness**: 0 duplicate URLs in dataset
- **Domain Diversity**: 60+ unique domains represented
- **Representative Distribution**: Balanced mix of website types and availability patterns

### Implementation Plan

#### Phase 16.1: Core Curation Framework `M`
**Deliverables:**
- [ ] Add `--best-100` CLI parameter with typer integration
- [ ] Implement `create_curated_dataset()` method in DatasetBuilder
- [ ] Add curation logic to `create_dataset_from_db()` workflow
- [ ] Create base curation infrastructure and interfaces

**Acceptance Criteria:**
- CLI parameter parsed and passed to dataset creation logic
- Curation framework integrated with existing availability dataset creation
- Code structure supports configurable target sizes (not hardcoded to 100)

#### Phase 16.2: Negative Case Collection `M`
**Deliverables:**
- [ ] Implement `_extract_negative_examples()` with deduplication
- [ ] Add URL uniqueness validation for negative cases
- [ ] Create comprehensive negative case coverage logic
- [ ] Add logging for negative case statistics

**Acceptance Criteria:**
- All `is_available: false` examples captured from date range
- URL deduplication working correctly (most recent preferred)
- No false negative examples missed or excluded

#### Phase 16.3: Positive Case Selection `M`
**Deliverables:**
- [ ] Implement `_select_representative_positive_examples()` method
- [ ] Add domain diversity optimization algorithm
- [ ] Create quality scoring system for positive examples
- [ ] Implement slot-filling logic for remaining capacity

**Acceptance Criteria:**
- Domain diversity maximized for positive examples
- Quality scoring prioritizes examples with complete data
- Target dataset size reached when sufficient data available

#### Phase 16.4: Quality Assurance `M`
**Deliverables:**
- [ ] Add dataset validation for size, uniqueness, and completeness
- [ ] Implement curation statistics reporting
- [ ] Create comprehensive test suite for all curation logic
- [ ] Add edge case handling for insufficient data scenarios

**Acceptance Criteria:**
- Dataset validation catches quality issues before output
- Statistics provide clear insight into curation results
- Edge cases handled gracefully (warn but don't fail)

### Testing Strategy

#### Unit Tests
- **Negative Case Extraction**: Test with various false availability scenarios
- **Deduplication Logic**: Verify URL uniqueness and recency preference
- **Positive Case Selection**: Test domain diversity and quality scoring
- **Dataset Validation**: Test size limits, uniqueness, and completeness

#### Integration Tests  
- **End-to-End Curation**: Full workflow from database to curated JSONL output
- **CLI Integration**: Test `--best-100` parameter with various date ranges
- **Quality Validation**: Verify curated datasets meet all quality criteria
- **Statistics Reporting**: Test curation statistics accuracy

#### Edge Case Tests
- **Insufficient Data**: Test behavior when <100 examples available
- **All Positive/Negative**: Test extreme distributions
- **Duplicate URLs**: Test deduplication across positive and negative cases
- **Domain Concentration**: Test when few domains dominate the data

### Success Metrics

#### Data Quality Metrics
- **Negative Coverage**: 100% of false availability cases included in curated datasets
- **URL Uniqueness**: 0% duplicate URLs across all curated datasets  
- **Domain Diversity**: >80% unique domains for positive cases when sufficient data available
- **Dataset Size**: Target size achieved or justified when not possible

#### Performance Metrics
- **Curation Speed**: Dataset curation adds <10% to creation time
- **Memory Efficiency**: Curation logic handles large date ranges without memory issues
- **Quality Validation**: Validation catches 100% of data quality issues

#### User Experience Metrics
- **Clear Statistics**: Users understand curation results from output statistics
- **Predictable Behavior**: Curation results consistent across multiple runs
- **Graceful Degradation**: Clear warnings when target size not achievable

### Dependencies

#### Required Completions
- Phase 15 (Availability Dataset Root Run Priority Bug) ✅ **COMPLETED**
- Existing availability dataset creation functionality ✅ **AVAILABLE**
- Database access with sufficient availability data ✅ **AVAILABLE**

#### Optional Enhancements  
- Performance monitoring for curation process efficiency
- Advanced quality scoring algorithms for positive example selection
- Configurable curation parameters (not just --best-100)

## Phase 17: Is_Available Report Feature 🔄 **PLANNED**

**Goal:** Add `is_available` report type to analyze website availability failures across traces  
**Success Criteria:** New `lse report is_available` command provides comprehensive analysis of website availability issues with date range support

### Feature Overview
Add a new report type called `is_available` that analyzes traces to identify when website availability checks failed. This report will complement the existing zenrows error analysis by focusing specifically on the `is_available` field from trace outputs.

### Problem Statement
Current reporting focuses on zenrows scraper errors, but there's a need for dedicated analysis of website availability failures:

1. **Availability-Specific Analysis**: Need reports showing when `is_available` was false vs general scraper errors
2. **Business Visibility**: Stakeholders need clear metrics on website accessibility issues  
3. **Trend Analysis**: Understanding patterns in website availability across different time periods
4. **Complement Evaluation**: Report data that aligns with availability evaluation dataset insights

### Technical Requirements

#### Data Source
The report will extract `is_available` values from the database field:
```sql
-- Extract from runs table 
data->'outputs'->'website_analysis'->'is_available'
```

#### Report Logic
- **Traces**: Analyze root runs (where `trace_id = run_id`) 
- **Availability Status**: Extract boolean `is_available` from website_analysis outputs
- **Count Logic**: Count traces where `is_available = false`
- **Percentage Calculation**: `(is_available false count / total traces) * 100`

### Command Interface

#### New Report Command
```bash
# Single date availability report
lse report is_available --date 2025-09-01

# Date range availability report  
lse report is_available --start-date 2025-09-01 --end-date 2025-09-07

# Project-specific availability report
lse report is_available --date 2025-09-01 --project my-project

# All projects aggregated (default)
lse report is_available --date 2025-09-01
```

#### Expected Output Format
CSV format matching existing report patterns:
```csv
date,Trace count,is_available = false count,percentage
2025-09-01,40,3,7.5
2025-09-02,35,1,2.9
2025-09-03,42,5,11.9
```

### Technical Implementation

#### Phase 17.1: Database Query Logic `M`
**Objective**: Implement database queries to extract availability data from traces

**Key Features:**
- Query root runs from database (`trace_id = run_id`)
- Extract `is_available` from `data->'outputs'->'website_analysis'->'is_available'`
- Support single date and date range operations
- Handle project filtering (single project or all projects aggregated)

**Implementation Details:**
```python
async def analyze_is_available_from_db(
    self, 
    project_name: Optional[str] = None,
    report_date: Optional[datetime] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Dict[str, Any]]:
    """Analyze is_available field from database traces."""
    
    # Build date filter
    date_filter = self._build_date_filter(report_date, start_date, end_date)
    
    # Query root runs with availability data
    query = """
    SELECT 
        run_date::text as date,
        COUNT(*) as total_traces,
        COUNT(*) FILTER (
            WHERE (data->'outputs'->'website_analysis'->>'is_available')::boolean = false
        ) as false_count
    FROM runs 
    WHERE trace_id = run_id  -- Root runs only
        AND data->'outputs'->'website_analysis'->'is_available' IS NOT NULL
        {project_filter}
        {date_filter}
    GROUP BY run_date
    ORDER BY run_date
    """
```

#### Phase 17.2: Report Command Integration `M`
**Objective**: Add `is_available` subcommand to existing report CLI structure

**Key Features:**
- Integrate with existing `lse report` command structure
- Support date and date range parameters (matching zenrows-errors pattern)
- Add project filtering capabilities
- Maintain consistent CLI interface patterns

**Command Structure:**
```python
@report_app.command("is_available")
def is_available_command(
    date: Optional[str] = typer.Option(None, "--date", help="Single date (YYYY-MM-DD)"),
    start_date: Optional[str] = typer.Option(None, "--start-date", help="Start date for range"),
    end_date: Optional[str] = typer.Option(None, "--end-date", help="End date for range"),
    project: Optional[str] = typer.Option(None, "--project", help="Project to analyze"),
) -> None:
    """Generate availability failure reports showing is_available=false patterns."""
```

#### Phase 17.3: Output Formatting `M`
**Objective**: Format availability analysis results into CSV output

**Key Features:**
- CSV output matching existing report format standards
- Percentage calculations with proper rounding
- Date formatting consistency
- Handle edge cases (zero traces, missing data)

**Output Format:**
- Column headers: `date,Trace count,is_available = false count,percentage`
- Date format: `YYYY-MM-DD`
- Percentage format: `XX.X` (one decimal place)
- Handle zero division gracefully

#### Phase 17.4: Integration and Testing `M`
**Objective**: Ensure seamless integration with existing report infrastructure

**Key Features:**
- Reuse existing database connection and analyzer infrastructure
- Comprehensive test coverage for new report type
- Error handling and edge case coverage
- Performance testing with large datasets

### Expected Usage Examples

#### Daily Availability Analysis
```bash
# Check availability issues for a specific date
lse report is_available --date 2025-09-13 --project crypto-scanner

# Output:
# date,Trace count,is_available = false count,percentage
# 2025-09-13,150,8,5.3
```

#### Weekly Availability Trends
```bash  
# Analyze availability trends over a week
lse report is_available --start-date 2025-09-01 --end-date 2025-09-07

# Output:
# date,Trace count,is_available = false count,percentage
# 2025-09-01,40,3,7.5
# 2025-09-02,35,1,2.9
# 2025-09-03,42,5,11.9
# 2025-09-04,38,2,5.3
# 2025-09-05,45,4,8.9
# 2025-09-06,41,1,2.4
# 2025-09-07,39,3,7.7
```

#### Multi-Project Aggregation
```bash
# Aggregate availability across all projects
lse report is_available --date 2025-09-13

# Output combines all projects into single daily totals
```

### Quality Gates

#### Phase 17.1 Completion Criteria
- [ ] Database queries correctly extract `is_available` from website_analysis
- [ ] Root run filtering works correctly (`trace_id = run_id`)
- [ ] Date range filtering supports both single date and date ranges
- [ ] Project filtering works for single projects and aggregated results

#### Phase 17.2 Completion Criteria  
- [ ] `is_available` subcommand integrated into existing report CLI
- [ ] Parameter validation matches existing report command patterns
- [ ] Help text and documentation clear and consistent
- [ ] CLI interface follows established conventions

#### Phase 17.3 Completion Criteria
- [ ] CSV output format matches specification exactly
- [ ] Percentage calculations accurate and properly rounded
- [ ] Date formatting consistent with other reports
- [ ] Edge cases handled gracefully (zero traces, missing data)

#### Phase 17.4 Completion Criteria
- [ ] Integration tests validate end-to-end functionality
- [ ] Performance acceptable for large date ranges and datasets
- [ ] Error handling comprehensive and user-friendly
- [ ] Test coverage exceeds 95% for all new code

### Implementation Plan

#### Phase 17.1: Database Analysis Engine (Week 1)
**Deliverables:**
- [ ] Add `analyze_is_available_from_db()` method to DatabaseTraceAnalyzer
- [ ] Implement SQL queries for availability data extraction
- [ ] Add date range and project filtering logic
- [ ] Create data aggregation and percentage calculation logic

**Acceptance Criteria:**
- Database queries return accurate availability statistics
- Date filtering works for both single dates and ranges
- Project filtering supports single projects and aggregation
- Performance acceptable for typical date ranges

#### Phase 17.2: CLI Command Implementation (Week 1)
**Deliverables:**
- [ ] Add `is_available` subcommand to report command group
- [ ] Implement parameter validation and help text
- [ ] Integrate with existing database analyzer infrastructure
- [ ] Add async execution wrapper for database operations

**Acceptance Criteria:**
- CLI command accepts all specified parameters correctly
- Help text provides clear usage guidance
- Parameter validation prevents invalid input combinations
- Error messages provide actionable feedback

#### Phase 17.3: Output Formatting and Validation (Week 1) 
**Deliverables:**
- [ ] Implement CSV formatting for availability statistics
- [ ] Add percentage calculation with proper rounding
- [ ] Create output formatter integration
- [ ] Add edge case handling for empty results

**Acceptance Criteria:**
- CSV output matches expected format specification
- Percentage calculations mathematically correct
- Edge cases handled without crashes or errors
- Output formatting consistent with existing reports

#### Phase 17.4: Testing and Quality Assurance (Week 1)
**Deliverables:**
- [ ] Comprehensive unit tests for database queries
- [ ] Integration tests for CLI command functionality  
- [ ] Performance tests with realistic datasets
- [ ] Edge case and error handling tests

**Acceptance Criteria:**
- Test coverage exceeds 95% for all new functionality
- Performance tests validate acceptable response times
- Edge case tests cover all identified scenarios
- Integration tests validate end-to-end workflows

### Success Metrics

#### Data Accuracy Metrics
- **Query Correctness**: 100% accurate extraction of `is_available` values from database
- **Calculation Accuracy**: Mathematical accuracy in percentage calculations 
- **Date Handling**: Correct handling of UTC dates and timezone considerations
- **Project Filtering**: Accurate aggregation across single and multiple projects

#### Performance Metrics  
- **Query Performance**: Availability reports complete within 30 seconds for any single date
- **Range Performance**: Date range reports complete within 2 minutes for 7-day periods
- **Memory Efficiency**: Report generation uses reasonable memory for large datasets
- **Scalability**: Performance degrades gracefully with increasing data volumes

#### User Experience Metrics
- **Interface Consistency**: CLI interface matches patterns from existing report commands
- **Error Handling**: Clear error messages for all failure scenarios
- **Documentation Quality**: Help text provides sufficient guidance for users
- **Output Clarity**: CSV format enables easy analysis and further processing

### Risk Assessment

#### Technical Risks
- **Data Availability**: `is_available` field may not be present in all traces
- **Query Performance**: Large date ranges could impact database performance
- **Data Consistency**: Mixed data formats across different trace versions
- **Integration Complexity**: Adding to existing report infrastructure may introduce regressions

#### Mitigation Strategies
- **Null Handling**: Implement robust null checking for missing availability data
- **Query Optimization**: Use appropriate database indexes and query optimization
- **Format Validation**: Validate data format compatibility across trace versions
- **Regression Testing**: Comprehensive testing of existing report functionality

#### Business Risks
- **Stakeholder Expectations**: Report data must align with business understanding of availability
- **Data Interpretation**: Users need guidance on interpreting availability vs zenrows error reports
- **Workflow Integration**: New reports must fit into existing analysis workflows

#### Risk Mitigation
- **Clear Documentation**: Document relationship between availability and zenrows reports
- **User Training**: Provide examples and guidance for report interpretation
- **Phased Rollout**: Gradual deployment with stakeholder feedback incorporation

### Dependencies

#### Required Completions
- Phase 11 (Reporting Database Migration) ✅ **COMPLETED**
- Database populated with traces containing website_analysis data ✅ **AVAILABLE**
- Existing report command infrastructure ✅ **AVAILABLE**

#### Optional Enhancements
- Phase 16 (Availability Dataset Curation) for comprehensive availability analysis
- Enhanced error reporting integration for cross-reference analysis
- Dashboard integration for real-time availability monitoring

#### External Dependencies
- PostgreSQL database with appropriate indexing for performance
- Sufficient trace data with website_analysis outputs for meaningful reports
- Stakeholder requirements validation for report format and content

---

## Development Guidelines

### Code Quality Standards
- **Testing**: Minimum 95% test coverage for all phases
- **Documentation**: Comprehensive docstrings and user documentation
- **Error Handling**: Graceful degradation and informative error messages
- **Performance**: Efficient algorithms and resource usage optimization
- **Security**: Secure credential management and data handling practices

### Phase Transition Criteria
Each phase must meet the following criteria before proceeding to the next:
1. **Functional Requirements**: All features working as specified
2. **Quality Gates**: Test coverage, documentation, and performance benchmarks met
3. **User Acceptance**: Stakeholder validation and feedback incorporation
4. **Technical Debt**: Code refactoring and optimization completed
5. **Documentation**: User guides, API documentation, and troubleshooting guides updated

### Maintenance and Updates
- **Monthly Reviews**: Regular assessment of phase progress and priorities
- **Quarterly Planning**: Adjustment of roadmap based on user feedback and business needs
- **Continuous Integration**: Automated testing and deployment pipelines
- **Security Updates**: Regular security audits and dependency updates
- **Performance Monitoring**: Ongoing performance optimization and monitoring
