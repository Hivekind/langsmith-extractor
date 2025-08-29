# Spec Requirements Document

> Spec: Zenrows Error Reporting
> Created: 2025-08-29
> Status: Planning

## Overview

Add a report command to analyze stored LangSmith trace data and generate daily error rate statistics for zenrows_scraper failures. This feature will provide visibility into scraper reliability trends and help identify patterns in zenrows-related errors.

## User Stories

### Daily Error Rate Analysis
As a Hivekind analyst, I want to generate daily error rate reports for zenrows_scraper, so that I can track scraper reliability trends and identify problematic days.

The user runs `lse report zenrows-errors --date 2025-08-28` and receives a CSV output showing the total traces for that day, how many had zenrows_scraper errors, and the error percentage. This enables quick assessment of scraper performance on any given day.

### Historical Error Trend Analysis  
As a developer investigating zenrows issues, I want to analyze error rates across date ranges, so that I can identify patterns and correlate errors with deployments or external factors.

The user runs `lse report zenrows-errors --start-date 2025-08-01 --end-date 2025-08-31` and receives daily error statistics for the entire month, enabling trend analysis and pattern identification for debugging and optimization efforts.

### Automated Reporting to Google Sheets
As a team lead monitoring system health, I want error rate reports automatically exported to Google Sheets, so that stakeholders can access up-to-date scraper reliability metrics without manual intervention.

The user runs `lse report zenrows-errors --date 2025-08-28 --export-to sheets` and the daily error statistics are automatically appended to a designated Google Sheet, enabling dashboard integration and stakeholder visibility.

## Spec Scope

1. **Report Command Structure** - Add `lse report zenrows-errors` with date filtering parameters
2. **Trace Analysis Engine** - Parse existing JSON trace files to detect error patterns in sub-traces
3. **Zenrows Error Detection** - Identify sub-traces named "zenrows_scraper" with Error status
4. **Daily Aggregation Logic** - Calculate error rates by grouping traces by date
5. **CSV Output Format** - Generate "Date,Total Traces,Zenrows Errors,Error Rate" output to stdout

## Out of Scope

- Analysis of other error types beyond zenrows_scraper
- Database storage of report results
- Real-time monitoring or alerting
- Modification of existing trace fetching functionality
- Custom report templates or formatting options

## Expected Deliverable

1. Running `lse report zenrows-errors --date 2025-08-28` outputs CSV data for the specified date
2. Running `lse report zenrows-errors --start-date 2025-08-01 --end-date 2025-08-31` outputs CSV data for the date range
3. All existing CLI functionality continues to work without changes

## Spec Documentation

- Tasks: @.agent-os/specs/2025-08-29-zenrows-error-reporting/tasks.md
- Technical Specification: @.agent-os/specs/2025-08-29-zenrows-error-reporting/sub-specs/technical-spec.md