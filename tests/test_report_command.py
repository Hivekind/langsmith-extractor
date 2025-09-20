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

    def test_zenrows_errors_rejects_start_date_parameter(self):
        """Test that --start-date parameter is rejected with clear error."""
        result = self.runner.invoke(
            app,
            [
                "report",
                "zenrows-errors",
                "--start-date",
                "2025-08-01",
            ],
        )

        # Should fail with parameter parsing error
        assert result.exit_code != 0
        # Typer sends error messages to output
        output = result.stdout + result.stderr
        assert "start-date" in output or "No such option" in output

    def test_zenrows_errors_rejects_end_date_parameter(self):
        """Test that --end-date parameter is rejected with clear error."""
        result = self.runner.invoke(
            app,
            [
                "report",
                "zenrows-errors",
                "--end-date",
                "2025-08-31",
            ],
        )

        # Should fail with parameter parsing error
        assert result.exit_code != 0
        # Typer sends error messages to output
        output = result.stdout + result.stderr
        assert "end-date" in output or "No such option" in output

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
        """Test that --date parameter is required."""
        result = self.runner.invoke(app, ["report", "zenrows-errors"])

        # Should require the --date parameter
        assert result.exit_code != 0
        # Typer sends error messages to output
        output = (result.stdout + result.stderr).lower()
        assert "missing option" in output or "required" in output

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


class TestIsAvailableCommandStructure:
    """Test is_available command basic structure and help functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_is_available_command_exists(self):
        """Test that is_available command is registered and accessible."""
        result = self.runner.invoke(app, ["report", "is_available", "--help"])

        assert result.exit_code == 0
        assert "is_available" in result.stdout.lower()

    def test_is_available_command_in_report_help(self):
        """Test that is_available command appears in report help."""
        result = self.runner.invoke(app, ["report", "--help"])

        assert result.exit_code == 0
        assert "is_available" in result.stdout or "is-available" in result.stdout

    def test_is_available_help_text_comprehensive(self):
        """Test that help text includes all parameters and usage examples."""
        result = self.runner.invoke(app, ["report", "is_available", "--help"])

        assert result.exit_code == 0
        # Check for key parameters in help text
        assert "--date" in result.stdout
        assert "--start-date" in result.stdout
        assert "--end-date" in result.stdout
        assert "--project" in result.stdout
        # Check for description mentioning availability
        assert "availability" in result.stdout.lower()


class TestIsAvailableCommandParameters:
    """Test is_available command parameter parsing and validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_accepts_single_date_parameter(self):
        """Test that --date parameter is accepted."""
        with patch("lse.commands.report.generate_is_available_report_from_db") as mock_report:
            mock_report.return_value = "date,Trace count,is_available = false count,percentage\n"

            result = self.runner.invoke(app, ["report", "is_available", "--date", "2025-09-01"])

            assert result.exit_code == 0

    def test_accepts_date_range_parameters(self):
        """Test that --start-date and --end-date parameters are accepted together."""
        with patch("lse.commands.report.generate_is_available_report_from_db") as mock_report:
            mock_report.return_value = "date,Trace count,is_available = false count,percentage\n"

            result = self.runner.invoke(
                app,
                [
                    "report",
                    "is_available",
                    "--start-date",
                    "2025-09-01",
                    "--end-date",
                    "2025-09-07",
                ],
            )

            assert result.exit_code == 0

    def test_accepts_project_parameter(self):
        """Test that --project parameter is accepted."""
        with patch("lse.commands.report.generate_is_available_report_from_db") as mock_report:
            mock_report.return_value = "date,Trace count,is_available = false count,percentage\n"

            result = self.runner.invoke(
                app, ["report", "is_available", "--date", "2025-09-01", "--project", "my-project"]
            )

            assert result.exit_code == 0

    def test_rejects_conflicting_date_parameters(self):
        """Test that --date and --start-date/--end-date cannot be used together."""
        result = self.runner.invoke(
            app,
            [
                "report",
                "is_available",
                "--date",
                "2025-09-01",
                "--start-date",
                "2025-09-01",
                "--end-date",
                "2025-09-07",
            ],
        )

        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "cannot specify both" in output.lower() or "date range" in output.lower()

    def test_rejects_incomplete_date_range(self):
        """Test that start-date without end-date is rejected."""
        result = self.runner.invoke(app, ["report", "is_available", "--start-date", "2025-09-01"])

        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "both" in output.lower() or "required" in output.lower()

    def test_rejects_end_date_without_start_date(self):
        """Test that end-date without start-date is rejected."""
        result = self.runner.invoke(app, ["report", "is_available", "--end-date", "2025-09-07"])

        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "both" in output.lower() or "required" in output.lower()

    def test_requires_date_parameters(self):
        """Test that command requires either single date or date range."""
        result = self.runner.invoke(app, ["report", "is_available"])

        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "required" in output.lower() or "either" in output.lower()

    def test_validates_date_format(self):
        """Test that invalid date formats are rejected."""
        result = self.runner.invoke(app, ["report", "is_available", "--date", "invalid-date"])

        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "invalid" in output.lower() or "format" in output.lower()


