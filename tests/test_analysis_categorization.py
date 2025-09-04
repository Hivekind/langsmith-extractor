"""Tests for enhanced trace analysis with error categorization."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from lse.analysis import TraceAnalyzer, extract_zenrows_errors
from lse.error_categories import ErrorCategoryManager


class TestEnhancedAnalyzeZenrowsErrors:
    """Test cases for enhanced analyze_zenrows_errors function with categorization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = TraceAnalyzer()

    def create_test_trace(self, trace_id: str, error_msg: str = None) -> dict:
        """Create a test trace with optional zenrows_scraper error."""
        trace = {
            "id": trace_id,
            "name": "root_trace",
            "start_time": "2025-09-04T10:00:00Z",
            "end_time": "2025-09-04T10:01:00Z",
            "status": "success",
            "child_runs": [],
        }

        if error_msg:
            zenrows_run = {
                "id": f"{trace_id}_zenrows",
                "name": "zenrows_scraper",
                "status": "error",
                "error": error_msg,
                "start_time": "2025-09-04T10:00:30Z",
                "end_time": "2025-09-04T10:00:45Z",
            }
            trace["child_runs"].append(zenrows_run)

        return trace

    @patch("lse.analysis.find_trace_files")
    @patch("lse.analysis.parse_trace_file")
    def test_analyze_includes_category_breakdown(self, mock_parse, mock_find):
        """Test that analysis includes category breakdown in results."""
        # Setup mock data
        mock_find.return_value = [Path("test1.json"), Path("test2.json")]

        trace1 = self.create_test_trace(
            "trace1", "HTTPError('404 Client Error: Not Found for url: https://example.com')"
        )
        trace2 = self.create_test_trace(
            "trace2",
            "HTTPError('422 Client Error: Unprocessable Entity for url: https://example.com')",
        )

        mock_parse.side_effect = [trace1, trace2]

        # Run analysis
        results = self.analyzer.analyze_zenrows_errors(
            data_dir=Path("/test"),
            project_name="test-project",
            single_date=datetime(2025, 9, 4, tzinfo=timezone.utc),
        )

        # Verify structure includes category breakdown
        assert len(results) == 1
        date_key = "2025-09-04"
        assert date_key in results

        day_data = results[date_key]
        assert "total_traces" in day_data
        assert "zenrows_errors" in day_data
        assert "error_rate" in day_data

        # Should include category breakdown
        assert "categories" in day_data
        categories = day_data["categories"]

        # Check specific categories
        assert "http_404_not_found" in categories
        assert "http_422_unprocessable" in categories
        assert "unknown_errors" in categories

        # Check category counts
        assert categories["http_404_not_found"] == 1
        assert categories["http_422_unprocessable"] == 1
        assert categories["unknown_errors"] == 0

    @patch("lse.analysis.find_trace_files")
    @patch("lse.analysis.parse_trace_file")
    def test_category_aggregation_multi_date(self, mock_parse, mock_find):
        """Test category aggregation across multiple dates."""
        mock_find.return_value = [Path("test1.json"), Path("test2.json"), Path("test3.json")]

        # Different dates for the traces
        trace1 = self.create_test_trace(
            "trace1", "HTTPError('404 Client Error: Not Found for url: https://example.com')"
        )
        trace1["start_time"] = "2025-09-04T10:00:00Z"

        trace2 = self.create_test_trace(
            "trace2", "HTTPError('404 Client Error: Not Found for url: https://example.com')"
        )
        trace2["start_time"] = "2025-09-05T10:00:00Z"

        trace3 = self.create_test_trace(
            "trace3",
            "ReadTimeout: HTTPSConnectionPool(host='example.com', port=443): Read timed out.",
        )
        trace3["start_time"] = "2025-09-05T11:00:00Z"

        mock_parse.side_effect = [trace1, trace2, trace3]

        # Run analysis for date range
        results = self.analyzer.analyze_zenrows_errors(
            data_dir=Path("/test"),
            project_name="test-project",
            start_date=datetime(2025, 9, 4, tzinfo=timezone.utc),
            end_date=datetime(2025, 9, 5, tzinfo=timezone.utc),
        )

        # Check both dates are present
        assert "2025-09-04" in results
        assert "2025-09-05" in results

        # Check 2025-09-04 has 1 404 error
        day1 = results["2025-09-04"]
        assert day1["categories"]["http_404_not_found"] == 1
        assert day1["categories"]["read_timeout"] == 0

        # Check 2025-09-05 has 1 404 and 1 timeout error
        day2 = results["2025-09-05"]
        assert day2["categories"]["http_404_not_found"] == 1
        assert day2["categories"]["read_timeout"] == 1

    @patch("lse.analysis.find_trace_files")
    @patch("lse.analysis.parse_trace_file")
    def test_category_counts_sum_to_total(self, mock_parse, mock_find):
        """Test that category counts sum to total error count."""
        mock_find.return_value = [Path("test1.json"), Path("test2.json"), Path("test3.json")]

        trace1 = self.create_test_trace(
            "trace1", "HTTPError('404 Client Error: Not Found for url: https://example.com')"
        )
        trace2 = self.create_test_trace(
            "trace2",
            "HTTPError('422 Client Error: Unprocessable Entity for url: https://example.com')",
        )
        trace3 = self.create_test_trace("trace3", "UnknownError: This should be unknown")

        mock_parse.side_effect = [trace1, trace2, trace3]

        results = self.analyzer.analyze_zenrows_errors(
            data_dir=Path("/test"),
            project_name="test-project",
            single_date=datetime(2025, 9, 4, tzinfo=timezone.utc),
        )

        day_data = results["2025-09-04"]
        total_errors = day_data["zenrows_errors"]
        categories = day_data["categories"]

        # Sum all category counts
        category_sum = sum(categories.values())

        # Category sum should equal total errors
        assert category_sum == total_errors == 3

    @patch("lse.analysis.find_trace_files")
    @patch("lse.analysis.parse_trace_file")
    def test_unknown_error_handling(self, mock_parse, mock_find):
        """Test handling of unknown error types."""
        mock_find.return_value = [Path("test1.json")]

        trace = self.create_test_trace("trace1", "NewTypeError: This is a completely new error")
        mock_parse.return_value = trace

        results = self.analyzer.analyze_zenrows_errors(
            data_dir=Path("/test"),
            project_name="test-project",
            single_date=datetime(2025, 9, 4, tzinfo=timezone.utc),
        )

        day_data = results["2025-09-04"]
        categories = day_data["categories"]

        # Unknown error should be categorized as unknown_errors
        assert categories["unknown_errors"] == 1
        assert categories["http_404_not_found"] == 0

    @patch("lse.analysis.find_trace_files")
    @patch("lse.analysis.parse_trace_file")
    def test_no_errors_categories_empty(self, mock_parse, mock_find):
        """Test that categories are empty when no errors exist."""
        mock_find.return_value = [Path("test1.json")]

        # Create trace without any errors
        trace = self.create_test_trace("trace1")  # No error message
        mock_parse.return_value = trace

        results = self.analyzer.analyze_zenrows_errors(
            data_dir=Path("/test"),
            project_name="test-project",
            single_date=datetime(2025, 9, 4, tzinfo=timezone.utc),
        )

        day_data = results["2025-09-04"]
        categories = day_data["categories"]

        # All categories should be 0
        for category_count in categories.values():
            assert category_count == 0

        assert day_data["zenrows_errors"] == 0

    @patch("lse.analysis.find_trace_files")
    @patch("lse.analysis.parse_trace_file")
    def test_multi_project_aggregation(self, mock_parse, mock_find):
        """Test aggregation behavior for multi-project analysis."""
        # This test validates the structure even though multi-project
        # aggregation happens at the report level
        mock_find.return_value = [Path("test1.json")]

        trace = self.create_test_trace(
            "trace1",
            "HTTPError('413 Client Error: Request Entity Too Large for url: https://example.com/large.pdf')",
        )
        mock_parse.return_value = trace

        results = self.analyzer.analyze_zenrows_errors(
            data_dir=Path("/test"),
            project_name="project1",
            single_date=datetime(2025, 9, 4, tzinfo=timezone.utc),
        )

        day_data = results["2025-09-04"]
        categories = day_data["categories"]

        # Should categorize PDF size limit error correctly
        assert categories["http_413_too_large"] == 1
        assert categories["http_404_not_found"] == 0


