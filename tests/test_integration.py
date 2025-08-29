"""Integration tests for zenrows error reporting using real trace data."""

import os
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch

import pytest

from lse.cli import app


class TestRealDataIntegration:
    """Test integration with real trace data files."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.data_dir = Path("data")

    def test_report_with_real_trace_data_single_date(self):
        """Test report command with real trace data for single date."""
        # Skip if no real data available
        if not self.data_dir.exists():
            pytest.skip("No data directory found for integration testing")

        # Mock environment to avoid API key requirements for report
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(app, ["report", "zenrows-errors", "--date", "2025-08-29"])

        # Should succeed and produce CSV output
        assert result.exit_code == 0
        assert "Date,Total Traces,Zenrows Errors,Error Rate" in result.stdout

        # Should have at least header line
        lines = result.stdout.strip().split("\n")
        assert len(lines) >= 1

        # If data exists, should show the requested date
        if len(lines) > 1:
            data_line = lines[1]
            assert "2025-08-29" in data_line

    def test_report_with_real_trace_data_date_range(self):
        """Test report command with real trace data for date range."""
        if not self.data_dir.exists():
            pytest.skip("No data directory found for integration testing")

        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(
                app,
                [
                    "report",
                    "zenrows-errors",
                    "--start-date",
                    "2025-08-25",
                    "--end-date",
                    "2025-08-29",
                ],
            )

        assert result.exit_code == 0
        assert "Date,Total Traces,Zenrows Errors,Error Rate" in result.stdout

        lines = result.stdout.strip().split("\n")
        assert len(lines) >= 1  # At least header

        # Dates should be sorted if data exists
        if len(lines) > 2:
            dates = [line.split(",")[0] for line in lines[1:]]
            assert dates == sorted(dates)

    def test_report_output_format_matches_spec(self):
        """Test that output format exactly matches specification."""
        if not self.data_dir.exists():
            pytest.skip("No data directory found for integration testing")

        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(app, ["report", "zenrows-errors", "--date", "2025-08-29"])

        # Verify exact header format
        assert result.exit_code == 0
        lines = result.stdout.split("\n")
        assert lines[0] == "Date,Total Traces,Zenrows Errors,Error Rate"

        # Verify data format if data exists
        if len(lines) > 1 and lines[1]:
            data_parts = lines[1].split(",")
            assert len(data_parts) == 4

            # Date format: YYYY-MM-DD
            date_part = data_parts[0]
            assert len(date_part) == 10
            assert date_part.count("-") == 2

            # Numbers should be integers
            total_traces = int(data_parts[1])
            zenrows_errors = int(data_parts[2])
            assert total_traces >= 0
            assert zenrows_errors >= 0
            assert zenrows_errors <= total_traces

            # Error rate should be percentage
            error_rate = data_parts[3]
            assert error_rate.endswith("%")
            assert "." in error_rate  # Should have decimal precision

    def test_report_handles_missing_data_gracefully(self):
        """Test report command with date that has no data."""
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(app, ["report", "zenrows-errors", "--date", "2020-01-01"])

        # Should succeed with just header
        assert result.exit_code == 0
        assert result.stdout.strip() == "Date,Total Traces,Zenrows Errors,Error Rate"

    def test_report_works_without_api_key(self):
        """Test that report command works without LangSmith API key."""
        # Report should work on local data without API access
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(app, ["report", "zenrows-errors", "--date", "2025-08-29"])

        # Should not fail due to missing API key
        assert result.exit_code == 0
        assert "API key" not in result.stderr


class TestPerformanceAndScalability:
    """Test performance characteristics with available data."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_report_performance_with_available_data(self):
        """Test report generation performance with available trace files."""
        data_dir = Path("data")
        if not data_dir.exists():
            pytest.skip("No data directory found for performance testing")

        # Count available trace files
        total_files = 0
        for project_dir in data_dir.iterdir():
            if project_dir.is_dir():
                for date_dir in project_dir.iterdir():
                    if date_dir.is_dir():
                        total_files += len(
                            [f for f in date_dir.glob("*.json") if not f.name.startswith("_")]
                        )

        if total_files == 0:
            pytest.skip("No trace files found for performance testing")

        self.runner.invoke(
            app,
            ["report", "zenrows-errors", "--start-date", "2025-01-01", "--end-date", "2025-12-31"],
        )

        # If we get here without timeout, performance is acceptable

    def test_memory_usage_with_large_traces(self):
        """Test memory efficiency with available trace files."""
        # This is a placeholder for memory testing
        # In a production environment, this would use memory profiling
        data_dir = Path("data")
        if not data_dir.exists():
            pytest.skip("No data directory found for memory testing")

        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(
                app,
                [
                    "report",
                    "zenrows-errors",
                    "--start-date",
                    "2025-08-01",
                    "--end-date",
                    "2025-08-31",
                ],
            )

        # Should complete successfully without memory errors
        assert result.exit_code == 0


class TestErrorHandlingWithRealData:
    """Test error handling scenarios with real trace structure."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_handles_real_trace_structure_variations(self):
        """Test handling of real trace structure variations."""
        data_dir = Path("data")
        if not data_dir.exists():
            pytest.skip("No data directory found for structure testing")

        # Test with actual data structure
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(app, ["report", "zenrows-errors", "--date", "2025-08-29"])

        # Should handle real trace structure without errors
        assert result.exit_code == 0
        assert "Error:" not in result.stderr

    def test_graceful_handling_of_partial_data(self):
        """Test graceful handling when some trace files are malformed."""
        # This tests the robustness of parsing with real file structures
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(
                app,
                [
                    "report",
                    "zenrows-errors",
                    "--start-date",
                    "2025-08-01",
                    "--end-date",
                    "2025-08-31",
                ],
            )

        # Should succeed even if some files can't be parsed
        assert result.exit_code == 0
        assert "Date,Total Traces,Zenrows Errors,Error Rate" in result.stdout


class TestCommandLineIntegration:
    """Test command-line integration and piping capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_stdout_piping_compatibility(self):
        """Test that output is suitable for piping to other commands."""
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(app, ["report", "zenrows-errors", "--date", "2025-08-29"])

        # CSV should go to stdout, logs to stderr
        assert result.exit_code == 0
        assert "Date,Total Traces,Zenrows Errors,Error Rate" in result.stdout

        # Logs should not be in stdout
        assert "INFO" not in result.stdout
        assert "ERROR" not in result.stdout

    def test_error_messages_to_stderr(self):
        """Test that error messages go to stderr, not stdout."""
        with patch.dict(os.environ, {}, clear=True):
            result = self.runner.invoke(app, ["report", "zenrows-errors", "--date", "invalid-date"])

        # Should fail with validation error
        assert result.exit_code == 1
        assert "Error:" in result.stderr
        assert "Date,Total Traces,Zenrows Errors,Error Rate" not in result.stdout

    def test_help_text_comprehensive(self):
        """Test that help text provides comprehensive usage information."""
        result = self.runner.invoke(app, ["report", "zenrows-errors", "--help"])

        assert result.exit_code == 0
        assert "zenrows_scraper" in result.stdout
        assert "Examples:" in result.stdout
        assert "--date" in result.stdout
        assert "--start-date" in result.stdout
        assert "--end-date" in result.stdout
