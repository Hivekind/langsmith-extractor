# Phase 3: Trace Archiving & Google Drive Integration

## Overview

This spec defines the implementation of trace archiving functionality that allows users to fetch, compress, and upload complete daily trace datasets to Google Drive, with the ability to restore archived data back to the local filesystem.

## User Stories

### As a Data Analyst
- I want to archive complete daily trace datasets to Google Drive so that I can free up local storage while maintaining access to historical data
- I want to restore archived traces from Google Drive so that I can re-analyze historical data when needed
- I want confirmation prompts before overwriting data so that I don't accidentally lose important information

### As an Engineering Lead
- I want automated archiving of trace data so that we maintain a complete historical record without manual intervention
- I want organized storage on Google Drive so that archived data is easy to locate and manage
- I want the ability to archive data for specific projects and dates so that I can manage storage efficiently

## Technical Requirements

### 1. Fix Trace Date Storage

**Current Issue**: Traces are stored in folders based on the fetch date (today), not the trace creation date.

**Solution**: Modify the storage logic to use the trace's `created_at` timestamp converted to UTC for determining the storage path.

**Changes Required**:
- Update `TraceStorage._get_storage_path()` to accept and use UTC trace creation date
- Modify `save_trace()` and `save_traces()` to extract creation date and convert to UTC
- All date-based operations must work with UTC days (GMT timezone)
- Ensure backward compatibility with existing stored traces

### 2. Archive Commands Structure

Create a new `archive` command group with subcommands:

```python
# Main archive command group
lse archive [subcommand]

# Subcommands:
- fetch: Fetch all traces for a specific date
- zip: Compress traces into a zip file
- upload: Upload zip file to Google Drive
- restore: Download and extract traces from Google Drive
```

Additionally, the bare `lse archive` command should perform all three operations (fetch, zip, upload) in sequence.

### 3. Google Drive Integration

**Authentication**:
- Support both OAuth2 and service account authentication
- Store credentials securely (not in repository)
- Use `GOOGLE_DRIVE_FOLDER_URL` from .env for target folder

**Folder Structure**:
```
[Google Drive Folder from URL]/
  └── [project-name]/
      ├── project-name_2025-08-29.zip  # UTC date
      ├── project-name_2025-08-30.zip  # UTC date
      └── ...
```

**API Operations**:
- List files in folder
- Upload file with overwrite protection
- Download file by name/date
- Create project subfolder if doesn't exist

### 4. Zip File Structure

**Naming Convention**: `[project-name]_[YYYY-MM-DD].zip` (where date is in UTC)

**Contents** (flat structure):
```
project-name_2025-08-29.zip
├── trace-id-1_timestamp.json
├── trace-id-2_timestamp.json
├── trace-id-3_timestamp.json
├── _summary.json
└── ...
```

### 5. Command Specifications

#### `lse archive fetch`
```bash
lse archive fetch --date 2025-08-29 --project my-project [--force]
```
- Fetches ALL traces for the specified UTC date (no limit)
- Stores in `data/[project]/[utc-date]/` using trace creation date converted to UTC
- `--force` flag skips confirmation if folder exists

#### `lse archive zip`
```bash
lse archive zip --date 2025-08-29 --project my-project [--output-dir ./archives]
```
- Creates zip from `data/[project]/[utc-date]/` folder
- Default output: `./archives/[project]_[utc-date].zip`
- Includes all JSON files in flat structure

#### `lse archive upload`
```bash
lse archive upload --date 2025-08-29 --project my-project [--force]
```
- Uploads zip file to Google Drive
- Creates project folder if needed
- `--force` flag skips overwrite confirmation

#### `lse archive` (combined)
```bash
lse archive --date 2025-08-29 --project my-project [--force]
```
- Executes fetch, zip, and upload in sequence
- Shows progress for each step
- Stops on any failure

#### `lse archive restore`
```bash
lse archive restore --project my-project [--start-date 2025-08-01] [--end-date 2025-08-31] [--force]
```
- Downloads zip files from Google Drive
- Extracts to `data/[project]/[utc-date]/` structure
- Default: restores all available dates
- `--force` flag skips overwrite confirmations

### 6. Progress Indicators

Use Rich progress bars for:
- Fetching traces (show count progress)
- Creating zip file (show file progress)
- Uploading to Google Drive (show upload progress)
- Downloading from Google Drive (show download progress)
- Extracting zip files (show extraction progress)

