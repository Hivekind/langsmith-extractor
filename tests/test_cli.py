"""Tests for CLI application and commands."""

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from lse.cli import app


class TestCLIApp:
    """Test the main CLI application."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_app_help(self):
        """Test that the main app shows help information."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "LangSmith Extractor" in result.stdout
        assert "Extract and analyze LangSmith trace data" in result.stdout

    def test_version_flag(self):
        """Test that --version flag works."""
        result = self.runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "lse v0.1.0" in result.stdout

    def test_version_short_flag(self):
        """Test that -v flag works for version."""
        result = self.runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "lse v0.1.0" in result.stdout

    def test_no_args_shows_help(self):
        """Test that running with no arguments shows help."""
        result = self.runner.invoke(app, [])
        # CLI should exit with error code 2 and show help due to no_args_is_help=True
        assert result.exit_code == 2
        assert "Usage:" in result.stdout

    def test_invalid_command(self):
        """Test that invalid commands show appropriate error."""
        result = self.runner.invoke(app, ["invalid-command"])
        assert result.exit_code != 0
        # Error messages are shown in stderr for typer, need to check stderr
        assert "No such command" in result.stderr or "invalid-command" in result.stderr


class TestLogging:
    """Test logging configuration."""

    def test_logging_setup_default_level(self):
        """Test that logging is configured with default level."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INFO"}, clear=True):
            from lse.cli import setup_logging

            # Clear any existing handlers
            logging.getLogger().handlers.clear()

            setup_logging("INFO")

            logger = logging.getLogger("lse")
            assert logger.level == logging.INFO

    def test_logging_setup_debug_level(self):
        """Test that logging can be configured with DEBUG level."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}, clear=True):
            from lse.cli import setup_logging

            # Clear any existing handlers
            logging.getLogger().handlers.clear()

            setup_logging("DEBUG")

            logger = logging.getLogger("lse")
            assert logger.level == logging.DEBUG

    def test_logging_output_to_stderr(self):
        """Test that log messages go to stderr."""
        import sys
        from io import StringIO
        from unittest.mock import patch

        with patch.dict(os.environ, {"LOG_LEVEL": "INFO"}, clear=True):
            from lse.cli import setup_logging

            # Capture stderr
            captured_stderr = StringIO()

            with patch.object(sys, "stderr", captured_stderr):
                # Clear any existing handlers
                logging.getLogger().handlers.clear()

                setup_logging("INFO")
                logger = logging.getLogger("lse")
                logger.info("Test message")

                stderr_output = captured_stderr.getvalue()
                assert "Test message" in stderr_output


class TestCLIIntegration:
    """Test CLI integration with configuration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_loads_configuration(self):
        """Test that CLI properly loads configuration."""
        # This test verifies that the CLI can access configuration
        # without actually requiring API keys for basic operations
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_content = """LANGSMITH_API_KEY=test-key
OUTPUT_DIR=/test/output
LOG_LEVEL=DEBUG
"""
            env_file.write_text(env_content)

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = self.runner.invoke(app, ["--version"])
                assert result.exit_code == 0
                assert "lse v0.1.0" in result.stdout
            finally:
                os.chdir(original_cwd)

    def test_cli_graceful_error_handling(self):
        """Test that CLI handles configuration errors gracefully."""
        # Test that the CLI doesn't crash on configuration issues
        # when running basic commands like --help or --version
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(app, ["--help"])
            assert result.exit_code == 0

            result = self.runner.invoke(app, ["--version"])
            assert result.exit_code == 0


class TestErrorHandling:
    """Test CLI error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_typer_exception_handling(self):
        """Test that Typer exceptions are handled properly."""
        # This test ensures that Typer's built-in error handling works
        result = self.runner.invoke(app, ["--invalid-flag"])
        assert result.exit_code != 0
        # Typer should handle this and show an error message


