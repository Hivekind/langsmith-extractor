# Product Roadmap

## Phase 1: Core MVP ✅ COMPLETED

**Goal:** Build foundational trace fetching and storage capabilities
**Success Criteria:** Successfully fetch and store LangSmith traces locally with basic CLI interface

### Features

- [x] CLI application structure with Typer - Set up basic command structure `S` ✅
- [x] Configuration management - Handle API keys and settings via .env file `S` ✅
- [x] Basic error handling and logging - Ensure robust operation `S` ✅
- [x] Progress indication utilities - Rich progress bars and spinners `S` ✅
- [x] Fetch command scaffold - Complete parameter parsing and validation `M` ✅
- [x] LangSmith API integration - Replace placeholder with real API calls `M` ✅
- [x] Save traces as JSON files - Store raw trace data locally `S` ✅

### Completed Infrastructure

- **CLI Foundation**: Typer-based `lse` command with comprehensive help and error handling
- **Configuration System**: Pydantic settings with .env file support and validation
- **Logging**: Dual output (console + file) with configurable levels
- **Progress Indication**: Rich-based progress bars and spinners (no colors)
- **Testing**: 63 tests covering all components with excellent coverage
- **LangSmith Integration**: Real API integration with LangSmithClient wrapper and retry logic
- **JSON Storage**: Atomic file writes with organized directory structure and metadata
- **Error Handling**: Comprehensive error handling with exponential backoff retry logic

### Production Ready Features

✅ **Fetch by Project**: `lse fetch --project my-project --limit 10`  
✅ **Fetch by Trace ID**: `lse fetch --trace-id abc123`  
✅ **Date Range Filtering**: `lse fetch --start-date 2025-08-29 --end-date 2025-08-30`  
✅ **Organized Storage**: `data/{project-name}/{YYYY-MM-DD}/{trace-id}_{timestamp}.json`  
✅ **Progress Indication**: Real-time progress bars during fetch and save operations  
✅ **Robust Error Handling**: Automatic retry with exponential backoff for transient failures

**Status**: Phase 1 is now complete and production-ready! ✅

## Phase 2: Error Rate Reporting (Zenrows Scraper) ✅ COMPLETED

**Goal:** Generate daily error rate reports for zenrows_scraper failures
**Success Criteria:** Output "Date, Total Traces, Zenrows Error Count" for any given day

### Target Report Format
```
Date,Total Traces,Zenrows Errors,Error Rate
2025-08-28,220,10,4.5%
2025-08-29,195,8,4.1%
```

### Features

- [x] **Report command structure** - Add `lse report` command with date parameters `S` ✅
- [x] **Trace analysis engine** - Parse JSON traces and detect sub-trace patterns `M` ✅
- [x] **Zenrows error detection** - Find sub-traces named "zenrows_scraper" with Error status `S` ✅
- [x] **Daily aggregation logic** - Group traces by date and calculate error rates `S` ✅
- [x] **stdout output formatting** - CSV-style output for review and piping `S` ✅
- [x] **Date range support** - Generate reports for single days or date ranges `S` ✅
- [x] **Project-scoped reporting** - Filter reports by project or aggregate all projects `S` ✅
- [x] **UTC timezone support** - All day-based reporting uses UTC days (GMT) `S` ✅
- [ ] **Google Sheets export** - OAuth2 setup and automated sheet updates `M`

### Command Interface Design
```bash
# Single day report for specific project
lse report zenrows-errors --project my-project --date 2025-08-28

# Date range report for specific project
lse report zenrows-errors --project my-project --start-date 2025-08-01 --end-date 2025-08-31

# All projects (aggregated)
lse report zenrows-errors --date 2025-08-28

# Output to Google Sheets (future)
lse report zenrows-errors --date 2025-08-28 --export-to sheets
```

### Completed Implementation Details

✅ **Recursive trace analysis** - Searches all child_runs recursively for zenrows_scraper errors  
✅ **UTC timezone handling** - All dates interpreted as UTC days, eliminating timezone complexity  
✅ **Inclusive date ranges** - End dates include full day (23:59:59)  
✅ **65+ comprehensive tests** - Full test coverage with TDD approach  
✅ **Live data validation** - Successfully tested with 400+ real traces

### Dependencies
- Existing JSON trace files from Phase 1 fetch operations
- Google Cloud project with Sheets API (for export feature only)

## Phase 3: Trace Archiving & Google Drive Integration ✅ COMPLETED

