# Spec Requirements Document

> Spec: URL Pattern Analysis for ZenRows Errors
> Created: 2025-09-06
> Status: Planning

## Overview

Add URL pattern analysis capabilities to the langsmith-extractor CLI to identify which URL patterns, domains, and file types are generating the most ZenRows errors, enabling targeted optimization and troubleshooting of problematic sites and content types.

## User Stories

**Story 1: Identify Top Failing Domains and File Types**
As a data analyst, I want to analyze ZenRows errors by domain and file type so I can identify which websites and content types (PDFs, images, etc.) are consistently problematic and need special handling or alternative scraping approaches.

**Story 2: Analyze URL Patterns Over Time**
As a system administrator, I want to analyze URL pattern failures for a specific date or date range so I can correlate errors with deployment changes or external site modifications.

**Story 3: Focus on Top Problem URLs and File Types**
As a developer, I want to limit results to the top N failing URLs/domains/file types (e.g., --top 10) so I can prioritize fixes for the most impactful issues without being overwhelmed by the full dataset.

## Spec Scope

1. **URL Pattern Extraction**: Parse URLs from trace data to extract domains, file extensions, and URL patterns for analysis
2. **Domain and File Type Analysis**: Aggregate errors by domain and file type to identify problematic websites and content types
3. **File Extension Classification**: Detect and categorize file types from URL extensions (PDF, images, API endpoints, HTML pages, etc.)
4. **Error Category Integration**: Leverage existing error categorization system to show error types per URL pattern and file type
5. **Date Filtering**: Support --date and date range parameters consistent with existing CLI commands
6. **Configurable Result Limits**: Add --top parameter to limit results to most problematic URLs/domains/file types

## Out of Scope

- URL normalization beyond basic domain extraction
- Pattern matching for URL parameters or query strings
- Historical trending analysis across multiple date ranges in single command
- Integration with external URL analysis tools
- Automatic remediation suggestions

## Expected Deliverable

1. **New CLI Command**: `lse report zenrows-url-patterns` command that analyzes URL patterns in archived trace data
2. **Domain and File Type Error Report**: Output showing domains/URLs/file types ranked by error count with error category breakdown
3. **Parameterized Analysis**: Command supports --date, --date-range, and --top parameters for flexible analysis

## Spec Documentation

- Tasks: @.agent-os/specs/2025-09-06-url-pattern-analysis/tasks.md
- Technical Specification: @.agent-os/specs/2025-09-06-url-pattern-analysis/sub-specs/technical-spec.md