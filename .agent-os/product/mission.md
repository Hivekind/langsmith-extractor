# Product Mission

## Pitch

LangSmith Extractor is a command-line utility that helps internal teams at Hivekind extract and analyze LangSmith trace data by providing automated data fetching, transformation, and export capabilities for comprehensive local analysis and reporting.

## Users

### Primary Customers

- **Internal Analytics Teams**: Teams at Hivekind who need to analyze LLM application performance and usage patterns from LangSmith data
- **Engineering Teams**: Developers and engineers who need to debug, monitor, and optimize LLM-powered applications

### User Personas

**Data Analyst** (25-40 years old)
- **Role:** Data Analyst / Business Intelligence Analyst
- **Context:** Works at Hivekind analyzing LLM application performance metrics and creating reports for stakeholders
- **Pain Points:** Manual data extraction from LangSmith UI is time-consuming, Limited ability to perform custom analysis on trace data
- **Goals:** Automate data extraction process, Create custom reports from LangSmith data

**Engineering Lead** (30-45 years old)
- **Role:** Engineering Manager / Tech Lead
- **Context:** Oversees LLM application development and needs visibility into system performance
- **Pain Points:** Difficulty aggregating trace data across multiple projects, No automated way to track performance trends
- **Goals:** Monitor application performance trends, Identify optimization opportunities

## The Problem

### Manual Data Extraction Overhead

Extracting trace data from LangSmith requires manual exports through the UI, which is time-consuming and error-prone. Teams spend hours per week manually downloading and processing data.

**Our Solution:** Automated CLI tool that fetches trace data programmatically and saves it locally for analysis.

### Limited Analysis Capabilities

LangSmith's built-in analytics don't support custom queries or complex data transformations needed for specific business reports. Teams struggle to create the exact reports stakeholders need.

**Our Solution:** Transform raw trace data into customizable tabular formats that can power any report structure.

### Disconnected Reporting Workflows

Data from LangSmith needs to be manually transferred to Google Sheets for stakeholder reporting. This creates delays and increases the risk of data inconsistency.

**Our Solution:** Direct export to Google Sheets with automated formatting for seamless reporting workflows.

## Differentiators

### Local-First Architecture

Unlike cloud-based solutions, we store all data locally, giving teams complete control over their trace data. This results in faster queries and no ongoing API costs for data access.

### Extensible Report Framework

Unlike fixed reporting tools, we provide a framework where teams can define custom transformations in code. This results in unlimited flexibility for creating exactly the reports needed.

## Key Features

### Core Features

- **Automated Trace Fetching:** Programmatically retrieve full trace data from LangSmith accounts via API
- **Local Data Storage:** Save traces in JSON files or lightweight local database for fast access
- **Custom Data Transformations:** Define report structures in code to transform raw data into specific tabular formats
- **Google Sheets Export:** Automatically export transformed data to Google Sheets with proper formatting

### Data Management Features

- **Batch Processing:** Efficiently fetch and process multiple traces in a single operation
- **Error Handling:** Robust error handling for API failures and data inconsistencies
- **Data Validation:** Ensure data integrity during fetching and transformation processes

### Future Features

- **Incremental Sync:** Track previously fetched traces to support ongoing synchronization
- **Multiple Export Formats:** Support for CSV, Excel, and other export formats beyond Google Sheets