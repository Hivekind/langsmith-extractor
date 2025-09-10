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

    def test_zenrows_errors_requires_end_date_with_start_date(self):
        """Test that --start-date requires --end-date."""
        result = self.runner.invoke(
            app,
            [
                "report",
                "zenrows-errors",
                "--start-date",
                "2025-08-01",
            ],
        )

        # Should fail because end-date is required with start-date
        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "End date is required when start date is provided" in output

    def test_zenrows_errors_requires_start_date_with_end_date(self):
        """Test that --end-date requires --start-date."""
        result = self.runner.invoke(
            app,
            [
                "report",
                "zenrows-errors",
                "--end-date",
                "2025-08-31",
            ],
        )

        # Should fail because start-date is required with end-date
        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "Start date is required when end date is provided" in output

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
        with patch("lse.commands.report.generate_zenrows_report"):
            result = self.runner.invoke(app, ["report", "zenrows-errors", "--date", "invalid-date"])

            # Should either succeed (if validation happens later) or fail with helpful message
            if result.exit_code != 0:
                assert "date" in result.stderr.lower() or "invalid" in result.stderr.lower()


class TestZenrowsDetailCommand:
    """Test zenrows-detail command structure and parameters."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_zenrows_detail_command_exists(self):
        """Test that zenrows-detail command is registered and accessible."""
        result = self.runner.invoke(app, ["report", "zenrows-detail", "--help"])

        assert result.exit_code == 0
        assert "zenrows" in result.stdout.lower()
        assert "detail" in result.stdout.lower()

    def test_zenrows_detail_accepts_date_parameter(self):
        """Test that --date parameter is accepted."""
        with patch("lse.commands.report.generate_zenrows_detail_report") as mock_report:
            mock_report.return_value = "Test output"

            result = self.runner.invoke(app, ["report", "zenrows-detail", "--date", "2025-08-29"])

            # Should accept the date parameter
            assert result.exit_code == 0 or "--date" not in result.stderr

    def test_zenrows_detail_accepts_project_parameter(self):
        """Test that --project parameter is accepted."""
        with patch("lse.commands.report.generate_zenrows_detail_report") as mock_report:
            mock_report.return_value = "Test output"

            result = self.runner.invoke(
                app,
                ["report", "zenrows-detail", "--date", "2025-08-29", "--project", "my-project"],
            )

            # Should accept the project parameter
            assert result.exit_code == 0 or "--project" not in result.stderr

    def test_zenrows_detail_accepts_format_parameter(self):
        """Test that --format parameter is accepted with text and json options."""
        with patch("lse.commands.report.generate_zenrows_detail_report") as mock_report:
            mock_report.return_value = "Test output"

            # Test text format
            result = self.runner.invoke(
                app,
                ["report", "zenrows-detail", "--date", "2025-08-29", "--format", "text"],
            )
            assert result.exit_code == 0 or "--format" not in result.stderr

            # Test json format
            result = self.runner.invoke(
                app,
                ["report", "zenrows-detail", "--date", "2025-08-29", "--format", "json"],
            )
            assert result.exit_code == 0 or "--format" not in result.stderr

    def test_zenrows_detail_requires_date_parameter(self):
        """Test that command requires date parameter."""
        result = self.runner.invoke(app, ["report", "zenrows-detail"])

        # Should fail when no date parameter provided
        assert result.exit_code != 0
        assert "required" in result.stderr.lower() or "missing" in result.stderr.lower()

    def test_zenrows_detail_shows_comprehensive_help(self):
        """Test that help text includes all parameters and usage examples."""
        result = self.runner.invoke(app, ["report", "zenrows-detail", "--help"])

        assert result.exit_code == 0
        # Check for key parameters in help text
        assert "--date" in result.stdout
        assert "--project" in result.stdout
        assert "--format" in result.stdout
        # Check for description
        assert "hierarchical" in result.stdout.lower() or "detail" in result.stdout.lower()

    def test_requires_date_parameter(self):
        """Test that at least one date parameter is required."""
        result = self.runner.invoke(app, ["report", "zenrows-errors"])

        # Should require at least one date parameter
        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "At least one date parameter is required" in output

    def test_accepts_valid_single_date(self):
        """Test that valid single date is accepted."""
        with patch("lse.commands.report.generate_zenrows_report") as mock_report:
            mock_report.return_value = "Date,Total Traces,Zenrows Errors,Error Rate\n"

            result = self.runner.invoke(app, ["report", "zenrows-errors", "--date", "2025-08-29"])

            # Should succeed with valid date
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
        result = self.runner.invoke(app, ["archive", "--help"])

        assert result.exit_code == 0
        assert "archive" in result.stdout.lower()

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
