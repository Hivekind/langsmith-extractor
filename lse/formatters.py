"""Output formatting utilities for trace analysis reports."""

import json
import logging
from typing import Dict, Union, Any

from rich.console import Console
from rich.tree import Tree

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

    def format_availability_report(
        self, analysis_data: Dict[str, Dict[str, Union[int, float]]]
    ) -> str:
        """Format availability analysis data as CSV report.

        Args:
            analysis_data: Analysis results from DatabaseTraceAnalyzer.analyze_is_available_from_db

        Returns:
            CSV formatted report string
        """
        self.logger.info("Formatting availability report")

        if not analysis_data:
            self.logger.warning("No availability analysis data provided, returning empty report")
            return "date,Trace count,is_available = false count,percentage\n"

        # CSV header for availability report
        header = "date,Trace count,is_available = false count,percentage"
        lines = [header]

        # Sort dates for consistent output
        for date_key in sorted(analysis_data.keys()):
            data = analysis_data[date_key]

            # Format percentage with 1 decimal place (no % symbol to match zenrows format)
            percentage = f"{data['percentage']:.1f}"

            # Create CSV row
            line = (
                f"{date_key},{data['total_traces']},{data['is_available_false_count']},{percentage}"
            )
            lines.append(line)

        # Join with newlines and add final newline
        result = "\n".join(lines) + "\n"

        self.logger.debug(f"Generated availability CSV report with {len(lines) - 1} data rows")
        return result

    def format_scraping_insights_report(
        self, analysis_data: Dict[str, Dict[str, Union[int, float]]]
    ) -> str:
        """Format scraping insights analysis data as CSV report.

        Args:
            analysis_data: Analysis results from DatabaseTraceAnalyzer.analyze_scraping_insights_from_db

        Returns:
            CSV formatted report string
        """
        self.logger.info("Formatting scraping insights report")

        if not analysis_data:
            self.logger.warning(
                "No scraping insights analysis data provided, returning empty report"
            )
            return "date,trace count,zenrows errors count,zenrows errors percentage,is_available false count,is_available false percentage\n"

        # CSV header for scraping insights report
        header = "date,trace count,zenrows errors count,zenrows errors percentage,is_available false count,is_available false percentage"
        lines = [header]

        # Sort dates for consistent output
        for date_key in sorted(analysis_data.keys()):
            data = analysis_data[date_key]

            # Format percentages with 1 decimal place (no % symbol to match other reports)
            zenrows_percentage = f"{data['zenrows_error_percentage']:.1f}"
            availability_percentage = f"{data['availability_false_percentage']:.1f}"

            # Create CSV row
            line = (
                f"{date_key},{data['total_traces']},{data['zenrows_error_count']},{zenrows_percentage},"
                f"{data['availability_false_count']},{availability_percentage}"
            )
            lines.append(line)

        # Join with newlines and add final newline
        result = "\n".join(lines) + "\n"

        self.logger.debug(f"Generated scraping insights CSV report with {len(lines) - 1} data rows")
        return result

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

    def _clean_error_message(self, error_msg: str) -> str:
        """Clean error message by extracting just the essential error info.

        Args:
            error_msg: Raw error message (potentially with stack trace)

        Returns:
            Cleaned error message with just the essential information
        """
        if not error_msg:
            return "Unknown error"

        # For HTTP errors, extract just the HTTP error info
        if "HTTPError(" in error_msg:
            # Extract the HTTPError message before "Traceback"
            if "')Traceback" in error_msg:
                http_part = error_msg.split("')Traceback")[0] + "')"
                # Further clean to get just the HTTP status and URL domain
                if "HTTPError('" in http_part:
                    error_text = http_part.split("HTTPError('")[1].rstrip("')")
                    # Extract status code and domain from URL
                    if " for url: " in error_text:
                        status_part, url_part = error_text.split(" for url: ", 1)
                        # Extract domain from URL
                        try:
                            from urllib.parse import urlparse

                            domain = urlparse(url_part.split("&")[0]).netloc
                            return f"{status_part} - {domain}"
                        except Exception:
                            return status_part
                    return error_text

        # For other errors, try to extract just the error type and message
        if "Error:" in error_msg and "Traceback" in error_msg:
            # Extract just the error line before the traceback
            lines = error_msg.split("\n")
            for line in lines:
                if any(err_type in line for err_type in ["Error:", "Exception:", "Timeout"]):
                    return line.strip()

        # For timeout errors
        if "ReadTimeout" in error_msg or "timeout" in error_msg.lower():
            return "Request timeout"

        # If all else fails, truncate to first 150 characters
        if len(error_msg) > 150:
            return error_msg[:147] + "..."

        return error_msg

    def format_zenrows_detail_text(self, hierarchy: Dict[str, Dict[str, Any]]) -> str:
        """Format zenrows detail hierarchy as indented text.

        Args:
            hierarchy: Hierarchical data structure from build_zenrows_detail_hierarchy

        Returns:
            Formatted text string
        """
        if not hierarchy:
            return "No zenrows errors found for the specified date.\n"

        lines = []
        lines.append("Zenrows Error Detail Report")
        lines.append("=" * 40)
        lines.append("")

        # Sort crypto symbols for consistent output
        for crypto in sorted(hierarchy.keys()):
            traces = hierarchy[crypto]
            lines.append(f"{crypto}:")

            # Sort traces by ID for consistent output
            for trace_id in sorted(traces.keys()):
                errors = traces[trace_id]
                lines.append(f"  {trace_id}:")

                # Handle both formats (list or dict with metadata)
                if isinstance(errors, dict):
                    error_list = errors.get("errors", [])
                else:
                    error_list = errors

                # Add each error with URL and timestamp on separate lines
                for error_detail in error_list:
                    # Handle both old format (string) and new format (dict)
                    if isinstance(error_detail, str):
                        # Backward compatibility with old format
                        clean_error = self._clean_error_message(error_detail)
                        lines.append(f"    Error: {clean_error}")
                        lines.append("      Time:")
                        lines.append("      URL:")
                    else:
                        # New format with full error details
                        error_msg = error_detail.get("error_message", "Unknown error")
                        clean_error = self._clean_error_message(error_msg)

                        # Format timestamp to UTC
                        formatted_time = ""
                        start_time = error_detail.get("start_time")
                        if start_time:
                            try:
                                # Convert to UTC and format nicely
                                from datetime import datetime

                                if isinstance(start_time, str):
                                    # Parse the timestamp
                                    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                                else:
                                    formatted_time = str(start_time)
                            except Exception:
                                formatted_time = str(start_time) if start_time else ""

                        # Get target URL
                        target_url = error_detail.get("target_url", "")

                        lines.append(f"    Error: {clean_error}")
                        lines.append(f"      Time: {formatted_time}")
                        lines.append(f"      URL: {target_url}")

            lines.append("")  # Empty line between crypto symbols

        return "\n".join(lines)

    def format_zenrows_detail_json(
        self, hierarchy: Dict[str, Dict[str, Any]], report_date: str, project_name: str = None
    ) -> str:
        """Format zenrows detail hierarchy as JSON.

        Args:
            hierarchy: Hierarchical data structure from build_zenrows_detail_hierarchy
            report_date: Date of the report (YYYY-MM-DD format)
            project_name: Optional project name

        Returns:
            JSON formatted string
        """
        # Calculate summary statistics
        total_errors = 0
        total_traces = 0
        crypto_counts = {}

        for crypto, traces in hierarchy.items():
            crypto_counts[crypto] = 0
            total_traces += len(traces)

            for trace_id, errors in traces.items():
                if isinstance(errors, dict):
                    error_count = len(errors.get("errors", []))
                else:
                    error_count = len(errors)

                total_errors += error_count
                crypto_counts[crypto] += error_count

        # Build output structure
        output = {
            "report_type": "zenrows_detail",
            "report_date": report_date,
            "project": project_name or "all",
            "summary": {
                "total_errors": total_errors,
                "total_traces": total_traces,
                "crypto_symbols": len(hierarchy),
                "errors_by_crypto": crypto_counts,
            },
            "details": hierarchy,
        }

        return json.dumps(output, indent=2)

    def format_zenrows_detail_rich(self, hierarchy: Dict[str, Dict[str, Any]]) -> str:
        """Format zenrows detail hierarchy using Rich for terminal display.

        Args:
            hierarchy: Hierarchical data structure from build_zenrows_detail_hierarchy

        Returns:
            Formatted string (Rich will handle the actual display)
        """
        if not hierarchy:
            return "No zenrows errors found for the specified date.\n"

        # Create a tree structure using Rich
        tree = Tree("🔍 Zenrows Error Detail Report")

        for crypto in sorted(hierarchy.keys()):
            crypto_branch = tree.add(f"💰 {crypto}")
            traces = hierarchy[crypto]

            for trace_id in sorted(traces.keys()):
                errors = traces[trace_id]
                trace_branch = crypto_branch.add(f"📋 Trace: {trace_id[:8]}...")

                # Handle both formats
                if isinstance(errors, dict):
                    error_list = errors.get("errors", [])
                    if "start_time" in errors:
                        trace_branch.add(f"🕐 {errors['start_time']}")
                else:
                    error_list = errors

                for error_msg in error_list:
                    # Truncate long error messages for display
                    display_msg = error_msg[:80] + "..." if len(error_msg) > 80 else error_msg
                    trace_branch.add(f"❌ {display_msg}")

        # Use console to render tree to string
        console = Console()
        with console.capture() as capture:
            console.print(tree)
        return capture.get()
