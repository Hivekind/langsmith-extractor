"""Integration tests for Phase 18 functionality."""

from typer.testing import CliRunner

from lse.cli import app


class TestPhase18Integration:
    """Test Phase 18 enhanced functionality integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_modernized_zenrows_errors_command_structure(self):
        """Test that modernized zenrows-errors command has proper structure."""
        result = self.runner.invoke(app, ["report", "zenrows-errors", "--help"])

        assert result.exit_code == 0
        # Check for new date range parameters
        assert "--start-date" in result.stdout
        assert "--end-date" in result.stdout
        assert "--date" in result.stdout
        assert "--project" in result.stdout

        # Check examples include date range usage
        assert "start-date" in result.stdout
        assert "end-date" in result.stdout

    def test_scraping_insights_command_exists(self):
        """Test that scraping-insights command is properly registered."""
        result = self.runner.invoke(app, ["report", "scraping-insights", "--help"])

        assert result.exit_code == 0
        assert "scraping-insights" in result.stdout.lower()
        assert "unified" in result.stdout.lower()
        assert "availability" in result.stdout.lower()
        assert "zenrows" in result.stdout.lower()

    def test_scraping_insights_has_all_parameters(self):
        """Test that scraping-insights command has all required parameters."""
        result = self.runner.invoke(app, ["report", "scraping-insights", "--help"])

        assert result.exit_code == 0
        assert "--date" in result.stdout
        assert "--start-date" in result.stdout
        assert "--end-date" in result.stdout
        assert "--project" in result.stdout

    def test_scraping_insights_help_examples(self):
        """Test that scraping-insights help includes comprehensive examples."""
        result = self.runner.invoke(app, ["report", "scraping-insights", "--help"])

        assert result.exit_code == 0
        # Should have examples for both single date and date range
        assert "single date" in result.stdout.lower()
        assert "date range" in result.stdout.lower()
        # Should have examples for both specific project and all projects
        assert "specific project" in result.stdout.lower()
        assert "all projects" in result.stdout.lower()

    def test_report_command_lists_all_commands(self):
        """Test that report command lists all available subcommands including new ones."""
        result = self.runner.invoke(app, ["report", "--help"])

        assert result.exit_code == 0
        # Original commands
        assert "zenrows-errors" in result.stdout
        assert "zenrows-detail" in result.stdout
        assert "is_available" in result.stdout
        # New command
        assert "scraping-insights" in result.stdout

    def test_zenrows_errors_parameter_validation_messages(self):
        """Test that zenrows-errors shows proper validation messages."""
        # Test that it requires some date parameter
        result = self.runner.invoke(app, ["report", "zenrows-errors"])

        # Should fail with validation error
        assert result.exit_code != 0
        # Should mention date requirements
        assert "date" in result.stdout.lower() or "date" in result.stderr.lower()

    def test_scraping_insights_parameter_validation_messages(self):
        """Test that scraping-insights shows proper validation messages."""
        # Test that it requires some date parameter
        result = self.runner.invoke(app, ["report", "scraping-insights"])

        # Should fail with validation error
        assert result.exit_code != 0
        # Should mention date requirements
        assert "date" in result.stdout.lower() or "date" in result.stderr.lower()

    def test_backward_compatibility_maintained(self):
        """Test that existing zenrows-errors usage patterns still work."""
        # Test that the old --date parameter still works in help
        result = self.runner.invoke(app, ["report", "zenrows-errors", "--help"])

        assert result.exit_code == 0
        assert "--date" in result.stdout
        assert "--project" in result.stdout

        # Help should indicate backward compatibility
        assert "single date" in result.stdout.lower()


class TestPhase18FormatterIntegration:
    """Test formatter integration for Phase 18 functionality."""

    def test_scraping_insights_formatter_imports(self):
        """Test that scraping insights formatter can be imported."""
        from lse.formatters import ReportFormatter

        formatter = ReportFormatter()
        assert hasattr(formatter, "format_scraping_insights_report")

    def test_scraping_insights_formatter_method_signature(self):
        """Test that scraping insights formatter has correct method signature."""
        from lse.formatters import ReportFormatter
        import inspect

        formatter = ReportFormatter()
        method = getattr(formatter, "format_scraping_insights_report")

        # Should be callable
        assert callable(method)

        # Check method signature
        sig = inspect.signature(method)
        assert "analysis_data" in sig.parameters

    def test_database_analyzer_has_new_methods(self):
        """Test that DatabaseTraceAnalyzer has new methods for Phase 18."""
        from lse.analysis import DatabaseTraceAnalyzer

        # Should have new method
        assert hasattr(DatabaseTraceAnalyzer, "analyze_scraping_insights_from_db")

        # Should have modernized method
        assert hasattr(DatabaseTraceAnalyzer, "analyze_zenrows_errors_from_db")

    def test_analyzer_method_signatures(self):
        """Test that analyzer methods have correct signatures for date range support."""
        from lse.analysis import DatabaseTraceAnalyzer
        import inspect

        # Check zenrows errors method signature
        zenrows_sig = inspect.signature(DatabaseTraceAnalyzer.analyze_zenrows_errors_from_db)
        assert "start_date" in zenrows_sig.parameters
        assert "end_date" in zenrows_sig.parameters
        assert "report_date" in zenrows_sig.parameters

        # Check scraping insights method signature
        insights_sig = inspect.signature(DatabaseTraceAnalyzer.analyze_scraping_insights_from_db)
        assert "start_date" in insights_sig.parameters
        assert "end_date" in insights_sig.parameters
        assert "report_date" in insights_sig.parameters
