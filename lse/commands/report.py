"""Report command for generating LangSmith trace analysis reports."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from lse.analysis import TraceAnalyzer, DatabaseTraceAnalyzer
from lse.config import get_settings
from lse.database import create_database_manager
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


def generate_zenrows_report(
    project_name: Optional[str] = None,
    single_date: Optional[datetime] = None,
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

    try:
        if project_name:
            # Single project analysis
            logger.info(f"Analyzing project: {project_name}")

            analysis_results = analyzer.analyze_zenrows_errors(
                data_dir=data_dir,
                project_name=project_name,
                single_date=single_date,
            )
        else:
            # Multi-project analysis - aggregate across all projects
            project_dirs = [d for d in data_dir.iterdir() if d.is_dir()]
            if not project_dirs:
                logger.warning(f"No project directories found in {data_dir}")
                return "Date,Total Traces,Zenrows Errors,Error Rate\n"

            # Aggregate results across all projects
            all_results = {}

            for project_dir in project_dirs:
                current_project = project_dir.name
                logger.info(f"Analyzing project: {current_project}")

                # Analyze traces for this project
                project_results = analyzer.analyze_zenrows_errors(
                    data_dir=data_dir,
                    project_name=current_project,
                    single_date=single_date,
                )

                # Merge results by date
                for date_key, data in project_results.items():
                    if date_key in all_results:
                        # Aggregate data for this date across projects
                        all_results[date_key]["total_traces"] += data["total_traces"]
                        all_results[date_key]["zenrows_errors"] += data["zenrows_errors"]
                    else:
                        all_results[date_key] = data.copy()

            # Recalculate error rates after aggregation
            for date_key, data in all_results.items():
                if data["total_traces"] == 0:
                    data["error_rate"] = 0.0
                else:
                    data["error_rate"] = round(
                        (data["zenrows_errors"] / data["total_traces"]) * 100, 1
                    )

            analysis_results = all_results

        # Format results as CSV using formatter
        formatter = ReportFormatter()
        return formatter.format_zenrows_report(analysis_results)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        # Return empty CSV with header on error
        return "Date,Total Traces,Zenrows Errors,Error Rate\n"


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


async def generate_zenrows_report_from_db(
    project_name: Optional[str] = None,
    report_date: Optional[datetime] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> str:
    """Generate zenrows error report from database for specified date(s).

    Args:
        project_name: Project to analyze (optional, defaults to all projects)
        report_date: Single date to analyze
        start_date: Start date for range analysis
        end_date: End date for range analysis

    Returns:
        CSV formatted report string
    """
    try:
        # Create database manager
        db_manager = await create_database_manager()

        try:
            # Initialize database analyzer
            analyzer = DatabaseTraceAnalyzer(db_manager)

            logger.info("Analyzing zenrows errors from database")
            analysis_results = await analyzer.analyze_zenrows_errors_from_db(
                project_name=project_name,
                report_date=report_date,
                start_date=start_date,
                end_date=end_date,
            )

            # Format results as CSV using formatter
            formatter = ReportFormatter()
            return formatter.format_zenrows_report(analysis_results)

        finally:
            await db_manager.close()

    except Exception as e:
        logger.error(f"Database zenrows analysis failed: {e}")
        # Return empty CSV with header on error
        return "Date,Total Traces,Zenrows Errors,Error Rate\n"


async def generate_zenrows_detail_report_from_db(
    project_name: Optional[str] = None,
    report_date: Optional[datetime] = None,
    output_format: str = "text",
) -> str:
    """Generate detailed zenrows error report from database with hierarchical grouping.

    Args:
        project_name: Project to analyze (optional, defaults to all projects)
        report_date: Date to analyze (required)
        output_format: Output format - "text" or "json"

    Returns:
        Formatted report string (text or JSON)
    """
    try:
        # Create database manager
        db_manager = await create_database_manager()

        try:
            logger.info(
                f"Generating zenrows detail report from database for {report_date.strftime('%Y-%m-%d')}"
            )

            # Initialize database analyzer
            analyzer = DatabaseTraceAnalyzer(db_manager)

            if project_name:
                # Single project analysis
                logger.info(f"Analyzing project from database: {project_name}")
                hierarchy = await analyzer.generate_zenrows_detail_from_db(
                    project_name=project_name,
                    report_date=report_date,
                )
            else:
                # Multi-project analysis - get all projects from database
                async with db_manager.get_session() as session:
                    from sqlalchemy import text

                    result = await session.execute(
                        text(
                            "SELECT DISTINCT project FROM runs WHERE run_date = :date ORDER BY project"
                        ),
                        {
                            "date": report_date.date()
                            if hasattr(report_date, "date")
                            else report_date
                        },
                    )
                    projects = [row[0] for row in result.fetchall()]

                if not projects:
                    logger.warning(f"No projects found in database for date {report_date}")
                    if output_format == "json":
                        formatter = ReportFormatter()
                        return formatter.format_zenrows_detail_json(
                            {}, report_date.strftime("%Y-%m-%d")
                        )
                    else:
                        return "No projects found in database.\n"

                # Collect hierarchies from all projects and merge
                combined_hierarchy = {}

                for project in projects:
                    logger.info(f"Analyzing project from database: {project}")

                    project_hierarchy = await analyzer.generate_zenrows_detail_from_db(
                        project_name=project,
                        report_date=report_date,
                    )

                    # Merge project hierarchy into combined hierarchy
                    for crypto, traces in project_hierarchy.items():
                        if crypto not in combined_hierarchy:
                            combined_hierarchy[crypto] = {}
                        combined_hierarchy[crypto].update(traces)

                hierarchy = combined_hierarchy

            if not hierarchy:
                logger.warning(
                    f"No zenrows errors found for date {report_date.strftime('%Y-%m-%d')}"
                )
                if output_format == "json":
                    formatter = ReportFormatter()
                    return formatter.format_zenrows_detail_json(
                        {}, report_date.strftime("%Y-%m-%d"), project_name
                    )
                else:
                    return f"No zenrows errors found for {report_date.strftime('%Y-%m-%d')}.\n"

            # Format the output
            formatter = ReportFormatter()
            if output_format == "json":
                return formatter.format_zenrows_detail_json(
                    hierarchy, report_date.strftime("%Y-%m-%d"), project_name
                )
            else:
                return formatter.format_zenrows_detail_text(hierarchy)

        finally:
            await db_manager.close()

    except Exception as e:
        logger.error(f"Database detail analysis failed: {e}")
        if output_format == "json":
            import json

            return json.dumps({"error": str(e)})
        else:
            return f"Error: {e}\n"


@report_app.command("zenrows-errors")
def zenrows_errors_command(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Single date (YYYY-MM-DD)"),
    start_date: Optional[str] = typer.Option(
        None, "--start-date", help="Start date for range (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = typer.Option(
        None, "--end-date", help="End date for range (YYYY-MM-DD)"
    ),
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Project name to analyze (defaults to all projects)"
    ),
) -> None:
    """
    Generate error rate reports for zenrows_scraper failures.

    Analyzes stored LangSmith trace data to calculate daily error rates
    for traces containing zenrows_scraper sub-traces with Error status.

    Examples:

      # Single day report for specific project
      lse report zenrows-errors --date 2025-08-29 --project my-project

      # All projects (aggregated) for single date
      lse report zenrows-errors --date 2025-08-29

      # Date range report for specific project
      lse report zenrows-errors --start-date 2025-08-29 --end-date 2025-09-05 --project my-project

      # Date range report for all projects
      lse report zenrows-errors --start-date 2025-08-29 --end-date 2025-09-05
    """
    logger.info("Starting zenrows error report generation")

    try:
        # Validate date parameters
        if date and (start_date or end_date):
            raise ValidationError(
                "Cannot specify both single date and date range. Use either --date OR --start-date/--end-date"
            )

        if (start_date and not end_date) or (end_date and not start_date):
            raise ValidationError("Both --start-date and --end-date required for range analysis")

        if not date and not (start_date and end_date):
            raise ValidationError(
                "Either single date (--date) or date range (--start-date/--end-date) required"
            )

        # Parse and validate dates
        from datetime import timezone

        report_dt = None
        start_dt = None
        end_dt = None

        if date:
            report_dt = validate_date(date).replace(tzinfo=timezone.utc)
            logger.info(f"Generating report for date: {date} (UTC timezone)")
        else:
            start_dt = validate_date(start_date).replace(tzinfo=timezone.utc)
            end_dt = validate_date(end_date).replace(tzinfo=timezone.utc)
            logger.info(
                f"Generating report for date range: {start_date} to {end_date} (UTC timezone)"
            )

        # Generate report using updated database method
        report_output = asyncio.run(
            generate_zenrows_report_from_db(
                project_name=project,
                report_date=report_dt,
                start_date=start_dt,
                end_date=end_dt,
            )
        )

        # Output CSV to stdout
        typer.echo(report_output)
        logger.info("Zenrows error report generation completed successfully")

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Zenrows error report generation failed: {e}")
        typer.echo(f"Error: Zenrows error report generation failed: {e}", err=True)
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

        report_output = asyncio.run(
            generate_zenrows_detail_report_from_db(
                project_name=project, report_date=report_dt, output_format=format
            )
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


async def generate_is_available_report_from_db(
    project_name: Optional[str] = None,
    report_date: Optional[datetime] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> str:
    """Generate is_available report from database for specified date(s).

    Args:
        project_name: Project to analyze (optional, defaults to all projects)
        report_date: Single date to analyze
        start_date: Start date for range analysis
        end_date: End date for range analysis

    Returns:
        CSV formatted report string
    """
    try:
        # Create database manager
        db_manager = await create_database_manager()

        try:
            # Initialize database analyzer
            analyzer = DatabaseTraceAnalyzer(db_manager)

            logger.info("Analyzing is_available data from database")
            analysis_results = await analyzer.analyze_is_available_from_db(
                project_name=project_name,
                report_date=report_date,
                start_date=start_date,
                end_date=end_date,
            )

            # Format results as CSV using formatter
            formatter = ReportFormatter()
            return formatter.format_availability_report(analysis_results)

        finally:
            await db_manager.close()

    except Exception as e:
        logger.error(f"Database availability analysis failed: {e}")
        # Return empty CSV with header on error
        return "date,Trace count,is_available = false count,percentage\n"


@report_app.command("is_available")
def is_available_command(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Single date (YYYY-MM-DD)"),
    start_date: Optional[str] = typer.Option(
        None, "--start-date", help="Start date for range (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = typer.Option(
        None, "--end-date", help="End date for range (YYYY-MM-DD)"
    ),
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Project name to analyze (defaults to all projects)"
    ),
) -> None:
    """
    Generate availability failure reports showing is_available=false patterns.

    Analyzes stored LangSmith trace data to calculate availability failure rates
    for traces where website_analysis.is_available was false.

    Examples:

      # Single day report for specific project
      lse report is_available --date 2025-09-01 --project my-project

      # All projects (aggregated) for single date
      lse report is_available --date 2025-09-01

      # Date range report for specific project
      lse report is_available --start-date 2025-09-01 --end-date 2025-09-07 --project my-project

      # Date range report for all projects
      lse report is_available --start-date 2025-09-01 --end-date 2025-09-07
    """
    logger.info("Starting is_available report generation")

    try:
        # Validate date parameters
        if date and (start_date or end_date):
            raise ValidationError(
                "Cannot specify both single date and date range. Use either --date OR --start-date/--end-date"
            )

        if (start_date and not end_date) or (end_date and not start_date):
            raise ValidationError("Both --start-date and --end-date required for range analysis")

        if not date and not (start_date and end_date):
            raise ValidationError(
                "Either single date (--date) or date range (--start-date/--end-date) required"
            )

        # Parse and validate dates
        from datetime import timezone

        report_dt = None
        start_dt = None
        end_dt = None

        if date:
            report_dt = validate_date(date).replace(tzinfo=timezone.utc)
            logger.info(f"Generating report for date: {date} (UTC timezone)")
        else:
            start_dt = validate_date(start_date).replace(tzinfo=timezone.utc)
            end_dt = validate_date(end_date).replace(tzinfo=timezone.utc)
            logger.info(
                f"Generating report for date range: {start_date} to {end_date} (UTC timezone)"
            )

        # Generate report using database
        report_output = asyncio.run(
            generate_is_available_report_from_db(
                project_name=project,
                report_date=report_dt,
                start_date=start_dt,
                end_date=end_dt,
            )
        )

        # Output CSV to stdout
        typer.echo(report_output)
        logger.info("Availability report generation completed successfully")

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Availability report generation failed: {e}")
        typer.echo(f"Error: Availability report generation failed: {e}", err=True)
        raise typer.Exit(1)


async def generate_scraping_insights_report_from_db(
    project_name: Optional[str] = None,
    report_date: Optional[datetime] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> str:
    """Generate scraping insights report from database for specified date(s).

    Args:
        project_name: Project to analyze (optional, defaults to all projects)
        report_date: Single date to analyze
        start_date: Start date for range analysis
        end_date: End date for range analysis

    Returns:
        CSV formatted report string
    """
    try:
        # Create database manager
        db_manager = await create_database_manager()

        try:
            # Initialize database analyzer
            analyzer = DatabaseTraceAnalyzer(db_manager)

            logger.info("Analyzing scraping insights from database")
            analysis_results = await analyzer.analyze_scraping_insights_from_db(
                project_name=project_name,
                report_date=report_date,
                start_date=start_date,
                end_date=end_date,
            )

            # Format results as CSV using formatter
            formatter = ReportFormatter()
            return formatter.format_scraping_insights_report(analysis_results)

        finally:
            await db_manager.close()

    except Exception as e:
        logger.error(f"Database scraping insights analysis failed: {e}")
        # Return empty CSV with header on error
        return "date,trace count,zenrows errors count,zenrows errors percentage,is_available false count,is_available false percentage\n"


@report_app.command("scraping-insights")
def scraping_insights_command(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Single date (YYYY-MM-DD)"),
    start_date: Optional[str] = typer.Option(
        None, "--start-date", help="Start date for range (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = typer.Option(
        None, "--end-date", help="End date for range (YYYY-MM-DD)"
    ),
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Project name to analyze (defaults to all projects)"
    ),
) -> None:
    """
    Generate unified scraping health reports combining availability and zenrows error metrics.

    Analyzes stored LangSmith trace data to provide comprehensive scraping health insights,
    combining both website availability failures and zenrows_scraper errors in a single report.

    Examples:

      # Single day unified report for specific project
      lse report scraping-insights --date 2025-09-01 --project my-project

      # All projects (aggregated) for single date
      lse report scraping-insights --date 2025-09-01

      # Date range unified report for specific project
      lse report scraping-insights --start-date 2025-09-01 --end-date 2025-09-07 --project my-project

      # Date range unified report for all projects
      lse report scraping-insights --start-date 2025-09-01 --end-date 2025-09-07
    """
    logger.info("Starting scraping insights report generation")

    try:
        # Validate date parameters
        if date and (start_date or end_date):
            raise ValidationError(
                "Cannot specify both single date and date range. Use either --date OR --start-date/--end-date"
            )

        if (start_date and not end_date) or (end_date and not start_date):
            raise ValidationError("Both --start-date and --end-date required for range analysis")

        if not date and not (start_date and end_date):
            raise ValidationError(
                "Either single date (--date) or date range (--start-date/--end-date) required"
            )

        # Parse and validate dates
        from datetime import timezone

        report_dt = None
        start_dt = None
        end_dt = None

        if date:
            report_dt = validate_date(date).replace(tzinfo=timezone.utc)
            logger.info(f"Generating unified report for date: {date} (UTC timezone)")
        else:
            start_dt = validate_date(start_date).replace(tzinfo=timezone.utc)
            end_dt = validate_date(end_date).replace(tzinfo=timezone.utc)
            logger.info(
                f"Generating unified report for date range: {start_date} to {end_date} (UTC timezone)"
            )

        # Generate unified report using database
        report_output = asyncio.run(
            generate_scraping_insights_report_from_db(
                project_name=project,
                report_date=report_dt,
                start_date=start_dt,
                end_date=end_dt,
            )
        )

        # Output CSV to stdout
        typer.echo(report_output)
        logger.info("Scraping insights report generation completed successfully")

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Scraping insights report generation failed: {e}")
        typer.echo(f"Error: Scraping insights report generation failed: {e}", err=True)
        raise typer.Exit(1)
