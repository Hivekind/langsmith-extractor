"""Report command for generating LangSmith trace analysis reports."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from lse.analysis import TraceAnalyzer
from lse.config import get_settings
from lse.exceptions import ValidationError
from lse.formatters import ReportFormatter

logger = logging.getLogger("lse.report")
console = Console()

# Create the report command group
report_app = typer.Typer(
    name="report",
    help="Generate reports from LangSmith trace data",
    no_args_is_help=True,
)


def validate_date(date_str: str) -> datetime:
    """Validate and parse date string in YYYY-MM-DD format.

    Args:
        date_str: Date string to validate

    Returns:
        Parsed datetime object

    Raises:
        ValidationError: If date format is invalid
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValidationError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD.")


def validate_date_range(
    start_date: Optional[str], end_date: Optional[str]
) -> tuple[Optional[datetime], Optional[datetime]]:
    """Validate date range parameters with UTC timezone handling.

    Args:
        start_date: Start date string (optional)
        end_date: End date string (optional)

    Returns:
        Tuple of parsed datetime objects in UTC timezone

    Raises:
        ValidationError: If date range is invalid
    """
    if not start_date and not end_date:
        return None, None

    if start_date and not end_date:
        raise ValidationError("End date is required when start date is provided.")

    if end_date and not start_date:
        raise ValidationError("Start date is required when end date is provided.")

    # Validate date format
    start_parsed = validate_date(start_date) if start_date else None
    end_parsed = validate_date(end_date) if end_date else None

    if start_parsed and end_parsed and start_parsed >= end_parsed:
        raise ValidationError("Start date must be before end date.")

    # Convert to UTC timezone datetimes for analysis
    if start_date and end_date:
        from datetime import timezone

        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        end_dt = end_dt.replace(
            hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
        )
        return start_dt, end_dt

    return None, None


def _display_category_statistics(analysis_results, progress_console):
    """Display category statistics to the console for verbose output."""
    from lse.error_categories import ErrorCategoryManager

    # Calculate total statistics across all dates
    total_traces = sum(data.get("total_traces", 0) for data in analysis_results.values())
    total_errors = sum(data.get("zenrows_errors", 0) for data in analysis_results.values())

    if total_errors == 0:
        progress_console.print("[yellow]📊 No zenrows errors found in the analyzed data[/yellow]")
        return

    # Aggregate category counts
    category_manager = ErrorCategoryManager()
    category_totals = {}

    for data in analysis_results.values():
        categories = data.get("categories", {})
        for category, count in categories.items():
            category_totals[category] = category_totals.get(category, 0) + count

    # Display summary
    progress_console.print("[cyan]📊 Analysis Summary:[/cyan]")
    progress_console.print(f"  Total traces analyzed: {total_traces:,}")
    progress_console.print(f"  Total zenrows errors: {total_errors:,}")
    progress_console.print(f"  Overall error rate: {(total_errors / total_traces) * 100:.1f}%")

    if category_totals:
        progress_console.print("[cyan]🏷️  Error Category Breakdown:[/cyan]")

        # Sort categories by count (descending)
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)

        for category, count in sorted_categories:
            if count > 0:
                percentage = (count / total_errors) * 100
                description = category_manager.get_category_description(category)
                progress_console.print(
                    f"  • {category}: {count:,} ({percentage:.1f}%) - {description}"
                )


def _merge_project_results(all_results, project_results):
    """Merge project results into the aggregated results dictionary."""
    for date_key, data in project_results.items():
        if date_key in all_results:
            # Aggregate data for this date across projects
            all_results[date_key]["total_traces"] += data["total_traces"]
            all_results[date_key]["zenrows_errors"] += data["zenrows_errors"]

            # Aggregate category counts
            existing_categories = all_results[date_key].get("categories", {})
            new_categories = data.get("categories", {})

            for category, count in new_categories.items():
                existing_categories[category] = existing_categories.get(category, 0) + count

            all_results[date_key]["categories"] = existing_categories
        else:
            all_results[date_key] = data.copy()