class TestEnhancedExtractZenrowsErrors:
    """Test cases for enhanced extract_zenrows_errors function with categorization."""

    def test_extract_includes_category(self):
        """Test that extracted errors include category information."""
        trace_data = {
            "id": "test-trace",
            "name": "root_trace",
            "status": "success",
            "child_runs": [
                {
                    "id": "zenrows-run",
                    "name": "zenrows_scraper",
                    "status": "error",
                    "error": "HTTPError('404 Client Error: Not Found for url: https://example.com')",
                    "start_time": "2025-09-04T10:00:00Z",
                    "end_time": "2025-09-04T10:01:00Z",
                }
            ],
        }

        errors = extract_zenrows_errors(trace_data)

        assert len(errors) == 1
        error = errors[0]

        # Should include category in error record
        assert "category" in error
        assert error["category"] == "http_404_not_found"

        # Should include trace and project info for logging
        assert "trace_id" in error
        assert "project" in error

    def test_extract_multiple_error_categories(self):
        """Test extraction with multiple different error types."""
        trace_data = {
            "id": "test-trace",
            "name": "root_trace",
            "status": "success",
            "child_runs": [
                {
                    "id": "zenrows-404",
                    "name": "zenrows_scraper",
                    "status": "error",
                    "error": "HTTPError('404 Client Error: Not Found for url: https://example.com')",
                    "start_time": "2025-09-04T10:00:00Z",
                },
                {
                    "id": "zenrows-timeout",
                    "name": "zenrows_scraper",
                    "status": "error",
                    "error": "ReadTimeout: HTTPSConnectionPool(host='example.com', port=443): Read timed out.",
                    "start_time": "2025-09-04T10:01:00Z",
                },
            ],
        }

        errors = extract_zenrows_errors(trace_data)

        assert len(errors) == 2

        # Check categories are correctly assigned
        categories = [error["category"] for error in errors]
        assert "http_404_not_found" in categories
        assert "read_timeout" in categories

    def test_extract_unknown_error_logging(self):
        """Test that unknown errors are properly logged."""
        trace_data = {
            "id": "test-trace",
            "name": "root_trace",
            "status": "success",
            "child_runs": [
                {
                    "id": "zenrows-unknown",
                    "name": "zenrows_scraper",
                    "status": "error",
                    "error": "CompletelyNewError: This has never been seen before",
                    "start_time": "2025-09-04T10:00:00Z",
                }
            ],
        }

        with patch("lse.error_categories.log_unknown_error") as mock_log:
            errors = extract_zenrows_errors(trace_data)

            assert len(errors) == 1
            assert errors[0]["category"] == "unknown_errors"

            # Should have logged the unknown error
            mock_log.assert_called_once()