**Goal:** Archive complete daily trace datasets to Google Drive with restore capabilities
**Success Criteria:** Successfully fetch, zip, and upload daily trace data to Google Drive with ability to restore

### Features

- [x] **Fix trace date storage** - Store traces by creation date, not fetch date `S` ✅
- [x] **Archive fetch command** - Fetch full trace data for a specific date `M` ✅
- [x] **Archive zip command** - Compress daily traces into zip files `S` ✅
- [x] **Google Drive upload** - Upload zip archives to configured Drive folder `M` ✅
- [x] **Combined archive command** - Single command to fetch, zip, and upload `S` ✅
- [x] **Restore from Drive** - Download and extract archived traces from Drive `M` ✅
- [x] **Overwrite protection** - Confirm before overwriting local or remote data `S` ✅
- [x] **Progress indicators** - Show progress during long-running operations `S` ✅

### Command Interface
```bash
# Individual steps
lse archive fetch --date 2025-08-29 --project my-project
lse archive zip --date 2025-08-29 --project my-project
lse archive upload --date 2025-08-29 --project my-project

# Combined operation
lse archive --date 2025-08-29 --project my-project

# Restore from Google Drive
lse archive restore --start-date 2025-08-01 --end-date 2025-08-31 --project my-project
```

### Archive Structure
- **Local storage**: `data/[project-name]/[trace-creation-date-utc]/trace-files.json`
- **Zip naming**: `[project-name]_[trace-creation-date-utc].zip`
- **Drive structure**: `[configured-folder]/[project-name]/[project-name]_[date-utc].zip`
- **Date Format**: All dates use UTC days (YYYY-MM-DD in GMT/UTC timezone)

### Dependencies
- Google Drive API credentials (OAuth2 or service account)
- Configured GOOGLE_DRIVE_FOLDER_URL in .env
- Fixed trace date storage (store by creation date)

### Completed Implementation

**Status**: Phase 3 is now complete and production-ready! ✅

#### Core Components Built
- **TraceStorage Enhanced**: Added creation date extraction with timezone-aware storage paths
- **ArchiveManager**: Complete zip creation/extraction and local archive management system
- **GoogleDriveClient**: Full Google Drive API integration with OAuth2 and service account support
- **Archive Commands**: Complete CLI suite with individual and combined operations

#### Production Ready Features

✅ **Archive fetch**: `lse archive fetch --date 2025-08-29 --project my-project`  
✅ **Archive zip**: `lse archive zip --date 2025-08-29 --project my-project`  
✅ **Archive upload**: `lse archive upload --date 2025-08-29 --project my-project`  
✅ **Combined workflow**: `lse archive --date 2025-08-29 --project my-project`  
✅ **Archive restore**: `lse archive restore --project my-project --start-date 2025-08-01`  
✅ **Progress indicators**: Rich progress bars for all long-running operations  
✅ **Overwrite protection**: Confirmation prompts with --force flag bypass  
✅ **UTC date-based storage**: Traces stored by UTC creation date, not fetch date  

#### Architecture Enhancements
- **Enhanced Configuration**: Added Google Drive settings with validation
- **Dependencies Added**: google-auth, google-auth-oauthlib, google-api-python-client
- **Error Handling**: Comprehensive error handling with recovery suggestions
- **File Organization**: Proper archive structure with project/date organization

#### Testing Completed
- Date extraction logic verified with existing trace data
- Zip creation tested with 177+ trace files 
- Command structure and help system verified
- Google Drive configuration validation working

## Phase 4: Advanced Reporting & Automation

**Goal:** Expand reporting capabilities and add automation features
**Success Criteria:** Support multiple report types and automated daily data collection

### Features

- [ ] **Generic report framework** - Extensible system for custom reports `M`
- [ ] **Additional error patterns** - Support for other error types beyond zenrows `S`
- [ ] **Performance reports** - Latency, token usage, and throughput analysis `M`
- [ ] **Automated daily fetch** - Scheduled data collection with cron support `M`
- [ ] **Historical data backfill** - Fetch and analyze past trace data `S`
- [ ] **Multiple export formats** - CSV files and Excel export options `S`
- [ ] **Report scheduling** - Automated report generation and delivery `L`
- [ ] **Dashboard integration** - Connect to monitoring dashboards `L`

### Future Report Types
- Token usage trends over time
- API endpoint performance analysis
- Error pattern analysis across different components
- Daily/weekly/monthly summary reports

### Dependencies
- Usage feedback from zenrows error reporting
- Additional stakeholder report requirements