def generate_zenrows_report(
    project_name: Optional[str] = None,
    single_date: Optional[datetime] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    verbose: bool = False,
) -> str:
    """Generate zenrows error report for specified date.

    Args:
        project_name: Project to analyze (optional, defaults to all projects)
        single_date: Single date to analyze (required)

    Returns:
        CSV formatted report string
    """
    settings = get_settings()
    data_dir = Path(settings.output_dir)

    # Initialize the trace analyzer
    analyzer = TraceAnalyzer()

    # Set up progress tracking
    if verbose:
        progress_console = Console(stderr=True)
        progress_console.print(
            "[blue]🔍 Starting zenrows error analysis with categorization...[/blue]"
        )

    try:
        if project_name:
            # Single project analysis
            logger.info(f"Analyzing project: {project_name}")
            if verbose:
                progress_console.print(f"[green]📁 Analyzing project:[/green] {project_name}")

            analysis_results = analyzer.analyze_zenrows_errors(
                data_dir=data_dir,
                project_name=project_name,
                single_date=single_date,
            )

            if verbose and analysis_results:
                _display_category_statistics(analysis_results, progress_console)
        else:
            # Multi-project analysis - aggregate across all projects
            project_dirs = [d for d in data_dir.iterdir() if d.is_dir()]
            if not project_dirs:
                logger.warning(f"No project directories found in {data_dir}")
                return "Date,Total Traces,Zenrows Errors,Error Rate\n"

            if verbose:
                progress_console.print(
                    f"[green]📂 Found {len(project_dirs)} projects to analyze[/green]"
                )

            # Aggregate results across all projects
            all_results = {}

            # Use progress bar for multi-project analysis
            if verbose:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=progress_console,
                ) as progress:
                    task = progress.add_task("Analyzing projects", total=len(project_dirs))

                    for project_dir in project_dirs:
                        current_project = project_dir.name
                        logger.info(f"Analyzing project: {current_project}")
                        progress.update(task, description=f"Analyzing {current_project}")

                        # Analyze traces for this project
                        project_results = analyzer.analyze_zenrows_errors(
                            data_dir=data_dir,
                            project_name=current_project,
                            single_date=single_date,
                            start_date=start_date,
                            end_date=end_date,
                        )

                        # Merge results
                        _merge_project_results(all_results, project_results)
                        progress.advance(task)
            else:
                # Non-verbose mode - just process without progress bar
                for project_dir in project_dirs:
                    current_project = project_dir.name
                    logger.info(f"Analyzing project: {current_project}")

                    # Analyze traces for this project
                    project_results = analyzer.analyze_zenrows_errors(
                        data_dir=data_dir,
                        project_name=current_project,
                        single_date=single_date,
                        start_date=start_date,
                        end_date=end_date,
                    )

                    # Merge results
                    _merge_project_results(all_results, project_results)

            # Recalculate error rates after aggregation
            for date_key, data in all_results.items():
                if data["total_traces"] == 0:
                    data["error_rate"] = 0.0
                else:
                    data["error_rate"] = round(data["zenrows_errors"] / data["total_traces"], 6)

            analysis_results = all_results

            if verbose and analysis_results:
                _display_category_statistics(analysis_results, progress_console)

        # Format results as CSV using formatter
        formatter = ReportFormatter()
        return formatter.format_zenrows_report(analysis_results)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        # Return empty CSV with header on error
        return "Date,Total Traces,Zenrows Errors,Error Rate\n"


