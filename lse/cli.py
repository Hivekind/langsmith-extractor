"""Main CLI application for LangSmith Extractor."""

import typer

from lse import __app_name__, __version__

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
    """
    pass


if __name__ == "__main__":
    app()