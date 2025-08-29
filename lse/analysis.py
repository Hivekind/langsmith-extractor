"""Trace analysis engine for processing LangSmith trace data."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from lse.exceptions import ValidationError

logger = logging.getLogger("lse.analysis")


def find_trace_files(
    data_dir: Path,
    project_name: str,
    single_date: Optional[datetime] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[Path]:
    """Find trace files for the specified date(s).

    Args:
        data_dir: Base directory containing trace data
        project_name: Name of the project to search in
        single_date: Single date to search for (optional)
        start_date: Start of date range (optional)
        end_date: End of date range (optional)

    Returns:
        List of trace file paths

    Raises:
        ValidationError: If no date parameters provided
    """
    if not single_date and not (start_date or end_date):
        raise ValidationError("At least one date parameter is required")

    project_dir = data_dir / project_name
    if not project_dir.exists():
        logger.warning(f"Project directory {project_dir} does not exist")
        return []

    trace_files = []

    if single_date:
        # Single date mode - only look in the specific date directory
        date_str = single_date.strftime("%Y-%m-%d")
        date_dir = project_dir / date_str
        if date_dir.exists():
            for trace_file in date_dir.glob("*.json"):
                if not trace_file.name.startswith("_"):  # Skip summary files
                    trace_files.append(trace_file)
        else:
            logger.warning(f"No data found for date {date_str} in project {project_name}")
    else:
        # Date range mode
        current_date = start_date or end_date
        end_search_date = end_date or start_date

        while current_date <= end_search_date:
            date_str = current_date.strftime("%Y-%m-%d")
            date_dir = project_dir / date_str
            if date_dir.exists():
                for trace_file in date_dir.glob("*.json"):
                    if not trace_file.name.startswith("_"):
                        trace_files.append(trace_file)

            # Move to next day
            from datetime import timedelta

            current_date += timedelta(days=1)

    logger.info(f"Found {len(trace_files)} trace files for analysis")
    return trace_files


def parse_trace_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Parse a JSON trace file.

    Args:
        file_path: Path to the trace file

    Returns:
        Parsed trace data or None if parsing fails
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract the trace data
        trace = data.get("trace")
        if not trace:
            logger.warning(f"No 'trace' key found in {file_path}")
            return None

        return trace

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON file {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading {file_path}: {e}")
        return None


def extract_zenrows_errors(trace_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract zenrows_scraper errors from trace data.

    Recursively searches through child runs to find sub-traces with name
    matching 'zenrows_scraper' and status indicating error.

    Args:
        trace_data: Parsed trace data

    Returns:
        List of error records containing details about zenrows failures
    """
    errors = []

    def search_child_runs(runs: List[Dict[str, Any]]) -> None:
        """Recursively search child runs for zenrows errors."""
        if not runs:
            return

        for run in runs:
            if not isinstance(run, dict):
                continue

            # Check if this is a zenrows_scraper run with error status
            name = run.get("name", "").lower()
            status = run.get("status", "").lower()

            if "zenrows_scraper" in name and status == "error":
                error_record = {
                    "id": run.get("id"),
                    "name": run.get("name"),
                    "status": run.get("status"),
                    "error": run.get("error", "Unknown error"),
                    "start_time": run.get("start_time"),
                    "end_time": run.get("end_time"),
                }
                errors.append(error_record)

            # Recursively search nested child runs
            nested_runs = run.get("child_runs")
            if nested_runs:
                search_child_runs(nested_runs)

    # Start search from top-level child runs
    child_runs = trace_data.get("child_runs")
    if child_runs:
        search_child_runs(child_runs)

    return errors