def generate_zenrows_url_patterns_report(
    project_name: Optional[str] = None,
    single_date: Optional[datetime] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    top: Optional[int] = None,
    verbose: bool = False,
) -> str:
    """Generate zenrows URL pattern analysis report.

    Args:
        project_name: Project to analyze (optional, defaults to all projects)
        single_date: Single date to analyze (optional)
        start_date: Start of date range (optional)
        end_date: End of date range (optional)
        top: Limit results to top N entries (optional)
        verbose: Show detailed progress information

    Returns:
        Formatted report string showing domain and file type statistics
    """
    settings = get_settings()
    data_dir = Path(settings.output_dir)

    # Initialize the trace analyzer
    analyzer = TraceAnalyzer()

    # Set up progress tracking
    if verbose:
        progress_console = Console(stderr=True)
        progress_console.print("[blue]🔍 Starting zenrows URL pattern analysis...[/blue]")

    try:
        if project_name:
            # Single project analysis
            logger.info(f"Analyzing URL patterns for project: {project_name}")
            if verbose:
                progress_console.print(f"[green]📁 Analyzing project:[/green] {project_name}")

            url_results = analyzer.analyze_url_patterns(
                data_dir=data_dir,
                project_name=project_name,
                single_date=single_date,
                start_date=start_date,
                end_date=end_date,
            )

            if verbose and url_results:
                total_analyzed = url_results.get("total_analyzed", 0)
                domains_count = len(url_results.get("domains", {}))
                file_types_count = len(url_results.get("file_types", {}))
                progress_console.print("[cyan]📊 URL Pattern Analysis Summary:[/cyan]")
                progress_console.print(f"  Total errors analyzed: {total_analyzed:,}")
                progress_console.print(f"  Unique domains found: {domains_count}")
                progress_console.print(f"  File types found: {file_types_count}")
        else:
            # Multi-project analysis - aggregate across all projects
            project_dirs = [d for d in data_dir.iterdir() if d.is_dir()]
            if not project_dirs:
                logger.warning(f"No project directories found in {data_dir}")
                return "Type,Name,Count,Top Error Categories\n"

            if verbose:
                progress_console.print(
                    f"[green]📂 Found {len(project_dirs)} projects to analyze[/green]"
                )

            # Aggregate results across all projects
            all_domains = {}
            all_file_types = {}
            total_analyzed = 0
            traces_without_urls = 0
            total_zenrows_traces = 0

            # Use progress bar for multi-project analysis
            if verbose:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=progress_console,
                ) as progress:
                    task = progress.add_task("Analyzing projects", total=len(project_dirs))

                    for project_dir in project_dirs:
                        current_project = project_dir.name
                        logger.info(f"Analyzing URL patterns for project: {current_project}")
                        progress.update(task, description=f"Analyzing {current_project}")

                        # Analyze URL patterns for this project
                        project_results = analyzer.analyze_url_patterns(
                            data_dir=data_dir,
                            project_name=current_project,
                            single_date=single_date,
                            start_date=start_date,
                            end_date=end_date,
                        )

                        # Merge domain results
                        for domain, stats in project_results.get("domains", {}).items():
                            if domain not in all_domains:
                                all_domains[domain] = {
                                    "count": 0,
                                    "error_categories": {},
                                    "sample_urls": [],
                                }
                            all_domains[domain]["count"] += stats["count"]

                            # Merge error categories
                            for category, count in stats.get("error_categories", {}).items():
                                if category not in all_domains[domain]["error_categories"]:
                                    all_domains[domain]["error_categories"][category] = 0
                                all_domains[domain]["error_categories"][category] += count

                            # Merge sample URLs (limit to avoid memory bloat)
                            existing_urls = set(all_domains[domain]["sample_urls"])
                            new_urls = stats.get("sample_urls", [])
                            for url in new_urls:
                                if len(existing_urls) < 10:  # Same limit as in analysis
                                    existing_urls.add(url)
                            all_domains[domain]["sample_urls"] = list(existing_urls)

                        # Merge file type results
                        for file_type, stats in project_results.get("file_types", {}).items():
                            if file_type not in all_file_types:
                                all_file_types[file_type] = {"count": 0, "error_categories": {}}
                            all_file_types[file_type]["count"] += stats["count"]

                            # Merge error categories
                            for category, count in stats.get("error_categories", {}).items():
                                if category not in all_file_types[file_type]["error_categories"]:
                                    all_file_types[file_type]["error_categories"][category] = 0
                                all_file_types[file_type]["error_categories"][category] += count

                        # Update totals
                        total_analyzed += project_results.get("total_analyzed", 0)
                        traces_without_urls += project_results.get("traces_without_urls", 0)
                        total_zenrows_traces += project_results.get("total_zenrows_traces", 0)

                        progress.advance(task)
            else:
                # Non-verbose mode - just process without progress bar
                for project_dir in project_dirs:
                    current_project = project_dir.name
                    logger.info(f"Analyzing URL patterns for project: {current_project}")

                    # Analyze URL patterns for this project
                    project_results = analyzer.analyze_url_patterns(
                        data_dir=data_dir,
                        project_name=current_project,
                        single_date=single_date,
                        start_date=start_date,
                        end_date=end_date,
                    )

                    # Merge results (same logic as verbose mode)
                    for domain, stats in project_results.get("domains", {}).items():
                        if domain not in all_domains:
                            all_domains[domain] = {
                                "count": 0,
                                "error_categories": {},
                                "sample_urls": [],
                            }
                        all_domains[domain]["count"] += stats["count"]

                        for category, count in stats.get("error_categories", {}).items():
                            if category not in all_domains[domain]["error_categories"]:
                                all_domains[domain]["error_categories"][category] = 0
                            all_domains[domain]["error_categories"][category] += count

                        # Merge sample URLs (limit to avoid memory bloat)
                        existing_urls = set(all_domains[domain]["sample_urls"])
                        new_urls = stats.get("sample_urls", [])
                        for url in new_urls:
                            if len(existing_urls) < 10:  # Same limit as in analysis
                                existing_urls.add(url)
                        all_domains[domain]["sample_urls"] = list(existing_urls)

                    for file_type, stats in project_results.get("file_types", {}).items():
                        if file_type not in all_file_types:
                            all_file_types[file_type] = {"count": 0, "error_categories": {}}
                        all_file_types[file_type]["count"] += stats["count"]

                        for category, count in stats.get("error_categories", {}).items():
                            if category not in all_file_types[file_type]["error_categories"]:
                                all_file_types[file_type]["error_categories"][category] = 0
                            all_file_types[file_type]["error_categories"][category] += count

                    total_analyzed += project_results.get("total_analyzed", 0)
                    traces_without_urls += project_results.get("traces_without_urls", 0)
                    total_zenrows_traces += project_results.get("total_zenrows_traces", 0)

            # Sort by frequency (descending)
            all_domains = dict(
                sorted(all_domains.items(), key=lambda x: x[1]["count"], reverse=True)
            )
            all_file_types = dict(
                sorted(all_file_types.items(), key=lambda x: x[1]["count"], reverse=True)
            )

            # Create aggregated results structure
            url_results = {
                "domains": all_domains,
                "file_types": all_file_types,
                "total_analyzed": total_analyzed,
                "traces_without_urls": traces_without_urls,
                "total_zenrows_traces": total_zenrows_traces,
            }

            if verbose and url_results:
                domains_count = len(url_results.get("domains", {}))
                file_types_count = len(url_results.get("file_types", {}))
                progress_console.print("[cyan]📊 URL Pattern Analysis Summary:[/cyan]")
                progress_console.print(f"  Total errors analyzed: {total_analyzed:,}")
                progress_console.print(f"  Unique domains found: {domains_count}")
                progress_console.print(f"  File types found: {file_types_count}")

        # Format results using formatter
        formatter = ReportFormatter()
        return formatter.format_zenrows_url_patterns_report(url_results, top)

    except Exception as e:
        logger.error(f"URL pattern analysis failed: {e}")
        # Return empty report with header on error
        return "Type,Name,Count,Top Error Categories\n"


