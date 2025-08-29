"""Output formatting utilities for trace analysis reports."""

import logging
from typing import Dict, Union

logger = logging.getLogger("lse.formatters")


def format_csv_report(
    analysis_data: Dict[str, Dict[str, Union[int, float]]], title: str = "Trace Analysis Report"
) -> str:
    """Format analysis data as CSV report.

    Args:
        analysis_data: Dictionary with date keys and analysis results
        title: Optional title for logging (not included in output)

    Returns:
        CSV formatted string with headers and data rows
    """
    logger.info(f"Formatting CSV report: {title}")

    # CSV header
    header = "Date,Total Traces,Zenrows Errors,Error Rate"
    lines = [header]

    # Sort dates for consistent output
    for date_key in sorted(analysis_data.keys()):
        data = analysis_data[date_key]

        # Format error rate as percentage with 1 decimal place
        error_rate = f"{data['error_rate']:.1f}%"

        # Create CSV row
        line = f"{date_key},{data['total_traces']},{data['zenrows_errors']},{error_rate}"
        lines.append(line)

    # Join with newlines and add final newline
    result = "\n".join(lines) + "\n"

    logger.debug(f"Generated CSV report with {len(lines) - 1} data rows")
    return result


def format_summary_stats(
    analysis_data: Dict[str, Dict[str, Union[int, float]]],
) -> Dict[str, Union[int, float]]:
    """Calculate summary statistics across all analyzed dates.

    Args:
        analysis_data: Dictionary with date keys and analysis results

    Returns:
        Summary statistics dictionary
    """
    if not analysis_data:
        return {
            "total_days": 0,
            "total_traces": 0,
            "total_zenrows_errors": 0,
            "overall_error_rate": 0.0,
            "worst_day": None,
            "best_day": None,
        }

    total_traces = sum(data["total_traces"] for data in analysis_data.values())
    total_errors = sum(data["zenrows_errors"] for data in analysis_data.values())

    overall_error_rate = 0.0
    if total_traces > 0:
        overall_error_rate = round((total_errors / total_traces) * 100, 1)

    # Find best and worst days
    worst_day = None
    best_day = None
    worst_rate = -1
    best_rate = 101  # Start with impossible value

    for date_key, data in analysis_data.items():
        rate = data["error_rate"]
        if rate > worst_rate:
            worst_rate = rate
            worst_day = date_key
        if rate < best_rate:
            best_rate = rate
            best_day = date_key

    return {
        "total_days": len(analysis_data),
        "total_traces": total_traces,
        "total_zenrows_errors": total_errors,
        "overall_error_rate": overall_error_rate,
        "worst_day": worst_day,
        "best_day": best_day,
    }


class ReportFormatter:
    """Class for formatting various types of analysis reports."""

    def __init__(self):
        """Initialize the report formatter."""
        self.logger = logging.getLogger("lse.formatters.ReportFormatter")

    def format_zenrows_report(self, analysis_data: Dict[str, Dict[str, Union[int, float]]]) -> str:
        """Format zenrows error analysis data as CSV report.

        Args:
            analysis_data: Analysis results from TraceAnalyzer

        Returns:
            CSV formatted report string
        """
        self.logger.info("Formatting zenrows error report")

        if not analysis_data:
            self.logger.warning("No analysis data provided, returning empty report")
            return "Date,Total Traces,Zenrows Errors,Error Rate\n"

        return format_csv_report(analysis_data, "Zenrows Error Rate Report")

    def format_summary(self, analysis_data: Dict[str, Dict[str, Union[int, float]]]) -> str:
        """Format analysis data as human-readable summary.

        Args:
            analysis_data: Analysis results from TraceAnalyzer

        Returns:
            Human-readable summary string
        """
        stats = format_summary_stats(analysis_data)

        if stats["total_days"] == 0:
            return "No data available for the specified date range.\n"

        lines = []
        lines.append("=== Zenrows Error Rate Summary ===")
        lines.append(f"Analysis period: {stats['total_days']} day(s)")
        lines.append(f"Total traces analyzed: {stats['total_traces']}")
        lines.append(f"Total zenrows errors: {stats['total_zenrows_errors']}")
        lines.append(f"Overall error rate: {stats['overall_error_rate']:.1f}%")

        if stats["worst_day"] and stats["best_day"]:
            worst_data = analysis_data[stats["worst_day"]]
            best_data = analysis_data[stats["best_day"]]
            lines.append(f"Worst day: {stats['worst_day']} ({worst_data['error_rate']:.1f}%)")
            lines.append(f"Best day: {stats['best_day']} ({best_data['error_rate']:.1f}%)")

        return "\n".join(lines) + "\n"