class TestCategoryAggregation:
    """Test cases for category aggregation functionality."""

    def test_aggregate_categories_by_date(self):
        """Test aggregating category counts by date."""
        # This would test a helper function for aggregating categories
        daily_categories = {
            "2025-09-04": {
                "http_404_not_found": 2,
                "http_422_unprocessable": 1,
                "read_timeout": 0,
                "unknown_errors": 0,
            },
            "2025-09-05": {
                "http_404_not_found": 1,
                "http_422_unprocessable": 0,
                "read_timeout": 2,
                "unknown_errors": 1,
            },
        }

        # Test that we can aggregate across dates
        totals = {}
        for date_categories in daily_categories.values():
            for category, count in date_categories.items():
                totals[category] = totals.get(category, 0) + count

        assert totals["http_404_not_found"] == 3
        assert totals["http_422_unprocessable"] == 1
        assert totals["read_timeout"] == 2
        assert totals["unknown_errors"] == 1

    def test_category_percentage_calculations(self):
        """Test calculation of category percentages."""
        categories = {
            "http_404_not_found": 50,
            "http_422_unprocessable": 18,
            "read_timeout": 13,
            "http_413_too_large": 12,
            "http_400_bad_request": 6,
            "http_503_service_unavailable": 1,
        }

        total_errors = sum(categories.values())

        percentages = {}
        for category, count in categories.items():
            percentages[category] = round((count / total_errors) * 100, 1)

        assert percentages["http_404_not_found"] == 50.0
        assert percentages["http_422_unprocessable"] == 18.0
        assert percentages["read_timeout"] == 13.0

    def test_empty_category_handling(self):
        """Test handling when no errors exist."""
        categories = {
            "http_404_not_found": 0,
            "http_422_unprocessable": 0,
            "read_timeout": 0,
            "unknown_errors": 0,
        }

        total_errors = sum(categories.values())
        assert total_errors == 0

        # Should handle division by zero gracefully
        if total_errors == 0:
            percentages = {category: 0.0 for category in categories}
        else:
            percentages = {
                category: round((count / total_errors) * 100, 1)
                for category, count in categories.items()
            }

        for percentage in percentages.values():
            assert percentage == 0.0