def generate_zenrows_detail_report(
    project_name: Optional[str] = None,
    report_date: Optional[datetime] = None,
    output_format: str = "text",
) -> str:
    """Generate detailed zenrows error report with hierarchical grouping.

    Args:
        project_name: Project to analyze (optional, defaults to all projects)
        report_date: Date to analyze (required)
        output_format: Output format - "text" or "json"

    Returns:
        Formatted report string (text or JSON)
    """
    settings = get_settings()
    data_dir = Path(settings.output_dir)

    # Import analysis functions
    from lse.analysis import (
        find_trace_files,
        parse_trace_file,
        build_zenrows_detail_hierarchy,
    )

    try:
        logger.info(f"Generating zenrows detail report for {report_date.strftime('%Y-%m-%d')}")

        # Handle single project or all projects
        projects_to_analyze = []
        if project_name:
            projects_to_analyze.append(project_name)
        else:
            # Get all project directories
            project_dirs = [d for d in data_dir.iterdir() if d.is_dir()]
            projects_to_analyze = [d.name for d in project_dirs]
            if not projects_to_analyze:
                logger.warning(f"No project directories found in {data_dir}")
                if output_format == "json":
                    formatter = ReportFormatter()
                    return formatter.format_zenrows_detail_json(
                        {}, report_date.strftime("%Y-%m-%d")
                    )
                else:
                    return "No project directories found.\n"

        # Collect traces from all projects
        all_traces = []
        for project in projects_to_analyze:
            logger.info(f"Analyzing project: {project}")

            # Find trace files for the specific date
            trace_files = find_trace_files(
                data_dir=data_dir,
                project_name=project,
                single_date=report_date,
            )

            # Parse all trace files
            for file_path in trace_files:
                trace_data = parse_trace_file(file_path)
                if trace_data:
                    all_traces.append(trace_data)

        if not all_traces:
            logger.warning(f"No traces found for date {report_date.strftime('%Y-%m-%d')}")
            if output_format == "json":
                formatter = ReportFormatter()
                return formatter.format_zenrows_detail_json(
                    {}, report_date.strftime("%Y-%m-%d"), project_name
                )
            else:
                return f"No traces found for {report_date.strftime('%Y-%m-%d')}.\n"

        # Build the hierarchical data structure
        logger.info(f"Building hierarchy from {len(all_traces)} traces")
        hierarchy = build_zenrows_detail_hierarchy(all_traces)

        # Format the output
        formatter = ReportFormatter()
        if output_format == "json":
            return formatter.format_zenrows_detail_json(
                hierarchy, report_date.strftime("%Y-%m-%d"), project_name
            )
        else:
            return formatter.format_zenrows_detail_text(hierarchy)

    except Exception as e:
        logger.error(f"Detail analysis failed: {e}")
        if output_format == "json":
            import json

            return json.dumps({"error": str(e)})
        else:
            return f"Error: {e}\n"


