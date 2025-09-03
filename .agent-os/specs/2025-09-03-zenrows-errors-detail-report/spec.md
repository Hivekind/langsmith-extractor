# Spec Requirements Document

> Spec: Zenrows Errors Detail Report
> Created: 2025-09-03

## Overview

Create a detailed zenrows error reporting command that provides hierarchical visibility into errors grouped by cryptocurrency symbol and root trace, enabling stakeholders to analyze error patterns across different cryptocurrencies and specific trace contexts.

## User Stories

### Error Analysis by Cryptocurrency

As a data analyst, I want to view zenrows errors organized by cryptocurrency symbol, so that I can identify which cryptocurrencies have the most scraping issues and prioritize fixes accordingly.

The analyst runs the report command for a specific date and receives a hierarchical view showing each cryptocurrency, its associated root traces, and the specific errors encountered. This allows them to quickly identify patterns such as certain cryptocurrencies consistently failing due to rate limits or specific proxy issues.

### Root Trace Error Tracking

As an operations engineer, I want to see all zenrows errors grouped by their true root trace (the top-level trace that initiated the entire hierarchy, such as "due_diligence"), so that I can understand the full business context of failures and identify systemic issues in our scraping pipelines.

The engineer uses the report to see which top-level business processes are experiencing errors, allowing them to correlate failures with specific business workflows rather than just individual scraper runs. This enables them to understand if errors are affecting specific business operations like due diligence processes or market analysis pipelines.

## Spec Scope

1. **Report Command** - Add `lse report zenrows-detail` command to generate hierarchical error reports
2. **Crypto Symbol Extraction** - Parse trace metadata to identify and extract cryptocurrency symbols from trace context
3. **True Root Trace Identification** - Traverse up the trace hierarchy to find the top-level root trace (e.g., "due_diligence") rather than the immediate parent trace containing the zenrows error
4. **Hierarchical Grouping** - Organize errors in crypto symbol → true root trace → error message hierarchy
5. **Error Message Extraction** - Extract and display actual error messages from zenrows_scraper traces
6. **Date and Project Filtering** - Support single date filtering (--date only) and project scoping

## Out of Scope

- Automatic error resolution or retry mechanisms
- Real-time monitoring or alerting capabilities
- Modification of existing zenrows-errors summary report
- Integration with external monitoring systems
- Historical trend analysis beyond date range queries

## Expected Deliverable

1. Working `lse report zenrows-detail` command that generates hierarchical error reports from archived trace data
2. Clear, readable output showing crypto symbol → root trace → error organization with proper indentation
3. Support for single-date queries (--date) with project filtering capabilities, consistent with archive commands