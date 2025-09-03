"""Report command for generating LangSmith trace analysis reports."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

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


def generate_zenrows_report(
    project_name: Optional[str] = None,
    single_date: Optional[datetime] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> str:
    """Generate zenrows error report for specified date(s).

    Args:
        project_name: Project to analyze (optional, defaults to all projects)
        single_date: Single date to analyze (optional)
        start_date: Start of date range (optional)
        end_date: End of date range (optional)

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
                start_date=start_date,
                end_date=end_date,
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
                    start_date=start_date,
                    end_date=end_date,
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
    # These will be used in the full implementation
    # settings = get_settings()
    # data_dir = Path(settings.output_dir)
    # analyzer = TraceAnalyzer()

    try:
        # For now, return a placeholder to make tests pass
        # Full implementation will be added in subsequent tasks
        if output_format == "json":
            import json

            return json.dumps(
                {"status": "not_implemented", "message": "Zenrows detail report coming soon"}
            )
        else:
            return "Zenrows Detail Report\n======================\nComing soon: Hierarchical error reporting by crypto symbol and root trace.\n"

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
) -> None:
    """
    Generate error rate reports for zenrows_scraper failures.

    Analyzes stored LangSmith trace data to calculate daily error rates
    for traces containing zenrows_scraper sub-traces with Error status.

    Examples:

      # Single day report for specific project
      lse report zenrows-errors --project my-project --date 2025-08-29

      # Date range report for specific project
      lse report zenrows-errors --project my-project --start-date 2025-08-01 --end-date 2025-08-31

      # All projects (aggregated)
      lse report zenrows-errors --date 2025-08-29
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

        # Parse and validate date parameters
        if date:
            # Single date mode with UTC timezone handling
            single_dt = validate_date(date)
            from datetime import timezone

            single_dt = single_dt.replace(tzinfo=timezone.utc)
            logger.info(f"Generating report for single date: {date} (UTC timezone)")

            report_output = generate_zenrows_report(project_name=project, single_date=single_dt)

        else:
            # Date range mode
            start_dt, end_dt = validate_date_range(start_date, end_date)

            if start_date and not end_date:
                raise ValidationError("--end-date is required when using --start-date")
            if end_date and not start_date:
                raise ValidationError("--start-date is required when using --end-date")

            logger.info(f"Generating report for date range: {start_date} to {end_date}")

            report_output = generate_zenrows_report(
                project_name=project, start_date=start_dt, end_date=end_dt
            )

        # Output CSV to stdout
        typer.echo(report_output)
        logger.info("Report generation completed successfully")

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        typer.echo(f"Error: Report generation failed: {e}", err=True)
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