@report_app.command("zenrows-errors")
def zenrows_errors_command(
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Project name to analyze (defaults to all projects)"
    ),
    date: Optional[str] = typer.Option(
        None, "--date", "-d", help="Generate report for a specific date (YYYY-MM-DD)"
    ),
    start_date: Optional[str] = typer.Option(
        None, "--start-date", help="Start date for date range report (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = typer.Option(
        None, "--end-date", help="End date for date range report (YYYY-MM-DD)"
    ),
    debug_unknown_errors: bool = typer.Option(
        False,
        "--debug-unknown-errors",
        help="Enable logging of unknown/unclassified errors for analysis",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress and category statistics"
    ),
) -> None:
    """
    Generate error rate reports for zenrows_scraper failures with error categorization.

    Analyzes stored LangSmith trace data to calculate daily error rates
    for traces containing zenrows_scraper sub-traces with Error status.

    The report includes categorized error breakdowns:
    - http_404_not_found: Target URLs not found or websites offline
    - http_422_unprocessable: Anti-bot detection or content processing failures
    - read_timeout: Network timeouts (60-second limit exceeded)
    - http_413_too_large: Content exceeds size limits (especially PDFs)
    - http_400_bad_request: Invalid URLs or blocked content types
    - http_503_service_unavailable: CDN or server temporarily unavailable
    - unknown_errors: Unclassified error patterns

    CSV Output Format:
    Date,Total Traces,Zenrows Errors,Error Rate,http_404_not_found,http_422_unprocessable,read_timeout,http_413_too_large,http_400_bad_request,http_503_service_unavailable,unknown_errors

    Examples:

      # Single day report for specific project
      lse report zenrows-errors --project my-project --date 2025-08-29

      # Date range report with verbose output
      lse report zenrows-errors --project my-project --start-date 2025-08-01 --end-date 2025-08-31 --verbose

      # All projects with unknown error debugging
      lse report zenrows-errors --date 2025-08-29 --debug-unknown-errors
    """
    logger.info("Starting zenrows error report generation")

    try:
        # Validate that at least one date parameter is provided
        if not date and not (start_date or end_date):
            raise ValidationError(
                "At least one date parameter is required. "
                "Use --date for single day or --start-date/--end-date for range."
            )

        # Validate that single date and date range are not mixed
        if date and (start_date or end_date):
            raise ValidationError(
                "Cannot use --date with --start-date/--end-date. "
                "Use either single date OR date range parameters."
            )

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    # Enable unknown error logging if debug flag is set
    if debug_unknown_errors:
        logger.info(
            "Unknown error debugging enabled - errors will be logged to logs/unknown_errors.log"
        )
        # Set a flag that the categorization system can check
        import os

        os.environ["LSE_DEBUG_UNKNOWN_ERRORS"] = "1"

    try:
        # Parse and validate date parameters
        if date:
            # Single date mode with UTC timezone handling
            single_dt = validate_date(date)
            from datetime import timezone

            single_dt = single_dt.replace(tzinfo=timezone.utc)
            logger.info(f"Generating report for single date: {date} (UTC timezone)")

            report_output = generate_zenrows_report(
                project_name=project, single_date=single_dt, verbose=verbose
            )

        else:
            # Date range mode
            start_dt, end_dt = validate_date_range(start_date, end_date)

            if start_date and not end_date:
                raise ValidationError("--end-date is required when using --start-date")
            if end_date and not start_date:
                raise ValidationError("--start-date is required when using --end-date")

            logger.info(f"Generating report for date range: {start_date} to {end_date}")

            report_output = generate_zenrows_report(
                project_name=project, start_date=start_dt, end_date=end_dt, verbose=verbose
            )

        # Output CSV to stdout
        typer.echo(report_output)
        logger.info("Report generation completed successfully")

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@report_app.command("zenrows-url-patterns")
def zenrows_url_patterns_command(
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Project name to analyze (defaults to all projects)"
    ),
    date: Optional[str] = typer.Option(
        None, "--date", "-d", help="Generate report for a specific date (YYYY-MM-DD)"
    ),
    start_date: Optional[str] = typer.Option(
        None, "--start-date", help="Start date for date range report (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = typer.Option(
        None, "--end-date", help="End date for date range report (YYYY-MM-DD)"
    ),
    top: Optional[int] = typer.Option(
        None, "--top", help="Limit results to top N entries (e.g., --top 10)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed progress and analysis statistics"
    ),
) -> None:
    """
    Analyze URL patterns and domains from zenrows_scraper errors.

    Identifies problematic URL patterns, domains, and file types from ZenRows
    error data to help identify sites that need special handling or configuration.

    The analysis includes:
    - Domain analysis: Which domains are causing the most errors
    - File type analysis: Error patterns by file type (PDFs, images, APIs, HTML)
    - Error categorization: Top error categories for each domain/file type
    - Frequency ranking: Results sorted by error count (most problematic first)

    Output Format:
    Type,Name,Count,Top Error Categories
    domain,example.com,45,http_404_not_found(30);http_422_unprocessable(15)
    file_type,pdf,32,http_413_too_large(20);http_404_not_found(12)

    Examples:

      # Single day analysis for specific project
      lse report zenrows-url-patterns --project my-project --date 2025-08-29

      # Date range analysis with top 20 results
      lse report zenrows-url-patterns --start-date 2025-08-01 --end-date 2025-08-31 --top 20

      # All projects with verbose output
      lse report zenrows-url-patterns --date 2025-08-29 --verbose --top 10
    """
    logger.info("Starting zenrows URL pattern analysis")

    try:
        # Validate that at least one date parameter is provided
        if not date and not (start_date or end_date):
            raise ValidationError(
                "At least one date parameter is required. "
                "Use --date for single day or --start-date/--end-date for range."
            )

        # Validate that single date and date range are not mixed
        if date and (start_date or end_date):
            raise ValidationError(
                "Cannot use --date with --start-date/--end-date. "
                "Use either single date OR date range parameters."
            )

        # Validate top parameter
        if top is not None and top <= 0:
            raise ValidationError("--top must be a positive number")

        # Parse and validate date parameters
        if date:
            # Single date mode with UTC timezone handling
            single_dt = validate_date(date)
            from datetime import timezone

            single_dt = single_dt.replace(tzinfo=timezone.utc)
            logger.info(f"Generating URL pattern report for single date: {date} (UTC timezone)")

            report_output = generate_zenrows_url_patterns_report(
                project_name=project, single_date=single_dt, top=top, verbose=verbose
            )

        else:
            # Date range mode
            start_dt, end_dt = validate_date_range(start_date, end_date)

            if start_date and not end_date:
                raise ValidationError("--end-date is required when using --start-date")
            if end_date and not start_date:
                raise ValidationError("--start-date is required when using --end-date")

            logger.info(f"Generating URL pattern report for date range: {start_date} to {end_date}")

            report_output = generate_zenrows_url_patterns_report(
                project_name=project, start_date=start_dt, end_date=end_dt, top=top, verbose=verbose
            )

        # Output report to stdout
        typer.echo(report_output)
        logger.info("URL pattern analysis completed successfully")

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    except Exception as e:
        logger.error(f"URL pattern analysis failed: {e}")
        typer.echo(f"Error: URL pattern analysis failed: {e}", err=True)
        raise typer.Exit(1)


