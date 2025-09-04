"""Tests for error categorization system."""

from unittest.mock import patch, mock_open

from lse.error_categories import ErrorCategoryManager, categorize_zenrows_error


class TestErrorCategoryManager:
    """Test cases for ErrorCategoryManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ErrorCategoryManager()

    def test_initialization_loads_default_categories(self):
        """Test that manager initializes with default error categories."""
        categories = self.manager.get_categories()

        # Should have all 6 production-identified categories
        expected_categories = {
            "http_404_not_found",
            "http_422_unprocessable",
            "http_413_too_large",
            "read_timeout",
            "http_400_bad_request",
            "http_503_service_unavailable",
        }

        assert set(categories.keys()) == expected_categories

    def test_get_category_patterns(self):
        """Test retrieving patterns for specific categories."""
        patterns_404 = self.manager.get_category_patterns("http_404_not_found")
        assert "404 Client Error: Not Found" in patterns_404

        patterns_timeout = self.manager.get_category_patterns("read_timeout")
        assert "ReadTimeout: HTTPSConnectionPool" in patterns_timeout

    def test_get_category_description(self):
        """Test retrieving descriptions for categories."""
        desc_404 = self.manager.get_category_description("http_404_not_found")
        assert "Target URL not found" in desc_404

        desc_413 = self.manager.get_category_description("http_413_too_large")
        assert "Content exceeds size limits" in desc_413

    def test_get_category_frequency(self):
        """Test retrieving frequency data for categories."""
        freq_404 = self.manager.get_category_frequency("http_404_not_found")
        assert freq_404 == 50.4

        freq_422 = self.manager.get_category_frequency("http_422_unprocessable")
        assert freq_422 == 18.2

    def test_get_all_patterns(self):
        """Test retrieving all patterns across categories."""
        all_patterns = self.manager.get_all_patterns()

        assert "404 Client Error: Not Found" in all_patterns
        assert "422 Client Error: Unprocessable Entity" in all_patterns
        assert "ReadTimeout: HTTPSConnectionPool" in all_patterns

    def test_add_new_category(self):
        """Test adding a new error category dynamically."""
        self.manager.add_category(
            "http_429_rate_limited",
            patterns=["429 Too Many Requests"],
            description="Rate limiting by target server",
            frequency_pct=0.0,
        )

        categories = self.manager.get_categories()
        assert "http_429_rate_limited" in categories

        patterns = self.manager.get_category_patterns("http_429_rate_limited")
        assert "429 Too Many Requests" in patterns

    def test_unknown_category_handling(self):
        """Test handling of unknown category requests."""
        patterns = self.manager.get_category_patterns("nonexistent_category")
        assert patterns == []

        desc = self.manager.get_category_description("nonexistent_category")
        assert desc == ""

        freq = self.manager.get_category_frequency("nonexistent_category")
        assert freq == 0.0

    def test_category_statistics(self):
        """Test category statistics and ordering."""
        stats = self.manager.get_category_statistics()

        # Should be ordered by frequency
        assert stats[0]["category"] == "http_404_not_found"
        assert stats[1]["category"] == "http_422_unprocessable"

        # Check statistics structure
        assert "frequency_pct" in stats[0]
        assert "description" in stats[0]


class TestCategorizeZenrowsError:
    """Test cases for categorize_zenrows_error function."""

    def test_categorize_404_error(self):
        """Test categorization of 404 Not Found errors."""
        error_record = {
            "error_message": "HTTPError('404 Client Error: Not Found for url: https://example.com')"
        }

        category = categorize_zenrows_error(error_record)
        assert category == "http_404_not_found"

    def test_categorize_422_error(self):
        """Test categorization of 422 Unprocessable Entity errors."""
        error_record = {
            "error_message": "HTTPError('422 Client Error: Unprocessable Entity for url: https://example.com')"
        }

        category = categorize_zenrows_error(error_record)
        assert category == "http_422_unprocessable"

    def test_categorize_413_error(self):
        """Test categorization of 413 Request Entity Too Large errors."""
        error_record = {
            "error_message": "HTTPError('413 Client Error: Request Entity Too Large for url: https://example.com/large.pdf')"
        }

        category = categorize_zenrows_error(error_record)
        assert category == "http_413_too_large"

    def test_categorize_400_error(self):
        """Test categorization of 400 Bad Request errors."""
        error_record = {
            "error_message": "HTTPError('400 Client Error: Bad Request for url: https://example.com')"
        }

        category = categorize_zenrows_error(error_record)
        assert category == "http_400_bad_request"

    def test_categorize_503_error(self):
        """Test categorization of 503 Service Unavailable errors."""
        error_record = {
            "error_message": "HTTPError('503 Server Error: Service Unavailable for url: https://example.com')"
        }

        category = categorize_zenrows_error(error_record)
        assert category == "http_503_service_unavailable"

    def test_categorize_timeout_error(self):
        """Test categorization of timeout errors."""
        error_record = {
            "error_message": "ReadTimeout: HTTPSConnectionPool(host='example.com', port=443): Read timed out. (read timeout=60)"
        }

        category = categorize_zenrows_error(error_record)
        assert category == "read_timeout"

    def test_categorize_unknown_error(self):
        """Test categorization of unknown/unmatched errors."""
        error_record = {"error_message": "SomeUnknownError: This is a new type of error"}

        category = categorize_zenrows_error(error_record)
        assert category == "unknown_errors"

    def test_categorize_empty_error_message(self):
        """Test handling of empty or missing error messages."""
        error_record = {"error_message": ""}
        category = categorize_zenrows_error(error_record)
        assert category == "unknown_errors"

        error_record = {}
        category = categorize_zenrows_error(error_record)
        assert category == "unknown_errors"

    def test_case_insensitive_matching(self):
        """Test that error matching is case insensitive."""
        error_record = {
            "error_message": "httperror('404 client error: not found for url: https://example.com')"
        }

        category = categorize_zenrows_error(error_record)
        assert category == "http_404_not_found"

    @patch("lse.error_categories.log_unknown_error")
    def test_unknown_error_logging(self, mock_log):
        """Test that unknown errors are logged for future analysis."""
        error_record = {
            "error_message": "NewUnknownError: This should be logged",
            "trace_id": "test-trace-123",
            "project": "test-project",
        }

        category = categorize_zenrows_error(error_record)
        assert category == "unknown_errors"

        # Should log the unknown error
        mock_log.assert_called_once()

    def test_partial_pattern_matching(self):
        """Test that partial patterns are matched correctly."""
        # Test variations of 404 error messages
        error_variations = [
            "HTTPError: 404 Client Error: Not Found for url",
            "404 Client Error: Not Found",
            "requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://example.com",
        ]

        for error_msg in error_variations:
            error_record = {"error_message": error_msg}
            category = categorize_zenrows_error(error_record)
            assert category == "http_404_not_found", f"Failed to categorize: {error_msg}"


class TestErrorLogging:
    """Test cases for unknown error logging system."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("lse.error_categories.datetime")
    def test_log_unknown_error(self, mock_datetime, mock_file):
        """Test logging of unknown errors to file."""
        from lse.error_categories import log_unknown_error

        # Mock datetime
        mock_datetime.now.return_value.isoformat.return_value = "2025-09-04T10:00:00"

        error_record = {
            "error_message": "UnknownError: New type of error",
            "trace_id": "trace-123",
            "project": "test-project",
        }

        log_unknown_error(error_record)

        # Verify file was opened for append (using Path object)
        from pathlib import Path

        expected_path = Path("logs/unknown_errors.log")
        mock_file.assert_called_once_with(expected_path, "a", encoding="utf-8")

        # Verify log entry was written
        handle = mock_file()
        handle.write.assert_called_once()
        written_content = handle.write.call_args[0][0]

        assert "2025-09-04T10:00:00" in written_content
        assert "trace-123" in written_content
        assert "test-project" in written_content
        assert "UnknownError: New type of error" in written_content

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_log_creates_directory(self, mock_file, mock_mkdir):
        """Test that logging creates logs directory if it doesn't exist."""
        from lse.error_categories import log_unknown_error

        error_record = {
            "error_message": "Test error",
            "trace_id": "trace-123",
            "project": "test-project",
        }

        log_unknown_error(error_record)

        # Should create logs directory
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestProductionDataValidation:
    """Test cases for validating categorization against production patterns."""

    def test_production_error_samples(self):
        """Test categorization against known production error samples."""
        # Real error patterns from production data analysis
        production_samples = [
            {
                "error": "HTTPError('404 Client Error: Not Found for url: https://nonos.systems/')",
                "expected": "http_404_not_found",
            },
            {
                "error": "HTTPError('413 Client Error: Request Entity Too Large for url: http://pepedollar.io/pepedollar_whitepaper_v1.pdf')",
                "expected": "http_413_too_large",
            },
            {
                "error": "HTTPError('422 Client Error: Unprocessable Entity for url: http://agoralend.xyz/')",
                "expected": "http_422_unprocessable",
            },
            {
                "error": "HTTPError('400 Client Error: Bad Request for url: https://vchat-token.onrender.com/')",
                "expected": "http_400_bad_request",
            },
            {
                "error": "ReadTimeout: HTTPSConnectionPool(host='1a.coingecko.xyz', port=443): Read timed out. (read timeout=60)",
                "expected": "read_timeout",
            },
        ]

        for sample in production_samples:
            error_record = {"error_message": sample["error"]}
            category = categorize_zenrows_error(error_record)
            assert category == sample["expected"], (
                f"Failed to categorize production error: {sample['error']}"
            )

    def test_frequency_distribution_accuracy(self):
        """Test that category frequencies match production data analysis."""
        manager = ErrorCategoryManager()

        # Validate frequencies match our production analysis
        assert manager.get_category_frequency("http_404_not_found") == 50.4
        assert manager.get_category_frequency("http_422_unprocessable") == 18.2
        assert manager.get_category_frequency("read_timeout") == 13.2
        assert manager.get_category_frequency("http_413_too_large") == 12.4
        assert manager.get_category_frequency("http_400_bad_request") == 5.8
        assert manager.get_category_frequency("http_503_service_unavailable") == 0.8

    def test_category_completeness(self):
        """Test that all production-identified categories are implemented."""
        manager = ErrorCategoryManager()
        categories = manager.get_categories()

        # All 6 categories from production analysis should be present
        required_categories = [
            "http_404_not_found",  # 50.4% - most common
            "http_422_unprocessable",  # 18.2% - second most common
            "read_timeout",  # 13.2% - network timeouts
            "http_413_too_large",  # 12.4% - PDF/size issues
            "http_400_bad_request",  # 5.8% - invalid requests
            "http_503_service_unavailable",  # 0.8% - server issues
        ]

        for category in required_categories:
            assert category in categories, f"Missing required category: {category}"
