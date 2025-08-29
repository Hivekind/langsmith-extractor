"""Custom exceptions for the LSE CLI."""


class LSEError(Exception):
    """Base exception for LSE CLI errors."""

    pass


class ConfigurationError(LSEError):
    """Raised when there are configuration-related errors."""

    pass


class APIError(LSEError):
    """Raised when there are LangSmith API communication errors."""

    pass


class ValidationError(LSEError):
    """Raised when there are input validation errors."""

    pass