@report_app.command("zenrows-detail")
def zenrows_detail_command(
    date: str = typer.Option(..., "--date", "-d", help="Date to generate report for (YYYY-MM-DD)"),
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Project name to analyze (defaults to all projects)"
    ),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text or json"),
) -> None:
    """
    Generate detailed zenrows error report with hierarchical grouping.

    Provides a hierarchical view of zenrows_scraper errors organized by
    cryptocurrency symbol and root trace, enabling detailed error analysis
    across different cryptocurrencies and trace contexts.

    The report shows:
    - Cryptocurrency symbols (BTC, ETH, etc.)
    - Root traces containing errors
    - Specific error messages from zenrows_scraper

    Examples:

      # Detailed report for specific project
      lse report zenrows-detail --date 2025-08-29 --project my-project

      # All projects with JSON output
      lse report zenrows-detail --date 2025-08-29 --format json
    """
    logger.info("Starting zenrows detail report generation")

    try:
        # Validate format parameter
        if format not in ["text", "json"]:
            raise ValidationError(f"Invalid format '{format}'. Must be 'text' or 'json'.")

        # Parse and validate date parameter
        report_dt = validate_date(date)
        from datetime import timezone

        report_dt = report_dt.replace(tzinfo=timezone.utc)
        logger.info(f"Generating detail report for date: {date} (UTC timezone)")

        report_output = generate_zenrows_detail_report(
            project_name=project, report_date=report_dt, output_format=format
        )

        # Output report to stdout
        typer.echo(report_output)
        logger.info("Detail report generation completed successfully")

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Detail report generation failed: {e}")
        typer.echo(f"Error: Detail report generation failed: {e}", err=True)
        raise typer.Exit(1)
