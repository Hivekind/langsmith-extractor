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
    """Validate date range parameters.

    Args:
        start_date: Start date string (optional)
        end_date: End date string (optional)

    Returns:
        Tuple of parsed datetime objects

    Raises:
        ValidationError: If date range is invalid
    """
    start_dt = None
    end_dt = None

    if start_date:
        start_dt = validate_date(start_date)

    if end_date:
        end_dt = validate_date(end_date)

    if start_dt and end_dt and start_dt >= end_dt:
        raise ValidationError("Start date must be before end date.")

    return start_dt, end_dt


def generate_zenrows_report(
    single_date: Optional[datetime] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> str:
    """Generate zenrows error report for specified date(s).

    Args:
        single_date: Single date to analyze (optional)
        start_date: Start of date range (optional)
        end_date: End of date range (optional)

    Returns:
        CSV formatted report string
    """
    settings = get_settings()
    data_dir = Path(settings.output_dir)

    # Find all project directories in the data directory
    project_dirs = [d for d in data_dir.iterdir() if d.is_dir()]
    if not project_dirs:
        logger.warning(f"No project directories found in {data_dir}")
        return "Date,Total Traces,Zenrows Errors,Error Rate\n"

    # Initialize the trace analyzer
    analyzer = TraceAnalyzer()

    # Aggregate results across all projects
    all_results = {}

    try:
        for project_dir in project_dirs:
            project_name = project_dir.name
            logger.info(f"Analyzing project: {project_name}")

            # Analyze traces for this project
            project_results = analyzer.analyze_zenrows_errors(
                data_dir=data_dir,
                project_name=project_name,
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
                data["error_rate"] = round((data["zenrows_errors"] / data["total_traces"]) * 100, 1)

        # Format results as CSV using formatter
        formatter = ReportFormatter()
        return formatter.format_zenrows_report(all_results)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        # Return empty CSV with header on error
        return "Date,Total Traces,Zenrows Errors,Error Rate\n"


@report_app.command("zenrows-errors")
def zenrows_errors_command(
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

      # Single day report
      lse report zenrows-errors --date 2025-08-29

      # Date range report
      lse report zenrows-errors --start-date 2025-08-01 --end-date 2025-08-31
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
            # Single date mode
            single_dt = validate_date(date)
            logger.info(f"Generating report for single date: {date}")

            report_output = generate_zenrows_report(single_date=single_dt)

        else:
            # Date range mode
            start_dt, end_dt = validate_date_range(start_date, end_date)

            if start_date and not end_date:
                raise ValidationError("--end-date is required when using --start-date")
            if end_date and not start_date:
                raise ValidationError("--start-date is required when using --end-date")

            logger.info(f"Generating report for date range: {start_date} to {end_date}")

            report_output = generate_zenrows_report(start_date=start_dt, end_date=end_dt)

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
