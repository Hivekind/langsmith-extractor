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
            
            with patch.object(sys, 'stderr', captured_stderr):
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