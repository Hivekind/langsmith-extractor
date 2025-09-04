"""Error categorization system for zenrows_scraper failures.

This module provides dynamic error categorization based on comprehensive
production data analysis. It classifies zenrows_scraper errors into categories
for enhanced reporting and analysis.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ErrorCategoryManager:
    """Manages error categories and provides classification functionality."""

    def __init__(self):
        """Initialize with production-validated error categories."""
        self._categories = self._load_default_categories()

    def _load_default_categories(self) -> Dict[str, Dict[str, Any]]:
        """Load default error categories based on production data analysis.

        Returns:
            Dictionary of category definitions with patterns, descriptions, and frequencies.
        """
        return {
            # Target Resource Issues (51.2% of all errors)
            "http_404_not_found": {
                "patterns": ["404 Client Error: Not Found"],
                "description": "Target URL not found or website offline",
                "frequency_pct": 50.4,
            },
            "http_503_service_unavailable": {
                "patterns": ["503 Server Error: Service Unavailable"],
                "description": "CDN or server temporarily unavailable",
                "frequency_pct": 0.8,
            },
            # ZenRows Proxy Issues (35.5% of all errors)
            "http_422_unprocessable": {
                "patterns": ["422 Client Error: Unprocessable Entity"],
                "description": "Anti-bot detection or complex content processing failure",
                "frequency_pct": 18.2,
            },
            "http_413_too_large": {
                "patterns": ["413 Client Error: Request Entity Too Large"],
                "description": "Content exceeds size limits (especially PDF files)",
                "frequency_pct": 12.4,
            },
            "http_400_bad_request": {
                "patterns": ["400 Client Error: Bad Request"],
                "description": "Invalid URLs or blocked content types",
                "frequency_pct": 5.8,
            },
            # Network Connectivity Issues (13.2% of all errors)
            "read_timeout": {
                "patterns": ["ReadTimeout: HTTPSConnectionPool"],
                "description": "60-second timeout exceeded during request",
                "frequency_pct": 13.2,
            },
        }

    def get_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get all available error categories.

        Returns:
            Dictionary of all category definitions.
        """
        return self._categories.copy()

    def get_category_patterns(self, category: str) -> List[str]:
        """Get pattern strings for a specific category.

        Args:
            category: Category name to get patterns for.

        Returns:
            List of pattern strings, empty if category not found.
        """
        if category in self._categories:
            return self._categories[category]["patterns"].copy()
        return []

    def get_category_description(self, category: str) -> str:
        """Get description for a specific category.

        Args:
            category: Category name to get description for.

        Returns:
            Description string, empty if category not found.
        """
        if category in self._categories:
            return self._categories[category]["description"]
        return ""

    def get_category_frequency(self, category: str) -> float:
        """Get frequency percentage for a specific category.

        Args:
            category: Category name to get frequency for.

        Returns:
            Frequency percentage, 0.0 if category not found.
        """
        if category in self._categories:
            return self._categories[category]["frequency_pct"]
        return 0.0

    def get_all_patterns(self) -> List[str]:
        """Get all patterns across all categories.

        Returns:
            List of all pattern strings.
        """
        patterns = []
        for category_data in self._categories.values():
            patterns.extend(category_data["patterns"])
        return patterns

    def add_category(
        self, category: str, patterns: List[str], description: str, frequency_pct: float = 0.0
    ):
        """Add a new error category dynamically.

        Args:
            category: Category name (should be snake_case).
            patterns: List of pattern strings to match against.
            description: Human-readable description of the category.
            frequency_pct: Frequency percentage from analysis (optional).
        """
        self._categories[category] = {
            "patterns": patterns,
            "description": description,
            "frequency_pct": frequency_pct,
        }
        logger.info(f"Added new error category: {category}")

    def get_category_statistics(self) -> List[Dict[str, Any]]:
        """Get category statistics ordered by frequency.

        Returns:
            List of category statistics dictionaries ordered by frequency (descending).
        """
        stats = []
        for category, data in self._categories.items():
            stats.append(
                {
                    "category": category,
                    "frequency_pct": data["frequency_pct"],
                    "description": data["description"],
                    "pattern_count": len(data["patterns"]),
                }
            )

        # Sort by frequency descending
        stats.sort(key=lambda x: x["frequency_pct"], reverse=True)
        return stats


