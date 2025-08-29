"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from lse.config import Settings
from lse.exceptions import ConfigurationError


class TestSettings:
    """Test the Settings configuration class."""

    def test_default_values(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.langsmith_api_url == "https://api.smith.langchain.com"
            assert settings.output_dir == Path("./data")
            assert settings.log_level == "INFO"

    def test_required_api_key_missing_raises_error(self):
        """Test that missing API key raises ConfigurationError."""
        with patch.dict(os.environ, {}, clear=True):
            # Also patch dotenv loading to ensure completely clean environment
            with patch("dotenv.load_dotenv"):
                with pytest.raises(ConfigurationError, match="LANGSMITH_API_KEY is required"):
                    Settings().validate_required_fields()

    def test_env_variable_override(self):
        """Test that environment variables override defaults."""
        test_env = {
            "LANGSMITH_API_KEY": "test-key-123",
            "LANGSMITH_API_URL": "https://custom-api.com",
            "OUTPUT_DIR": "/custom/path",
            "LOG_LEVEL": "DEBUG",
        }

        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            assert settings.langsmith_api_key == "test-key-123"
            assert settings.langsmith_api_url == "https://custom-api.com"
            assert settings.output_dir == Path("/custom/path")
            assert settings.log_level == "DEBUG"

    def test_dotenv_file_loading(self):
        """Test loading configuration from .env file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_content = """LANGSMITH_API_KEY=from-file-123
LANGSMITH_API_URL=https://from-file.com
OUTPUT_DIR=/from/file
LOG_LEVEL=WARNING
"""
            env_file.write_text(env_content)

            # Change to temp directory to test .env loading
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                with patch.dict(os.environ, {}, clear=True):
                    settings = Settings()
                    assert settings.langsmith_api_key == "from-file-123"
                    assert settings.langsmith_api_url == "https://from-file.com"
                    assert settings.output_dir == Path("/from/file")
                    assert settings.log_level == "WARNING"
            finally:
                os.chdir(original_cwd)

    def test_env_variables_override_dotenv(self):
        """Test that environment variables take precedence over .env file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_content = """LANGSMITH_API_KEY=from-file
LANGSMITH_API_URL=https://from-file.com
"""
            env_file.write_text(env_content)

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                test_env = {
                    "LANGSMITH_API_KEY": "from-env",
                    "LANGSMITH_API_URL": "https://from-env.com",
                }

                with patch.dict(os.environ, test_env, clear=True):
                    settings = Settings()
                    assert settings.langsmith_api_key == "from-env"
                    assert settings.langsmith_api_url == "https://from-env.com"
            finally:
                os.chdir(original_cwd)

    def test_output_dir_creation(self):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "new_output_dir"
            assert not output_path.exists()

            test_env = {
                "LANGSMITH_API_KEY": "test-key",
                "OUTPUT_DIR": str(output_path),
            }

            with patch.dict(os.environ, test_env, clear=True):
                settings = Settings()
                settings.ensure_output_dir()
                assert output_path.exists()
                assert output_path.is_dir()

    def test_log_level_validation(self):
        """Test that invalid log levels raise validation error."""
        test_env = {
            "LANGSMITH_API_KEY": "test-key",
            "LOG_LEVEL": "INVALID",
        }

        with patch.dict(os.environ, test_env, clear=True):
            with pytest.raises(ValueError, match="Invalid log level"):
                Settings()

    def test_api_url_validation(self):
        """Test that invalid API URLs raise validation error."""
        test_env = {
            "LANGSMITH_API_KEY": "test-key",
            "LANGSMITH_API_URL": "not-a-url",
        }

        with patch.dict(os.environ, test_env, clear=True):
            with pytest.raises(ValueError, match="Invalid URL format"):
                Settings()


class TestConfigurationIntegration:
    """Test configuration integration scenarios."""

    def test_complete_valid_configuration(self):
        """Test a complete valid configuration setup."""
        test_env = {
            "LANGSMITH_API_KEY": "sk-test-key-123",
            "LANGSMITH_API_URL": "https://api.smith.langchain.com",
            "OUTPUT_DIR": "./test_data",
            "LOG_LEVEL": "INFO",
        }

        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            settings.validate_required_fields()

            assert settings.langsmith_api_key == "sk-test-key-123"
            assert settings.langsmith_api_url == "https://api.smith.langchain.com"
            assert settings.output_dir == Path("./test_data")
            assert settings.log_level == "INFO"