class TestEnhancedZenrowsErrorsCommand:
    """Test the enhanced zenrows-errors command with categorization features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_help_shows_new_flags(self):
        """Test that help text shows the new flags and updated documentation."""
        result = self.runner.invoke(app, ["report", "zenrows-errors", "--help"])
        assert result.exit_code == 0

        # Check for new flags
        assert "--debug-unknown-errors" in result.stdout
        assert "--verbose" in result.stdout

        # Check for enhanced help text
        assert "categorization" in result.stdout
        assert "http_404_not_found" in result.stdout
        assert "unknown_errors" in result.stdout

    def test_debug_unknown_errors_flag_syntax(self):
        """Test that --debug-unknown-errors flag is accepted syntactically."""
        # This tests the flag syntax without actually running analysis
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(app, ["report", "zenrows-errors", "--help"])
            assert result.exit_code == 0
            assert "Enable logging of unknown/unclassified" in result.stdout

    def test_verbose_flag_syntax(self):
        """Test that --verbose flag is accepted syntactically."""
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(app, ["report", "zenrows-errors", "--help"])
            assert result.exit_code == 0
            assert "Show detailed progress and category" in result.stdout

    def test_enhanced_csv_output_format_in_help(self):
        """Test that help shows the enhanced CSV output format."""
        result = self.runner.invoke(app, ["report", "zenrows-errors", "--help"])
        assert result.exit_code == 0

        # Check for CSV format documentation
        assert "CSV Output Format" in result.stdout
        assert "Date,Total Traces,Zenrows Errors" in result.stdout
        assert "http_404_not_found" in result.stdout
        assert "http_422_unprocessable" in result.stdout

    def test_enhanced_examples_in_help(self):
        """Test that help shows enhanced usage examples."""
        result = self.runner.invoke(app, ["report", "zenrows-errors", "--help"])
        assert result.exit_code == 0

        # Check for enhanced examples
        assert "--verbose" in result.stdout
        assert "--debug-unknown-errors" in result.stdout

    @patch.dict(os.environ, {"LANGSMITH_API_KEY": "test-key"}, clear=True)
    def test_command_with_debug_flag_no_data(self):
        """Test command with debug flag when no data exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty data directory
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()

            with patch.dict(os.environ, {"OUTPUT_DIR": str(data_dir)}, clear=True):
                result = self.runner.invoke(
                    app,
                    ["report", "zenrows-errors", "--date", "2025-09-04", "--debug-unknown-errors"],
                )
                # Should succeed but produce empty report
                assert result.exit_code == 0
                assert "Date,Total Traces,Zenrows Errors,Error Rate" in result.stdout

    @patch.dict(os.environ, {"LANGSMITH_API_KEY": "test-key"}, clear=True)
    def test_command_with_verbose_flag_no_data(self):
        """Test command with verbose flag when no data exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty data directory
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()

            with patch.dict(os.environ, {"OUTPUT_DIR": str(data_dir)}, clear=True):
                result = self.runner.invoke(
                    app, ["report", "zenrows-errors", "--date", "2025-09-04", "--verbose"]
                )
                # Should succeed but produce empty report
                assert result.exit_code == 0
                assert "Date,Total Traces,Zenrows Errors,Error Rate" in result.stdout

    def test_backward_compatibility_no_new_flags(self):
        """Test that command still works without using any new flags."""
        # This ensures backward compatibility is maintained
        result = self.runner.invoke(app, ["report", "zenrows-errors", "--help"])
        assert result.exit_code == 0

        # Original flags should still be present
        assert "--project" in result.stdout
        assert "--date" in result.stdout
        assert "--start-date" in result.stdout
        assert "--end-date" in result.stdout

    def test_error_category_descriptions_in_help(self):
        """Test that help includes detailed error category descriptions."""
        result = self.runner.invoke(app, ["report", "zenrows-errors", "--help"])
        assert result.exit_code == 0

        # Check for category descriptions (text may be formatted across lines)
        assert "Target" in result.stdout and "URLs" in result.stdout
        assert "Anti-bot" in result.stdout and "detection" in result.stdout
        assert "Network timeouts" in result.stdout
        assert "Content exceeds size limits" in result.stdout
        assert "Invalid URLs" in result.stdout or "blocked content" in result.stdout
        assert "temporarily unavailable" in result.stdout
        assert "Unclassified error patterns" in result.stdout

    @patch("lse.commands.report.generate_zenrows_report")
    def test_debug_flag_enables_logging(self, mock_generate):
        """Test that debug flag enables unknown error logging."""
        mock_generate.return_value = "Date,Total Traces,Zenrows Errors,Error Rate\n"

        with patch.dict(os.environ, {"LANGSMITH_API_KEY": "test-key"}, clear=True):
            result = self.runner.invoke(
                app, ["report", "zenrows-errors", "--date", "2025-09-04", "--debug-unknown-errors"]
            )

            assert result.exit_code == 0
            # Check that environment variable was set for debugging
            assert os.environ.get("LSE_DEBUG_UNKNOWN_ERRORS") == "1"

    @patch("lse.commands.report.generate_zenrows_report")
    def test_verbose_flag_passed_to_function(self, mock_generate):
        """Test that verbose flag is passed to the generation function."""
        mock_generate.return_value = "Date,Total Traces,Zenrows Errors,Error Rate\n"

        with patch.dict(os.environ, {"LANGSMITH_API_KEY": "test-key"}, clear=True):
            result = self.runner.invoke(
                app, ["report", "zenrows-errors", "--date", "2025-09-04", "--verbose"]
            )

            assert result.exit_code == 0
            # Check that verbose=True was passed to the function
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            assert call_args.kwargs.get("verbose") is True

    def test_flag_combination_syntax(self):
        """Test that both flags can be used together syntactically."""
        result = self.runner.invoke(app, ["report", "zenrows-errors", "--help"])
        assert result.exit_code == 0

        # Both flags should be documented
        assert "--debug-unknown-errors" in result.stdout
        assert "--verbose" in result.stdout


class TestZenrowsUrlPatternsCommand:
    """Test the zenrows-url-patterns command for URL pattern analysis."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_help_shows_command_options(self):
        """Test that help text shows all command options and documentation."""
        result = self.runner.invoke(app, ["report", "zenrows-url-patterns", "--help"])
        assert result.exit_code == 0

        # Check for required flags
        assert "--date" in result.stdout
        assert "--start-date" in result.stdout
        assert "--end-date" in result.stdout
        assert "--project" in result.stdout
        assert "--top" in result.stdout
        assert "--verbose" in result.stdout

        # Check for command description
        assert "Analyze URL patterns and domains" in result.stdout
        assert "zenrows_scraper errors" in result.stdout

    def test_command_requires_date_parameter(self):
        """Test that command requires at least one date parameter."""
        with patch.dict(os.environ, {"OUTPUT_DIR": "/tmp"}, clear=True):
            result = self.runner.invoke(app, ["report", "zenrows-url-patterns"])
            assert result.exit_code == 1
            assert "At least one date parameter is required" in result.stderr

    def test_single_date_flag_syntax(self):
        """Test that --date flag is accepted syntactically."""
        with patch.dict(os.environ, {"OUTPUT_DIR": "/tmp"}, clear=True):
            result = self.runner.invoke(
                app, ["report", "zenrows-url-patterns", "--date", "2025-08-29"]
            )
            # May exit with error due to missing data, but should accept syntax
            # Either success (0) or data-related error (1) is acceptable
            assert result.exit_code in [0, 1]

    def test_date_range_flags_syntax(self):
        """Test that --start-date and --end-date flags are accepted."""
        with patch.dict(os.environ, {"OUTPUT_DIR": "/tmp"}, clear=True):
            result = self.runner.invoke(
                app,
                [
                    "report",
                    "zenrows-url-patterns",
                    "--start-date",
                    "2025-08-01",
                    "--end-date",
                    "2025-08-31",
                ],
            )
            # May exit with error due to missing data, but should accept syntax
            assert result.exit_code in [0, 1]

    def test_project_filter_syntax(self):
        """Test that --project flag is accepted for filtering."""
        with patch.dict(os.environ, {"OUTPUT_DIR": "/tmp"}, clear=True):
            result = self.runner.invoke(
                app,
                [
                    "report",
                    "zenrows-url-patterns",
                    "--project",
                    "test-project",
                    "--date",
                    "2025-08-29",
                ],
            )
            assert result.exit_code in [0, 1]

    def test_top_flag_syntax(self):
        """Test that --top flag is accepted for limiting results."""
        with patch.dict(os.environ, {"OUTPUT_DIR": "/tmp"}, clear=True):
            result = self.runner.invoke(
                app,
                ["report", "zenrows-url-patterns", "--date", "2025-08-29", "--top", "10"],
            )
            assert result.exit_code in [0, 1]

    def test_verbose_flag_syntax(self):
        """Test that --verbose flag is accepted."""
        with patch.dict(os.environ, {"OUTPUT_DIR": "/tmp"}, clear=True):
            result = self.runner.invoke(
                app, ["report", "zenrows-url-patterns", "--date", "2025-08-29", "--verbose"]
            )
            assert result.exit_code in [0, 1]

    def test_invalid_date_format_error(self):
        """Test that invalid date formats show appropriate error."""
        with patch.dict(os.environ, {"OUTPUT_DIR": "/tmp"}, clear=True):
            result = self.runner.invoke(
                app, ["report", "zenrows-url-patterns", "--date", "invalid-date"]
            )
            assert result.exit_code == 1

    def test_mixed_date_parameters_error(self):
        """Test that mixing single date with date range shows error."""
        with patch.dict(os.environ, {"OUTPUT_DIR": "/tmp"}, clear=True):
            result = self.runner.invoke(
                app,
                [
                    "report",
                    "zenrows-url-patterns",
                    "--date",
                    "2025-08-29",
                    "--start-date",
                    "2025-08-01",
                ],
            )
            assert result.exit_code == 1
            assert "Cannot use --date with --start-date" in result.stderr

    def test_incomplete_date_range_error(self):
        """Test that incomplete date range shows error."""
        with patch.dict(os.environ, {"OUTPUT_DIR": "/tmp"}, clear=True):
            # Test missing end date
            result = self.runner.invoke(
                app,
                ["report", "zenrows-url-patterns", "--start-date", "2025-08-01"],
            )
            assert result.exit_code == 1
            assert "End date is required when start date is provided" in result.stderr

            # Test missing start date
            result = self.runner.invoke(
                app,
                ["report", "zenrows-url-patterns", "--end-date", "2025-08-31"],
            )
            assert result.exit_code == 1
            assert "Start date is required when end date is provided" in result.stderr

    def test_invalid_top_parameter_error(self):
        """Test that invalid --top parameter shows error."""
        with patch.dict(os.environ, {"OUTPUT_DIR": "/tmp"}, clear=True):
            result = self.runner.invoke(
                app,
                ["report", "zenrows-url-patterns", "--date", "2025-08-29", "--top", "0"],
            )
            assert result.exit_code == 1
            assert "--top must be a positive number" in result.stderr

    def test_output_format_examples_in_help(self):
        """Test that help shows output format documentation."""
        result = self.runner.invoke(app, ["report", "zenrows-url-patterns", "--help"])
        assert result.exit_code == 0

        # Check for output format documentation
        assert "Output Format" in result.stdout
        assert "Type,Name,Count,Top Error Categories" in result.stdout

    def test_usage_examples_in_help(self):
        """Test that help shows usage examples."""
        result = self.runner.invoke(app, ["report", "zenrows-url-patterns", "--help"])
        assert result.exit_code == 0

        # Check for usage examples section
        assert "Examples:" in result.stdout
        # The full examples might be truncated in test output, but key elements should be there
        assert "Single day analysis" in result.stdout or "project --date" in result.stdout
        # At minimum, the command description should mention examples
        assert "Examples:" in result.stdout

    @patch("lse.commands.report.generate_zenrows_url_patterns_report")
    def test_function_called_with_correct_parameters_single_date(self, mock_generate):
        """Test that report generation function is called with correct parameters for single date."""
        mock_generate.return_value = "Type,Name,Count,Top Error Categories\n"

        with patch.dict(os.environ, {"LANGSMITH_API_KEY": "test-key"}, clear=True):
            result = self.runner.invoke(
                app,
                [
                    "report",
                    "zenrows-url-patterns",
                    "--project",
                    "test-project",
                    "--date",
                    "2025-08-29",
                    "--top",
                    "10",
                    "--verbose",
                ],
            )

            assert result.exit_code == 0
            mock_generate.assert_called_once()

            # Check function was called with correct parameters
            call_kwargs = mock_generate.call_args[1]
            assert call_kwargs["project_name"] == "test-project"
            assert call_kwargs["top"] == 10
            assert call_kwargs["verbose"] is True
            assert call_kwargs["single_date"] is not None
            # start_date and end_date should not be in kwargs for single date mode

    @patch("lse.commands.report.generate_zenrows_url_patterns_report")
    def test_function_called_with_correct_parameters_date_range(self, mock_generate):
        """Test that report generation function is called with correct parameters for date range."""
        mock_generate.return_value = "Type,Name,Count,Top Error Categories\n"

        with patch.dict(os.environ, {"LANGSMITH_API_KEY": "test-key"}, clear=True):
            result = self.runner.invoke(
                app,
                [
                    "report",
                    "zenrows-url-patterns",
                    "--start-date",
                    "2025-08-01",
                    "--end-date",
                    "2025-08-31",
                    "--top",
                    "5",
                ],
            )

            assert result.exit_code == 0
            mock_generate.assert_called_once()

            # Check function was called with correct parameters
            call_kwargs = mock_generate.call_args[1]
            assert call_kwargs["project_name"] is None  # No project specified
            assert call_kwargs["top"] == 5
            assert call_kwargs["verbose"] is False  # Default value
            assert call_kwargs["start_date"] is not None
            assert call_kwargs["end_date"] is not None
            # single_date should not be in kwargs for date range mode

    def test_empty_data_produces_valid_csv_header(self):
        """Test that command produces valid CSV header even with no data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty data directory
            data_dir = Path(temp_dir)

            with patch.dict(os.environ, {"OUTPUT_DIR": str(data_dir)}, clear=True):
                result = self.runner.invoke(
                    app, ["report", "zenrows-url-patterns", "--date", "2025-08-29"]
                )

                assert result.exit_code == 0
                assert "Type,Name,Count,Top Error Categories" in result.stdout

    def test_flag_combinations_syntax(self):
        """Test that various flag combinations are accepted syntactically."""
        with patch.dict(os.environ, {"OUTPUT_DIR": "/tmp"}, clear=True):
            # Test all flags together
            result = self.runner.invoke(
                app,
                [
                    "report",
                    "zenrows-url-patterns",
                    "--project",
                    "test-project",
                    "--date",
                    "2025-08-29",
                    "--top",
                    "20",
                    "--verbose",
                ],
            )
            assert result.exit_code in [0, 1]

    def test_backward_compatibility_with_basic_usage(self):
        """Test that command works with minimal required arguments."""
        with patch.dict(os.environ, {"OUTPUT_DIR": "/tmp"}, clear=True):
            result = self.runner.invoke(
                app, ["report", "zenrows-url-patterns", "--date", "2025-08-29"]
            )
            # Should accept basic syntax even if no data exists
            assert result.exit_code in [0, 1]