### 7. Error Handling

**Atomic Operations**: Treat each day as an atomic unit
- If fetch fails, no partial data is saved
- If zip fails, no partial zip is created
- If upload fails, local data remains intact

**Confirmation Prompts**:
- Before overwriting local folder during fetch
- Before overwriting zip file on Google Drive
- Before overwriting local data during restore

**Error Messages**:
- Clear indication of what failed and why
- Suggestions for recovery (e.g., use --force flag)
- Preserve partial progress where safe

## Implementation Plan

### Phase 3.1: Fix Date Storage
1. Update `TraceStorage` to use trace creation dates
2. Add migration utility for existing data (optional)
3. Update tests for new date handling

### Phase 3.2: Archive Commands Infrastructure
1. Create `lse/commands/archive.py` module
2. Implement command group structure
3. Add configuration for Google Drive

### Phase 3.3: Fetch & Zip Implementation
1. Implement `archive fetch` command
2. Implement `archive zip` command
3. Add progress indicators
4. Add overwrite protection

### Phase 3.4: Google Drive Integration
1. Add Google Drive client wrapper
2. Implement authentication (OAuth2/service account)
3. Implement `archive upload` command
4. Add folder management logic

### Phase 3.5: Restore Functionality
1. Implement `archive restore` command
2. Add date range filtering
3. Add extraction with progress
4. Add overwrite confirmations

### Phase 3.6: Combined Command & Testing
1. Implement combined `archive` command
2. Add comprehensive tests
3. Add integration tests with mock Drive
4. Documentation updates

## Dependencies

### New Python Packages
```toml
[project.dependencies]
google-auth = "^2.35.0"
google-auth-oauthlib = "^1.2.0"
google-api-python-client = "^2.149.0"
```

### Environment Variables
```bash
# Existing
LANGSMITH_API_KEY=xxx

# New
GOOGLE_DRIVE_FOLDER_URL=https://drive.google.com/drive/folders/xxx
GOOGLE_DRIVE_AUTH_TYPE=oauth2  # or 'service_account'
GOOGLE_DRIVE_CREDENTIALS_PATH=./credentials.json  # for service account
```

## Testing Strategy

### Unit Tests
- Test date extraction from traces
- Test zip file creation/extraction
- Test Google Drive operations (mocked)
- Test confirmation prompts
- Test error handling

### Integration Tests
- Test full archive workflow (fetch → zip → upload)
- Test restore workflow (download → extract)
- Test with real trace data (small dataset)
- Test overwrite scenarios

### Manual Testing
- Test with large datasets (1000+ traces)
- Test Google Drive authentication flows
- Test network interruption handling
- Test progress indicators

## Critical Issues Identified

### Issue 1: Incomplete Trace Fetching
**Problem**: UTC day boundary fetching returns 66 traces, but LangSmith UI shows 158 traces for the same UTC date (2025-08-26).
**Impact**: Archive is missing 58% of traces (92 traces not captured)
**Root Cause**: UTC day boundaries may not align with LangSmith's internal trace timestamping
**Status**: 🔴 Critical - Must be fixed before production use

### Issue 2: Missing Child Runs  
**Problem**: Current fetch only captures root traces, missing all child/sub-runs
**Impact**: LangSmith UI shows 5,361 total runs for the period, but we only capture ~158 root traces
**Root Cause**: `is_root=True` filter in client excludes child runs from fetch results
**Status**: 🔴 Critical - Archive is fundamentally incomplete without child runs

## Success Criteria

1. ✅ Traces are stored by UTC creation date, not fetch date
2. 🔴 **BROKEN**: Can fetch all traces for a specific date (missing 58% of traces)
3. 🔴 **BROKEN**: Can fetch all child runs for complete trace data
4. ✅ Can create zip files with proper naming
5. ✅ Can upload to Google Drive with folder organization  
6. ✅ Can restore archived data from Google Drive
7. ✅ Proper confirmation prompts prevent data loss
8. ✅ Progress indicators show operation status
9. ✅ All operations handle errors gracefully

## Future Enhancements

- Incremental archiving (only new traces)
- Compression options (zip, tar.gz, etc.)
- Encryption for sensitive data
- Automated daily archiving via cron
- Archive retention policies
- Multi-cloud support (S3, Azure Blob, etc.)