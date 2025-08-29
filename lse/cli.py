"""Main CLI application for LangSmith Extractor."""

import logging
import sys
from pathlib import Path

import typer

from lse import __app_name__, __version__
from lse.config import get_settings
from lse.exceptions import ConfigurationError, LSEError


app = typer.Typer(
    name=__app_name__,
    help="LangSmith Extractor - Extract and analyze LangSmith trace data",
    no_args_is_help=True,
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Display version information."""
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


def setup_logging(log_level: str) -> None:
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    logs_dir = Path(".logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set up formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)
    
    # File handler
    file_handler = logging.FileHandler(logs_dir / "lse.log")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    
    # Configure root logger
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Configure our application logger
    logger = logging.getLogger("lse")
    logger.setLevel(numeric_level)


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application version",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """
    LangSmith Extractor (lse) - CLI tool for extracting and analyzing LangSmith trace data.
    
    A command-line utility for extracting trace data from LangSmith accounts
    and saving it locally for analysis and reporting.
    """
    try:
        # Load configuration and set up logging
        settings = get_settings()
        setup_logging(settings.log_level)
        
        logger = logging.getLogger("lse")
        logger.debug(f"Starting {__app_name__} v{__version__}")
        
    except ConfigurationError as e:
        # Don't fail on configuration errors for basic commands like --help, --version
        # These are handled by typer before we get here due to is_eager=True
        pass
    except Exception as e:
        typer.echo(f"Error initializing application: {e}", err=True)
        raise typer.Exit(1)


def handle_exceptions(func):
    """Decorator to handle exceptions in CLI commands."""
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConfigurationError as e:
            typer.echo(f"Configuration Error: {e}", err=True)
            typer.echo("Please check your .env file or environment variables.", err=True)
            raise typer.Exit(1)
        except LSEError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
        except KeyboardInterrupt:
            typer.echo("\nOperation cancelled by user.", err=True)
            raise typer.Exit(130)
        except Exception as e:
            logger = logging.getLogger("lse")
            logger.exception("Unexpected error occurred")
            typer.echo(f"Unexpected error: {e}", err=True)
            typer.echo("Check the logs for more details.", err=True)
            raise typer.Exit(1)
    
    return wrapper


# Register commands
from lse.commands.fetch import fetch_command
app.command("fetch")(handle_exceptions(fetch_command))


if __name__ == "__main__":
    app()