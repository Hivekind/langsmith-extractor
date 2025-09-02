# Remove Redundant Fetch Command

## Problem Summary

The LSE CLI currently has two fetch commands with overlapping functionality:
- `lse fetch` - General purpose fetching with limits and filtering
- `lse archive fetch` - Complete data archiving for specific dates

This creates user confusion, maintenance overhead, and violates the principle of having one clear way to do things. Users must learn two different command interfaces when a single enhanced command could handle all use cases.

## Analysis of Current Commands

### `lse fetch` Capabilities
```bash
# Fetch specific trace
lse fetch --trace-id abc123

# Fetch from project with limit
lse fetch --project my-project --limit 10

# Fetch date range
lse fetch --start-date 2024-01-01 --end-date 2024-01-02
```

### `lse archive fetch` Capabilities  
```bash
# Fetch complete daily dataset
lse archive fetch --project my-project --date 2025-08-20

# Include child runs
lse archive fetch --project my-project --date 2025-08-20 --include-children

# Control API rate limiting
lse archive fetch --project my-project --date 2025-08-20 --delay-ms 500
```

### Overlap Analysis
Both commands:
- Fetch traces from LangSmith API
- Support project filtering
- Store traces locally in organized structure
- Use same underlying client and storage systems

### Missing Functionality Cross-over
- `lse fetch` lacks: child runs support, date-specific organization, rate limiting
- `lse archive fetch` lacks: trace ID support, limits, date ranges, interactive use

## Solution Design

### Unified Command Interface

Consolidate everything into `lse archive fetch` with enhanced functionality:

```bash
# Current archive use cases (unchanged)
lse archive fetch --project my-project --date 2025-08-20
lse archive fetch --project my-project --date 2025-08-20 --include-children

# New capabilities (migrated from lse fetch)
lse archive fetch --trace-id abc123
lse archive fetch --project my-project --date 2025-08-20 --limit 100
lse archive fetch --project my-project --start-date 2025-08-01 --end-date 2025-08-31

# Combined capabilities
lse archive fetch --project my-project --date 2025-08-20 --limit 50 --include-children
```

### Command Naming Decision

**Option 1**: Keep `lse archive fetch` 
- ✅ No breaking changes to existing workflows
- ❌ "archive" in name suggests only bulk operations

**Option 2**: Rename to `lse fetch`
- ✅ Simpler, more intuitive name
- ❌ Breaking change for archive users
- **Recommended**: This better reflects the unified purpose

### Enhanced Parameter Design

```bash
lse fetch [OPTIONS]

Options:
  # Target selection (one required)
  --trace-id    TEXT     Fetch specific trace by ID
  --project     TEXT     Project name for date/range based fetching
  
  # Date filtering (when using --project)
  --date        TEXT     Specific date (YYYY-MM-DD) - fetches all traces
  --start-date  TEXT     Date range start (YYYY-MM-DD)  
  --end-date    TEXT     Date range end (YYYY-MM-DD)
  
  # Behavior modifiers
  --limit       INTEGER  Max traces to fetch (default: unlimited for --date, 100 for ranges)
  --include-children     Fetch complete trace hierarchies
  --delay-ms    INTEGER  API request delay in milliseconds (default: 200)
  --force                Skip confirmations for large operations
```

### Default Behaviors

1. **Single date** (`--date`): Fetch all traces (archive behavior)
2. **Date range**: Fetch with sensible limit (100) unless overridden
3. **Trace ID**: Fetch single trace with children
4. **Child runs**: Default OFF for performance, explicit opt-in

## Implementation Plan

### Phase 1: Enhance Archive Fetch
1. Add `--trace-id` support to archive fetch
2. Add `--start-date`/`--end-date` range support  
3. Add `--limit` parameter with smart defaults
4. Update help text and examples

### Phase 2: Migration Preparation
1. Audit all uses of `lse fetch` in:
   - Documentation and examples
   - Test files
   - Internal workflows
2. Create migration guide
3. Add deprecation warning to `lse fetch`

### Phase 3: Command Rename (Optional)
1. Rename `lse archive fetch` → `lse fetch`
2. Keep `lse archive fetch` as alias with deprecation warning
3. Update all documentation

### Phase 4: Cleanup
1. Remove old `lse fetch` command entirely
2. Remove deprecation warnings
3. Clean up test files and documentation

## Breaking Changes Assessment

### Minimal Impact Approach (Recommended)
- Keep `lse archive fetch` as primary command
- Remove `lse fetch` entirely
- All existing archive workflows continue unchanged

### Clean Slate Approach (Optional)
- Rename to `lse fetch` with enhanced functionality
- Provide migration period with aliases
- Better long-term UX but requires user migration

## Benefits

### For Users
- **Single command to learn**: One fetch interface for all use cases
- **Consistent behavior**: Same parameters and storage patterns
- **Enhanced capabilities**: Best features from both commands combined
- **Clearer documentation**: Single set of examples and help text

### For Maintenance  
- **Reduced code duplication**: Single fetch implementation
- **Simplified testing**: Fewer command combinations to test
- **Easier documentation**: Single command to document
- **Clear upgrade path**: One place to add new fetch features

## Risk Mitigation

### User Confusion Risk
- **Mitigation**: Comprehensive documentation updates
- **Mitigation**: Clear error messages if old command used

### Workflow Disruption Risk
- **Mitigation**: Audit existing usage before changes
- **Mitigation**: Deprecation period with warnings
- **Mitigation**: Alias support during transition

### Feature Regression Risk
- **Mitigation**: Comprehensive test coverage for all scenarios
- **Mitigation**: Feature parity checklist validation

## Success Criteria

1. **Feature Parity**: All current `lse fetch` use cases work with enhanced `lse archive fetch`
2. **No Regressions**: All existing archive workflows continue unchanged
3. **Test Coverage**: All fetch scenarios covered by unified test suite
4. **Documentation**: Single, comprehensive fetch command documentation
5. **User Experience**: Simpler, more intuitive command interface

## Timeline

- **Day 1**: Enhance archive fetch with missing functionality
- **Day 1**: Add comprehensive test coverage
- **Day 2**: Remove old fetch command
- **Day 2**: Update documentation and examples
- **Day 3**: Test migration and validate all use cases

This consolidation will significantly improve the CLI's usability while reducing maintenance overhead.