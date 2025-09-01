# Task Tracking: Fix Zenrows Error Detection

## Status: 🔥 IN PROGRESS

**Start Date**: 2025-09-01
**Target Completion**: 2025-09-02
**Priority**: HIGH - Production bug affecting reporting accuracy

## Task Breakdown

### Phase 1: Core Logic Fix ⏳

#### 1.1 Update extract_zenrows_errors function
- [ ] Check root trace for zenrows_scraper name
- [ ] Check root trace status for "error"
- [ ] Create error record from root trace
- [ ] Preserve existing child_runs search logic
- **File**: `lse/analysis.py`
- **Function**: `extract_zenrows_errors()`
- **Estimate**: 30 minutes

#### 1.2 Handle None child_runs
- [ ] Add null check before searching child_runs
- [ ] Prevent TypeError when child_runs is None
- [ ] Add appropriate logging for debugging
- **File**: `lse/analysis.py`
- **Estimate**: 15 minutes

### Phase 2: Testing 🧪

#### 2.1 Unit Tests
- [ ] Test root-level error detection
- [ ] Test with None child_runs
- [ ] Test with empty child_runs list
- [ ] Test with populated child_runs
- [ ] Test mixed scenarios (root + child errors)
- **File**: `tests/test_analysis.py`
- **Estimate**: 45 minutes

#### 2.2 Integration Testing
- [ ] Run report on 2025-08-20 data
- [ ] Verify 17 errors detected
- [ ] Check error details are correct
- [ ] Test with other dates for regression
- **Command**: `uv run lse report zenrows-errors --project my-project --date 2025-08-20`
- **Estimate**: 30 minutes

### Phase 3: Enhanced Fetching (Optional) 🔄

#### 3.1 Add --include-children support
- [ ] Research LangSmith API child_runs population
- [ ] Add flag to fetch command
- [ ] Update storage to handle larger files
- [ ] Document performance impact
- **Files**: `lse/cli.py`, `lse/client.py`
- **Estimate**: 2 hours
- **Decision**: May defer to Phase 5

### Phase 4: Documentation 📚

#### 4.1 Code Documentation
- [ ] Add docstring updates
- [ ] Include examples of both error types
- [ ] Document the child_runs limitation
- **Files**: `lse/analysis.py`
- **Estimate**: 15 minutes

#### 4.2 User Documentation
- [ ] Update README if needed
- [ ] Add troubleshooting section
- [ ] Document known limitations
- **Files**: `README.md`, `CLAUDE.md`
- **Estimate**: 30 minutes

## Progress Log

### 2025-09-01
- ✅ Identified root cause: child_runs are None, errors at root level
- ✅ Analyzed 2025-08-20 data: confirmed 17 root-level errors
- ✅ Updated roadmap with Phase 4 for bug fix
- ✅ Created specification document
- ✅ Created this task tracking file
- ⏳ Ready to implement fix

### Next Steps
1. Implement the core logic fix in `extract_zenrows_errors()`
2. Run against 2025-08-20 data to verify fix
3. Add comprehensive tests
4. Consider if --include-children support is needed

## Notes and Blockers

### Notes
- All 4191 traces from 2025-08-20 have `child_runs: None`
- 17 traces have `name: "zenrows_scraper"` and `status: "error"`
- Current code only searches child_runs, missing all root errors
- Fix must be backwards compatible

### Potential Blockers
- None identified yet

## Definition of Done

- [ ] Code changes implemented and linted
- [ ] All tests passing
- [ ] Report shows 17 errors for 2025-08-20
- [ ] No regression on other dates
- [ ] Documentation updated
- [ ] Code reviewed and approved
- [ ] Deployed to production environment

## Commands for Testing

```bash
# Test the fix
uv run lse report zenrows-errors --project my-project --date 2025-08-20

# Expected output should show:
# Date,Total Traces,Zenrows Errors,Error Rate
# 2025-08-20,4191,17,0.4%

# Run tests
uv run pytest tests/test_analysis.py -v

# Check code quality
uv run ruff check --fix . && uv run ruff format .
```