def categorize_zenrows_error(error_record: Dict[str, Any]) -> str:
    """Categorize a zenrows_scraper error based on error message patterns.

    Args:
        error_record: Dictionary containing error information including 'error_message'.

    Returns:
        Category string, 'unknown_errors' if no pattern matches.
    """
    error_message = error_record.get("error_message", "")

    if not error_message:
        return "unknown_errors"

    # Convert to lowercase for case-insensitive matching
    error_lower = error_message.lower()

    # Initialize category manager
    manager = ErrorCategoryManager()
    categories = manager.get_categories()

    # Check each category for pattern matches
    for category, category_data in categories.items():
        for pattern in category_data["patterns"]:
            if pattern.lower() in error_lower:
                logger.debug(f"Categorized error as {category}: {error_message[:100]}...")
                return category

    # No pattern matched - log as unknown error for analysis
    log_unknown_error(error_record)
    return "unknown_errors"


def log_unknown_error(error_record: Dict[str, Any]):
    """Log unknown error patterns for future analysis.

    Args:
        error_record: Dictionary containing error information.
    """
    try:
        # Ensure logs directory exists
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create log entry
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "trace_id": error_record.get("trace_id", "unknown"),
            "project": error_record.get("project", "unknown"),
            "error_message": error_record.get("error_message", ""),
        }

        # Write to log file
        log_file = log_dir / "unknown_errors.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(
                f"{timestamp} | {log_entry['project']} | {log_entry['trace_id']} | {log_entry['error_message']}\n"
            )

        logger.info(
            f"Logged unknown error for analysis: {error_record.get('error_message', '')[:50]}..."
        )

    except Exception as e:
        logger.error(f"Failed to log unknown error: {e}")


def get_category_breakdown_columns() -> List[str]:
    """Get ordered list of category column names for CSV output.

    Returns:
        List of category column names ordered by frequency (most common first).
    """
    manager = ErrorCategoryManager()
    stats = manager.get_category_statistics()

    # Add unknown_errors as the last column
    columns = [stat["category"] for stat in stats]
    if "unknown_errors" not in columns:
        columns.append("unknown_errors")

    return columns


def validate_error_categorization(test_errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate error categorization against a set of test errors.

    Args:
        test_errors: List of error records with expected categories.

    Returns:
        Validation results with accuracy metrics.
    """
    results = {
        "total_errors": len(test_errors),
        "correctly_categorized": 0,
        "mismatches": [],
        "accuracy_percent": 0.0,
    }

    for error in test_errors:
        actual_category = categorize_zenrows_error(error)
        expected_category = error.get("expected_category")

        if actual_category == expected_category:
            results["correctly_categorized"] += 1
        else:
            results["mismatches"].append(
                {
                    "error_message": error.get("error_message", "")[:100],
                    "expected": expected_category,
                    "actual": actual_category,
                }
            )

    if results["total_errors"] > 0:
        results["accuracy_percent"] = (
            results["correctly_categorized"] / results["total_errors"]
        ) * 100

    return results


def get_production_validation_samples() -> List[Dict[str, Any]]:
    """Get production error samples for validation testing.

    Returns:
        List of production error samples with expected categories.
    """
    return [
        {
            "error_message": "HTTPError('404 Client Error: Not Found for url: https://example.com/')",
            "expected_category": "http_404_not_found",
            "trace_id": "validation-404-1",
            "project": "validation",
        },
        {
            "error_message": "HTTPError('422 Client Error: Unprocessable Entity for url: https://example.com/')",
            "expected_category": "http_422_unprocessable",
            "trace_id": "validation-422-1",
            "project": "validation",
        },
        {
            "error_message": "HTTPError('413 Client Error: Request Entity Too Large for url: https://example.com/large.pdf')",
            "expected_category": "http_413_too_large",
            "trace_id": "validation-413-1",
            "project": "validation",
        },
        {
            "error_message": "HTTPError('400 Client Error: Bad Request for url: https://example.com/')",
            "expected_category": "http_400_bad_request",
            "trace_id": "validation-400-1",
            "project": "validation",
        },
        {
            "error_message": "HTTPError('503 Server Error: Service Unavailable for url: https://example.com/')",
            "expected_category": "http_503_service_unavailable",
            "trace_id": "validation-503-1",
            "project": "validation",
        },
        {
            "error_message": "ReadTimeout: HTTPSConnectionPool(host='example.com', port=443): Read timed out. (read timeout=60)",
            "expected_category": "read_timeout",
            "trace_id": "validation-timeout-1",
            "project": "validation",
        },
        {
            "error_message": "UnknownError: This is a new type of error that should be unknown",
            "expected_category": "unknown_errors",
            "trace_id": "validation-unknown-1",
            "project": "validation",
        },
    ]