class TestDataStructureBackwardCompatibility:
    """Test cases to ensure backward compatibility of data structures."""

    @patch("lse.analysis.find_trace_files")
    @patch("lse.analysis.parse_trace_file")
    def test_existing_fields_preserved(self, mock_parse, mock_find):
        """Test that existing fields are preserved in enhanced results."""
        analyzer = TraceAnalyzer()
        mock_find.return_value = [Path("test.json")]

        trace = {
            "id": "test-trace",
            "name": "root_trace",
            "start_time": "2025-09-04T10:00:00Z",
            "status": "success",
            "child_runs": [
                {
                    "id": "zenrows-run",
                    "name": "zenrows_scraper",
                    "status": "error",
                    "error": "HTTPError('404 Client Error: Not Found for url: https://example.com')",
                }
            ],
        }
        mock_parse.return_value = trace

        results = analyzer.analyze_zenrows_errors(
            data_dir=Path("/test"),
            project_name="test-project",
            single_date=datetime(2025, 9, 4, tzinfo=timezone.utc),
        )

        day_data = results["2025-09-04"]

        # All existing fields must be preserved
        assert "total_traces" in day_data
        assert "zenrows_errors" in day_data
        assert "error_rate" in day_data

        # New categories field should be added
        assert "categories" in day_data

        # Verify data types match expectations
        assert isinstance(day_data["total_traces"], int)
        assert isinstance(day_data["zenrows_errors"], int)
        assert isinstance(day_data["error_rate"], float)
        assert isinstance(day_data["categories"], dict)

    def test_category_structure_consistent(self):
        """Test that category structure is consistent."""
        manager = ErrorCategoryManager()
        categories = manager.get_categories()

        # Should have all expected categories
        expected_categories = {
            "http_404_not_found",
            "http_422_unprocessable",
            "http_413_too_large",
            "read_timeout",
            "http_400_bad_request",
            "http_503_service_unavailable",
        }

        assert set(categories.keys()) == expected_categories

        # Each category should have the expected structure
        for category, data in categories.items():
            assert "patterns" in data
            assert "description" in data
            assert "frequency_pct" in data
            assert isinstance(data["patterns"], list)
            assert isinstance(data["description"], str)
            assert isinstance(data["frequency_pct"], (int, float))
