# Phase 3: Trace Archiving Tasks

## Phase 3.1: Fix Date Storage ⏳

### Task 1: Update TraceStorage for creation date usage
- [ ] Modify `_get_storage_path()` to accept trace creation date
- [ ] Update `save_trace()` to extract and use `created_at` from trace
- [ ] Update `save_traces()` to handle creation dates for batch saves
- [ ] Ensure backward compatibility with existing stored traces

### Task 2: Add UTC date extraction utilities
- [ ] Create helper function to extract creation date from trace
- [ ] Handle timezone conversion to UTC (from any timezone to GMT)
- [ ] Add validation for UTC date formats

### Task 3: Update tests for UTC date handling
- [ ] Update storage tests to verify UTC creation date usage
- [ ] Add tests for UTC date extraction logic  
- [ ] Test backward compatibility

## Phase 3.2: Archive Commands Infrastructure ⏳

### Task 4: Create archive command module
- [ ] Create `lse/commands/archive.py`
- [ ] Set up Typer app for archive commands
- [ ] Register with main CLI app

### Task 5: Add Google Drive configuration
- [ ] Update `config.py` with Drive settings
- [ ] Add environment variables to `.env.example`
- [ ] Add validation for Drive configuration

### Task 6: Create archive utilities module
- [ ] Create `lse/archive.py` for shared logic
- [ ] Add zip file creation utilities
- [ ] Add progress indicator helpers

## Phase 3.3: Fetch & Zip Implementation ⏳

### Task 7: Implement archive fetch command
- [ ] Create fetch command function
- [ ] Add UTC date parameter parsing
- [ ] Implement fetch all traces for UTC date (no limit)
- [ ] Add overwrite confirmation logic
- [ ] Add --force flag support

### Task 8: Implement archive zip command
- [ ] Create zip command function
- [ ] Implement zip file creation from folder
- [ ] Add flat file structure in zip
- [ ] Include _summary.json in zip
- [ ] Add progress indicator for zipping

### Task 9: Add overwrite protection
- [ ] Implement confirmation prompts
- [ ] Add --force flag to skip prompts
- [ ] Handle user input gracefully

## Phase 3.4: Google Drive Integration ⏳

### Task 10: Create Google Drive client
- [ ] Create `lse/drive.py` module
- [ ] Implement authentication (OAuth2/service account)
- [ ] Add Drive API wrapper methods
- [ ] Handle authentication errors

### Task 11: Implement folder management
- [ ] Parse folder URL from environment
- [ ] Create project subfolders as needed
- [ ] List files in folders
- [ ] Check for existing files

### Task 12: Implement archive upload command
- [ ] Create upload command function
- [ ] Add file upload with progress
- [ ] Add overwrite confirmation for existing files
- [ ] Handle upload errors and retries

## Phase 3.5: Restore Functionality ⏳

### Task 13: Implement archive restore command
- [ ] Create restore command function
- [ ] Add UTC date range parameters
- [ ] List available archives on Drive
- [ ] Download selected archives

### Task 14: Implement extraction logic
- [ ] Extract zip files to correct UTC folder structure
- [ ] Add progress indicator for extraction
- [ ] Handle existing local files
- [ ] Add overwrite confirmations

### Task 15: Add restore error handling
- [ ] Handle missing archives gracefully
- [ ] Validate zip file integrity
- [ ] Clean up partial extractions on failure

## Phase 3.6: Combined Command & Testing ⏳

### Task 16: Implement combined archive command
- [ ] Create main archive command
- [ ] Chain fetch, zip, upload operations
- [ ] Show progress for each step
- [ ] Stop on any failure

### Task 17: Add comprehensive unit tests
- [ ] Test date storage fixes
- [ ] Test zip creation/extraction
- [ ] Test Drive operations (mocked)
- [ ] Test command functions

### Task 18: Add integration tests
- [ ] Test full archive workflow
- [ ] Test restore workflow
- [ ] Test error scenarios
- [ ] Test with sample data

### Task 19: Documentation and examples
- [ ] Update CLAUDE.md with new commands
- [ ] Add examples to README
- [ ] Document Drive setup process
- [ ] Add troubleshooting guide

## Summary

**Total Tasks**: 19
**Completed**: 0/19
**Status**: Not Started

## Priority Order

1. **Critical Path** (Must do first):
   - Task 1-3: Fix date storage issue
   - Task 4-6: Set up command infrastructure

2. **Core Functionality**:
   - Task 7-9: Fetch and zip implementation
   - Task 10-12: Google Drive integration

3. **Complete Feature**:
   - Task 13-15: Restore functionality
   - Task 16: Combined command

4. **Quality & Documentation**:
   - Task 17-19: Testing and documentation

## Time Estimates

- Phase 3.1: 2-3 hours
- Phase 3.2: 1-2 hours
- Phase 3.3: 3-4 hours
- Phase 3.4: 4-5 hours
- Phase 3.5: 3-4 hours
- Phase 3.6: 3-4 hours

**Total Estimate**: 16-22 hours