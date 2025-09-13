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
) -> List[Path]:
    """Find trace files for the specified date.

    Args:
        data_dir: Base directory containing trace data
        project_name: Name of the project to search in
        single_date: Single date to search for (required)

    Returns:
        List of trace file paths

    Raises:
        ValidationError: If no date parameter provided
    """
    if not single_date:
        raise ValidationError("Date parameter is required")

    project_dir = data_dir / project_name
    if not project_dir.exists():
        logger.warning(f"Project directory {project_dir} does not exist")
        return []

    trace_files = []

    # Single date mode - only look in the specific date directory
    date_str = single_date.strftime("%Y-%m-%d")
    date_dir = project_dir / date_str
    if date_dir.exists():
        for trace_file in date_dir.glob("*.json"):
            if not trace_file.name.startswith("_"):  # Skip summary files
                trace_files.append(trace_file)
    else:
        logger.warning(f"No data found for date {date_str} in project {project_name}")

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

    Checks the root trace first for zenrows_scraper errors, then recursively
    searches through child runs (if they exist) to find sub-traces with name
    matching 'zenrows_scraper' and status indicating error.

    Args:
        trace_data: Parsed trace data

    Returns:
        List of error records containing details about zenrows failures
    """
    errors = []

    # First check if the root trace itself is a zenrows_scraper with error
    root_name = trace_data.get("name", "").lower()
    root_status = trace_data.get("status", "").lower()

    if "zenrows_scraper" in root_name and root_status == "error":
        error_record = {
            "id": trace_data.get("id"),
            "name": trace_data.get("name"),
            "status": trace_data.get("status"),
            "error": trace_data.get("error", "Unknown error"),
            "start_time": trace_data.get("start_time"),
            "end_time": trace_data.get("end_time"),
        }
        errors.append(error_record)

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

    # Then search child runs if they exist and are not None
    child_runs = trace_data.get("child_runs")
    if child_runs is not None and child_runs:
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
    ) -> Dict[str, Dict[str, Union[int, float]]]:
        """Analyze zenrows_scraper errors in trace data.

        Args:
            data_dir: Base directory containing trace data
            project_name: Name of the project to analyze
            single_date: Single date to analyze (required)

        Returns:
            Dictionary with daily error statistics
        """
        self.logger.info("Starting zenrows error analysis")

        # Find relevant trace files
        trace_files = find_trace_files(
            data_dir=data_dir,
            project_name=project_name,
            single_date=single_date,
        )

        if not trace_files:
            self.logger.warning("No run files found for analysis")
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

        # Analyze each day
        daily_data = {}
        for date_key, date_traces in grouped_traces.items():
            # Count only root traces (traces without parent_run_id) for the total
            root_traces = [t for t in date_traces if t.get("parent_run_id") is None]
            total_root_traces = len(root_traces)
            total_errors = 0

            # Count zenrows errors across ALL traces (both root and child)
            for trace in date_traces:
                errors = extract_zenrows_errors(trace)
                total_errors += len(errors)

            daily_data[date_key] = {
                "total_traces": total_root_traces,
                "zenrows_errors": total_errors,
            }

        # Calculate error rates
        result = calculate_error_rates(daily_data)

        self.logger.info(f"Analysis completed for {len(result)} days")
        return result


def extract_crypto_symbol(trace: Dict[str, Any]) -> str:
    """Extract cryptocurrency symbol from trace data.

    Looks for symbols in multiple places:
    1. inputs.input_data.crypto_symbol field (highest priority)
    2. inputs.input_data.name field (for cases where name is the symbol)
    3. metadata.symbol field
    4. extra.crypto field
    5. Trace name parsing for common patterns

    Args:
        trace: Trace data dictionary

    Returns:
        Cryptocurrency symbol in uppercase (e.g., "BTC", "ETH") or "Unknown"
    """
    # Check inputs field first (highest priority for traces with structured data)
    inputs = trace.get("inputs", {})
    if inputs and isinstance(inputs, dict):
        # Check for crypto_symbol in input_data
        input_data = inputs.get("input_data", {})
        if input_data and isinstance(input_data, dict):
            crypto_symbol = input_data.get("crypto_symbol")
            if crypto_symbol and isinstance(crypto_symbol, str):
                return crypto_symbol.upper()

            # Check for name field that might be the crypto symbol
            name_field = input_data.get("name")
            if name_field and isinstance(name_field, str):
                # Only use name if it looks like a crypto symbol (short, uppercase-like)
                name_clean = name_field.strip().upper()
                if (
                    len(name_clean) <= 10 and name_clean.isalnum()
                ):  # Reasonable crypto symbol length
                    return name_clean

    # Check metadata (high priority)
    metadata = trace.get("metadata", {})
    if metadata and isinstance(metadata, dict):
        symbol = metadata.get("symbol")
        if symbol:
            return symbol.upper()

    # Check extra field
    extra = trace.get("extra", {})
    if extra and isinstance(extra, dict):
        crypto = extra.get("crypto")
        if crypto:
            return crypto.upper()

    # Parse from trace name and error message
    name = trace.get("name", "")
    error_msg = trace.get("error", "")

    # Combine name and error message for analysis
    search_text = f"{name} {error_msg}".upper()

    if search_text:
        # Common crypto symbols to look for
        common_symbols = [
            "BTC",
            "BITCOIN",
            "ETH",
            "ETHEREUM",
            "SOL",
            "SOLANA",
            "DOGE",
            "DOGECOIN",
            "ADA",
            "CARDANO",
            "DOT",
            "POLKADOT",
            "MATIC",
            "POLYGON",
            "AVAX",
            "AVALANCHE",
            "LINK",
            "CHAINLINK",
            "XRP",
            "RIPPLE",
            "BNB",
            "BINANCE",
            "USDC",
            "USDT",
        ]

        # Crypto-related domain patterns to symbol mapping
        domain_patterns = {
            "BNB": ["bnb", "binance"],
            "ETH": ["ethereum", "eth"],
            "BTC": ["bitcoin", "btc"],
            "SOL": ["solana", "sol"],
            "DOGE": ["doge", "shiba", "inu"],
            "MATIC": ["polygon", "matic"],
            "ADA": ["cardano", "ada"],
        }

        # First, check for direct symbol matches
        for symbol in common_symbols:
            # Look for patterns like BTC_USDT or ETH-USD
            if f"{symbol}_" in search_text or f"{symbol}-" in search_text:
                return symbol.split()[0]  # Take first word for multi-word entries
            # Check for symbol at word boundaries
            if symbol in search_text:
                import re

                pattern = rf"\b{symbol}\b"
                if re.search(pattern, search_text):
                    return symbol.split()[0]

        # Then check for domain-based patterns
        for symbol, patterns in domain_patterns.items():
            for pattern in patterns:
                if pattern.upper() in search_text:
                    return symbol

    return "Unknown"


def extract_zenrows_error_details(trace: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract detailed zenrows error information from a trace.

    Similar to extract_zenrows_errors but includes more details for
    the hierarchical report.

    Args:
        trace: Parsed trace data

    Returns:
        List of error detail dictionaries
    """
    errors = []
    root_trace_id = trace.get("id")

    # Extract crypto symbol for this trace
    crypto_symbol = extract_crypto_symbol(trace)

    # Check if the root trace itself is a zenrows_scraper with error
    root_name = trace.get("name", "").lower()
    root_status = trace.get("status", "").lower()

    # Check for zenrows in the name OR if it's a scraper with error status
    # This catches both "zenrows_scraper" and crypto scrapers like "BTC_scraper"
    is_zenrows_error = ("zenrows" in root_name and root_status == "error") or (
        "scraper" in root_name and root_status == "error"
    )

    if is_zenrows_error:
        # Extract target URL from inputs
        target_url = None
        inputs = trace.get("inputs", {})
        if inputs and isinstance(inputs, dict):
            # Try different possible input fields for URL
            target_url = inputs.get("input") or inputs.get("url") or inputs.get("target_url")

        error_detail = {
            "trace_id": root_trace_id,
            "root_trace_id": root_trace_id,
            "crypto_symbol": crypto_symbol,
            "error_message": trace.get("error", "Unknown error"),
            "start_time": trace.get("start_time"),
            "target_url": target_url,
            "name": trace.get("name"),
        }
        errors.append(error_detail)

    def search_child_runs(runs: List[Dict[str, Any]], parent_crypto: str) -> None:
        """Recursively search child runs for zenrows errors."""
        if not runs:
            return

        for run in runs:
            if not isinstance(run, dict):
                continue

            # Check if this is a zenrows_scraper run with error status
            name = run.get("name", "").lower()
            status = run.get("status", "").lower()

            is_error = ("zenrows" in name and status == "error") or (
                "scraper" in name and status == "error"
            )

            if is_error:
                # Try to get crypto symbol from child, fall back to parent's
                child_crypto = extract_crypto_symbol(run)
                if child_crypto == "Unknown":
                    child_crypto = parent_crypto

                # Extract target URL from child run inputs
                target_url = None
                child_inputs = run.get("inputs", {})
                if child_inputs and isinstance(child_inputs, dict):
                    # Try different possible input fields for URL
                    target_url = (
                        child_inputs.get("input")
                        or child_inputs.get("url")
                        or child_inputs.get("target_url")
                    )

                error_detail = {
                    "trace_id": run.get("id"),
                    "root_trace_id": root_trace_id,
                    "crypto_symbol": child_crypto,
                    "error_message": run.get("error", "Unknown error"),
                    "start_time": run.get("start_time"),
                    "target_url": target_url,
                    "name": run.get("name"),
                }
                errors.append(error_detail)

            # Recursively search nested child runs
            nested_runs = run.get("child_runs")
            if nested_runs:
                search_child_runs(nested_runs, crypto_symbol)

    # Search child runs if they exist
    child_runs = trace.get("child_runs")
    if child_runs is not None and child_runs:
        search_child_runs(child_runs, crypto_symbol)

    return errors