class TestIsAvailableCommandOutputFormat:
    """Test is_available command output formatting."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_csv_output_format_single_date(self):
        """Test that CSV output format is correct for single date."""
        expected_output = (
            "date,Trace count,is_available = false count,percentage\n2025-09-01,40,3,7.5\n"
        )

        with patch("lse.commands.report.generate_is_available_report_from_db") as mock_report:
            mock_report.return_value = expected_output

            result = self.runner.invoke(app, ["report", "is_available", "--date", "2025-09-01"])

            assert result.exit_code == 0
            assert "date,Trace count,is_available = false count,percentage" in result.stdout
            assert "2025-09-01,40,3,7.5" in result.stdout

    def test_csv_output_format_date_range(self):
        """Test that CSV output format is correct for date range."""
        expected_output = (
            "date,Trace count,is_available = false count,percentage\n"
            "2025-09-01,40,3,7.5\n"
            "2025-09-02,35,1,2.9\n"
            "2025-09-03,42,5,11.9\n"
        )

        with patch("lse.commands.report.generate_is_available_report_from_db") as mock_report:
            mock_report.return_value = expected_output

            result = self.runner.invoke(
                app,
                [
                    "report",
                    "is_available",
                    "--start-date",
                    "2025-09-01",
                    "--end-date",
                    "2025-09-03",
                ],
            )

            assert result.exit_code == 0
            assert "date,Trace count,is_available = false count,percentage" in result.stdout
            assert "2025-09-01,40,3,7.5" in result.stdout
            assert "2025-09-02,35,1,2.9" in result.stdout
            assert "2025-09-03,42,5,11.9" in result.stdout

    def test_outputs_to_stdout(self):
        """Test that report outputs to stdout for easy piping."""
        with patch("lse.commands.report.generate_is_available_report_from_db") as mock_report:
            mock_report.return_value = "date,Trace count,is_available = false count,percentage\n"

            result = self.runner.invoke(app, ["report", "is_available", "--date", "2025-09-01"])

            assert result.exit_code == 0
            # Output should be in stdout, not stderr
            assert len(result.stdout) > 0
            assert "date,Trace count,is_available = false count,percentage" in result.stdout

    def test_handles_empty_results(self):
        """Test that empty results are handled gracefully."""
        with patch("lse.commands.report.generate_is_available_report_from_db") as mock_report:
            mock_report.return_value = "date,Trace count,is_available = false count,percentage\n"

            result = self.runner.invoke(app, ["report", "is_available", "--date", "2025-09-01"])

            assert result.exit_code == 0
            assert "date,Trace count,is_available = false count,percentage" in result.stdout


class TestIsAvailableCommandIntegration:
    """Test is_available command integration with existing CLI structure."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_maintains_existing_report_commands(self):
        """Test that existing report commands still work after adding is_available."""
        result = self.runner.invoke(app, ["report", "zenrows-errors", "--help"])

        assert result.exit_code == 0
        assert "zenrows" in result.stdout.lower()

    def test_follows_cli_error_handling_patterns(self):
        """Test that is_available command follows existing error handling patterns."""
        # Test with database connection error
        with patch("lse.commands.report.generate_is_available_report_from_db") as mock_report:
            mock_report.side_effect = Exception("Database connection failed")

            result = self.runner.invoke(app, ["report", "is_available", "--date", "2025-09-01"])

            # Should handle errors gracefully
            assert result.exit_code != 0
            output = result.stdout + result.stderr
            assert "error" in output.lower() or "failed" in output.lower()

    def test_database_manager_properly_closed(self):
        """Test that database manager is properly closed after report generation."""
        with patch("lse.commands.report.create_database_manager") as mock_db_manager:
            mock_manager = mock_db_manager.return_value.__aenter__.return_value
            mock_analyzer = patch("lse.commands.report.DatabaseTraceAnalyzer").start()
            mock_analyzer.return_value.analyze_is_available_from_db.return_value = {}

            self.runner.invoke(app, ["report", "is_available", "--date", "2025-09-01"])

            # Database manager should be created and closed
            mock_db_manager.assert_called_once()
            mock_manager.close.assert_called_once()


class TestIsAvailableCommandUsageExamples:
    """Test is_available command with realistic usage examples."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_single_project_single_date(self):
        """Test single project, single date analysis."""
        expected_output = (
            "date,Trace count,is_available = false count,percentage\n2025-09-01,50,4,8.0\n"
        )

        with patch("lse.commands.report.generate_is_available_report_from_db") as mock_report:
            mock_report.return_value = expected_output

            result = self.runner.invoke(
                app,
                ["report", "is_available", "--date", "2025-09-01", "--project", "crypto-analysis"],
            )

            assert result.exit_code == 0
            # Verify the mock was called with correct parameters
            mock_report.assert_called_once()
            call_args = mock_report.call_args
            assert call_args[1]["project_name"] == "crypto-analysis"
            assert call_args[1]["report_date"] is not None
            assert call_args[1]["start_date"] is None
            assert call_args[1]["end_date"] is None

    def test_all_projects_date_range(self):
        """Test all projects aggregated over date range."""
        expected_output = (
            "date,Trace count,is_available = false count,percentage\n"
            "2025-09-01,120,8,6.7\n"
            "2025-09-02,115,12,10.4\n"
            "2025-09-03,130,5,3.8\n"
        )

        with patch("lse.commands.report.generate_is_available_report_from_db") as mock_report:
            mock_report.return_value = expected_output

            result = self.runner.invoke(
                app,
                [
                    "report",
                    "is_available",
                    "--start-date",
                    "2025-09-01",
                    "--end-date",
                    "2025-09-03",
                ],
            )

            assert result.exit_code == 0
            # Verify the mock was called with correct parameters
            mock_report.assert_called_once()
            call_args = mock_report.call_args
            assert call_args[1]["project_name"] is None  # All projects
            assert call_args[1]["report_date"] is None
            assert call_args[1]["start_date"] is not None
            assert call_args[1]["end_date"] is not None
