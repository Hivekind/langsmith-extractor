"""Configuration management for LSE CLI."""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from lse.exceptions import ConfigurationError


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LangSmith API Configuration
    langsmith_api_key: Optional[str] = Field(
        default=None,
        description="LangSmith API key for authentication",
    )
    langsmith_api_url: str = Field(
        default="https://api.smith.langchain.com",
        description="Base URL for LangSmith API",
    )

    # Output Configuration
    output_dir: Path = Field(
        default=Path("./data"),
        description="Directory for saving fetched traces",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Google Drive Configuration (for archive functionality)
    google_drive_folder_url: Optional[str] = Field(
        default=None,
        description="Google Drive folder URL for storing archived traces",
    )
    google_drive_auth_type: str = Field(
        default="oauth2",
        description="Google Drive authentication type: 'oauth2' or 'service_account'",
    )
    google_drive_credentials_path: Optional[Path] = Field(
        default=None,
        description="Path to Google Drive credentials JSON file (for service account)",
    )

    def __init__(self, **kwargs):
        """Initialize settings with .env file loading."""
        # Load .env file from current working directory
        load_dotenv(override=False)
        super().__init__(**kwargs)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the accepted values."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level '{v}'. Must be one of: {', '.join(valid_levels)}")
        return v.upper()

    @field_validator("langsmith_api_url")
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        """Validate that API URL is properly formatted."""
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL format '{v}'. URL must start with http:// or https://")
        return v

    @field_validator("output_dir", mode="before")
    @classmethod
    def validate_output_dir(cls, v) -> Path:
        """Convert output directory to Path object."""
        return Path(v)

    @field_validator("google_drive_auth_type")
    @classmethod
    def validate_auth_type(cls, v: str) -> str:
        """Validate Google Drive auth type is supported."""
        valid_types = {"oauth2", "service_account"}
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid auth type '{v}'. Must be one of: {', '.join(valid_types)}")
        return v.lower()

    @field_validator("google_drive_credentials_path", mode="before")
    @classmethod
    def validate_credentials_path(cls, v) -> Optional[Path]:
        """Convert credentials path to Path object."""
        if v is None:
            return None
        return Path(v)

    def validate_required_fields(self) -> None:
        """Validate that all required fields are present."""
        if not self.langsmith_api_key:
            raise ConfigurationError(
                "LANGSMITH_API_KEY is required. Please set it in your .env file or as an environment variable."
            )

    def ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_headers(self) -> dict[str, str]:
        """Get HTTP headers for LangSmith API requests."""
        if not self.langsmith_api_key:
            raise ConfigurationError("API key is required for making requests")

        return {
            "Authorization": f"Bearer {self.langsmith_api_key}",
            "Content-Type": "application/json",
        }


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