def build_zenrows_detail_hierarchy(
    traces: List[Dict[str, Any]], include_metadata: bool = False
) -> Dict[str, Dict[str, Any]]:
    """Build hierarchical data structure for zenrows detail report.

    Creates a nested dictionary structure:
    {
        "BTC": {
            "due_diligence_12345": ["error1", "error2"],
            "due_diligence_67890": ["error3"]
        },
        "ETH": {
            "due_diligence_11111": ["error4"]
        }
    }

    Or with metadata:
    {
        "BTC": {
            "due_diligence_12345": {
                "errors": ["error1", "error2"],
                "start_time": "2025-08-29T10:00:00Z",
                "name": "due_diligence"
            }
        }
    }

    Args:
        traces: List of trace dictionaries
        include_metadata: Whether to include additional metadata

    Returns:
        Hierarchical dictionary grouped by crypto symbol and true root trace
    """
    # First, build a lookup table for all traces by their ID
    trace_lookup = {}
    for trace in traces:
        trace_id = trace.get("id")
        if trace_id:
            trace_lookup[trace_id] = trace

    hierarchy = {}

    for trace in traces:
        # Extract all errors from this trace
        errors = extract_zenrows_error_details(trace)

        if not errors:
            continue

        # For each error, find the true root trace and extract crypto symbol from it
        for error in errors:
            # Find the true root trace by looking up the trace_id
            trace_id = trace.get("trace_id")  # This points to the root trace
            true_root_trace = None

            if trace_id and trace_id in trace_lookup:
                # Found the root trace
                true_root_trace = trace_lookup[trace_id]
                # Verify it's actually a root trace (depth 0)
                run_depth = true_root_trace.get("extra", {}).get("metadata", {}).get("ls_run_depth")
                if run_depth != 0:
                    # If not depth 0, keep searching for the actual root
                    # This is a fallback - shouldn't happen normally
                    true_root_trace = None

            # If we couldn't find the true root trace, fall back to current trace
            if not true_root_trace:
                true_root_trace = trace

            # Extract crypto symbol from the true root trace (not the error trace)
            crypto = extract_crypto_symbol(true_root_trace)

            root_id = true_root_trace.get("id")
            root_name = true_root_trace.get("name", "unknown")

            # Initialize crypto level if needed
            if crypto not in hierarchy:
                hierarchy[crypto] = {}

            # Initialize trace level if needed
            if root_id not in hierarchy[crypto]:
                if include_metadata:
                    hierarchy[crypto][root_id] = {
                        "errors": [],
                        "start_time": true_root_trace.get("start_time"),
                        "name": root_name,
                    }
                else:
                    hierarchy[crypto][root_id] = []

            # Add error details (full object with URL, timestamp, etc.)
            if include_metadata:
                hierarchy[crypto][root_id]["errors"].append(error)
            else:
                hierarchy[crypto][root_id].append(error)

    return hierarchy
