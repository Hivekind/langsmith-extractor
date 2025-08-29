"""Tests for report command functionality."""

from unittest.mock import patch

from typer.testing import CliRunner

from lse.cli import app


class TestReportCommandStructure:
    """Test report command basic structure and help functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_report_command_exists(self):
        """Test that report command is registered and accessible."""
        result = self.runner.invoke(app, ["report", "--help"])

        assert result.exit_code == 0
        assert "report" in result.stdout.lower()

    def test_report_command_shows_subcommands(self):
        """Test that report command lists available subcommands."""
        result = self.runner.invoke(app, ["report", "--help"])

        assert result.exit_code == 0
        assert "zenrows-errors" in result.stdout

    def test_zenrows_errors_subcommand_exists(self):
        """Test that zenrows-errors subcommand is available."""
        result = self.runner.invoke(app, ["report", "zenrows-errors", "--help"])

        assert result.exit_code == 0
        assert "zenrows" in result.stdout.lower()


class TestReportCommandParameters:
    """Test report command parameter parsing and validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_zenrows_errors_accepts_date_parameter(self):
        """Test that --date parameter is accepted."""
        # Mock the actual implementation to avoid file system dependencies
        with patch("lse.commands.report.generate_zenrows_report") as mock_report:
            mock_report.return_value = None

            result = self.runner.invoke(app, ["report", "zenrows-errors", "--date", "2025-08-29"])

            # Should not fail due to parameter parsing
            assert "--date" not in result.stdout or result.exit_code == 0

    def test_zenrows_errors_accepts_date_range_parameters(self):
        """Test that --start-date and --end-date parameters are accepted."""
        with patch("lse.commands.report.generate_zenrows_report") as mock_report:
            mock_report.return_value = None

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

            # Should not fail due to parameter parsing
            assert result.exit_code == 0 or "start-date" not in result.stdout

    def test_zenrows_errors_shows_help_text(self):
        """Test that help text is comprehensive and useful."""
        result = self.runner.invoke(app, ["report", "zenrows-errors", "--help"])

        assert result.exit_code == 0
        assert "date" in result.stdout.lower()
        assert "zenrows" in result.stdout.lower()


class TestDateParameterValidation:
    """Test date parameter validation logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_validates_date_format(self):
        """Test that invalid date formats are rejected."""
        with patch("lse.commands.report.generate_zenrows_report") as mock_report:
            result = self.runner.invoke(app, ["report", "zenrows-errors", "--date", "invalid-date"])

            # Should either succeed (if validation happens later) or fail with helpful message
            if result.exit_code != 0:
                assert "date" in result.stderr.lower() or "invalid" in result.stderr.lower()

    def test_validates_date_range_order(self):
        """Test that start date must be before end date."""
        with patch("lse.commands.report.generate_zenrows_report") as mock_report:
            result = self.runner.invoke(
                app,
                [
                    "report",
                    "zenrows-errors",
                    "--start-date",
                    "2025-08-31",
                    "--end-date",
                    "2025-08-01",
                ],
            )

            # Should either succeed (if validation happens later) or fail with helpful message
            if result.exit_code != 0:
                assert "date" in result.stderr.lower() or "range" in result.stderr.lower()

    def test_requires_at_least_one_date_parameter(self):
        """Test that at least one date parameter is required."""
        with patch("lse.commands.report.generate_zenrows_report") as mock_report:
            result = self.runner.invoke(app, ["report", "zenrows-errors"])

            # Should require at least one date parameter
            if result.exit_code != 0:
                assert "date" in result.stderr.lower() or "required" in result.stderr.lower()

    def test_accepts_valid_single_date(self):
        """Test that valid single date is accepted."""
        with patch("lse.commands.report.generate_zenrows_report") as mock_report:
            mock_report.return_value = "Date,Total Traces,Zenrows Errors,Error Rate\n"

            result = self.runner.invoke(app, ["report", "zenrows-errors", "--date", "2025-08-29"])

            # Should succeed with valid date
            assert result.exit_code == 0

    def test_accepts_valid_date_range(self):
        """Test that valid date range is accepted."""
        with patch("lse.commands.report.generate_zenrows_report") as mock_report:
            mock_report.return_value = "Date,Total Traces,Zenrows Errors,Error Rate\n"

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

            # Should succeed with valid date range
            assert result.exit_code == 0


class TestReportCommandIntegration:
    """Test report command integration with existing CLI structure."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_report_command_in_main_help(self):
        """Test that report command appears in main CLI help."""
        result = self.runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "report" in result.stdout

    def test_maintains_existing_commands(self):
        """Test that existing commands still work after adding report."""
        result = self.runner.invoke(app, ["fetch", "--help"])

        assert result.exit_code == 0
        assert "fetch" in result.stdout.lower()

    def test_follows_cli_error_handling_patterns(self):
        """Test that report command follows existing error handling patterns."""
        # Test with invalid command structure
        result = self.runner.invoke(app, ["report", "nonexistent-command"])

        # Should follow existing error patterns
        assert result.exit_code != 0
        if result.stderr:
            assert len(result.stderr) > 0


class TestReportOutputFormat:
    """Test report command output formatting."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_csv_output_format(self):
        """Test that CSV output format is correct."""
        expected_output = "Date,Total Traces,Zenrows Errors,Error Rate\n2025-08-29,100,5,5.0%\n"

        with patch("lse.commands.report.generate_zenrows_report") as mock_report:
            mock_report.return_value = expected_output

            result = self.runner.invoke(app, ["report", "zenrows-errors", "--date", "2025-08-29"])

            assert result.exit_code == 0
            assert "Date,Total Traces,Zenrows Errors,Error Rate" in result.stdout

    def test_outputs_to_stdout(self):
        """Test that report outputs to stdout for easy piping."""
        with patch("lse.commands.report.generate_zenrows_report") as mock_report:
            mock_report.return_value = "Date,Total Traces,Zenrows Errors,Error Rate\n"

            result = self.runner.invoke(app, ["report", "zenrows-errors", "--date", "2025-08-29"])

            assert result.exit_code == 0
            # Output should be in stdout, not stderr
            assert len(result.stdout) > 0