def group_by_date(traces: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group traces by their date.

    Args:
        traces: List of trace data

    Returns:
        Dictionary with dates as keys and lists of traces as values
    """
    grouped = {}

    for trace in traces:
        start_time_str = trace.get("start_time")
        if not start_time_str:
            logger.warning(f"Trace {trace.get('id')} missing start_time, skipping")
            continue

        try:
            # Parse various datetime formats
            if "T" in start_time_str:
                # ISO format: 2025-08-29T06:44:12.622037Z
                start_time_str = start_time_str.replace("Z", "").split("T")[0]
            else:
                # Space format: 2025-08-29 06:44:12.622037
                start_time_str = start_time_str.split(" ")[0]

            date_key = start_time_str

            if date_key not in grouped:
                grouped[date_key] = []
            grouped[date_key].append(trace)

        except Exception as e:
            logger.warning(
                f"Failed to parse start_time '{start_time_str}' for trace {trace.get('id')}: {e}"
            )
            continue

    return grouped


def calculate_error_rates(
    daily_data: Dict[str, Dict[str, int]],
) -> Dict[str, Dict[str, Union[int, float]]]:
    """Calculate error rates for daily trace data.

    Args:
        daily_data: Dictionary with date keys and trace/error counts

    Returns:
        Dictionary with error rates added to each day's data
    """
    result = {}

    for date_key, data in daily_data.items():
        total_traces = data["total_traces"]
        zenrows_errors = data["zenrows_errors"]

        if total_traces == 0:
            error_rate = 0.0
        else:
            error_rate = round((zenrows_errors / total_traces) * 100, 1)

        result[date_key] = {
            "total_traces": total_traces,
            "zenrows_errors": zenrows_errors,
            "error_rate": error_rate,
        }

    return result


class TraceAnalyzer:
    """Main class for analyzing trace data and generating reports."""

    def __init__(self):
        """Initialize the trace analyzer."""
        self.logger = logging.getLogger("lse.analysis.TraceAnalyzer")

    def analyze_zenrows_errors(
        self,
        data_dir: Path,
        project_name: str,
        single_date: Optional[datetime] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Dict[str, Union[int, float]]]:
        """Analyze zenrows_scraper errors in trace data.

        Args:
            data_dir: Base directory containing trace data
            project_name: Name of the project to analyze
            single_date: Single date to analyze (optional)
            start_date: Start of date range (optional)
            end_date: End of date range (optional)

        Returns:
            Dictionary with daily error statistics
        """
        self.logger.info("Starting zenrows error analysis")

        # Find relevant trace files
        trace_files = find_trace_files(
            data_dir=data_dir,
            project_name=project_name,
            single_date=single_date,
            start_date=start_date,
            end_date=end_date,
        )

        if not trace_files:
            self.logger.warning("No trace files found for analysis")
            return {}

        # Parse all trace files
        traces = []
        for file_path in trace_files:
            trace_data = parse_trace_file(file_path)
            if trace_data:
                traces.append(trace_data)

        if not traces:
            self.logger.warning("No valid traces found after parsing")
            return {}

        # Group traces by date
        grouped_traces = group_by_date(traces)

        # Filter by requested dates if specified
        if single_date:
            requested_date = single_date.strftime("%Y-%m-%d")
            grouped_traces = {k: v for k, v in grouped_traces.items() if k == requested_date}
        elif start_date or end_date:
            start_str = start_date.strftime("%Y-%m-%d") if start_date else "0000-00-00"
            end_str = end_date.strftime("%Y-%m-%d") if end_date else "9999-12-31"
            grouped_traces = {k: v for k, v in grouped_traces.items() if start_str <= k <= end_str}

        # Analyze each day
        daily_data = {}
        for date_key, date_traces in grouped_traces.items():
            total_traces = len(date_traces)
            total_errors = 0

            # Count zenrows errors for this date
            for trace in date_traces:
                errors = extract_zenrows_errors(trace)
                total_errors += len(errors)

            daily_data[date_key] = {"total_traces": total_traces, "zenrows_errors": total_errors}

        # Calculate error rates
        result = calculate_error_rates(daily_data)

        self.logger.info(f"Analysis completed for {len(result)} days")
        return result
