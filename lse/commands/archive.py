"""Archive commands for backing up traces to Google Drive."""

import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress

from lse.archive import ArchiveManager
from lse.config import get_settings

logger = logging.getLogger(__name__)
console = Console()

# Create the archive app
archive_app = typer.Typer(
    name="archive",
    help="Archive trace data to Google Drive and restore from backups",
    no_args_is_help=True,
)


@archive_app.command("fetch")
def archive_fetch(
    date: str = typer.Option(
        ...,
        "--date",
        help="Date to fetch traces for (YYYY-MM-DD format)",
    ),
    project: str = typer.Option(
        ...,
        "--project",
        help="Project name to fetch traces from",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip confirmation if local folder already exists",
    ),
) -> None:
    """Fetch all traces for a specific date and project.

    This command fetches ALL traces (no limit) for the given date
    and stores them in the local filesystem organized by creation date.
    """
    try:
        from lse.client import LangSmithClient
        from lse.storage import TraceStorage
        from lse.utils import ProgressContext
        from datetime import datetime

        console.print(f"[blue]🔄 Fetching all traces for {project} on {date}[/blue]")

        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            console.print(f"[red]❌ Invalid date format '{date}'. Expected YYYY-MM-DD[/red]")
            raise typer.Exit(1)

        # Initialize components
        settings = get_settings()
        archive_manager = ArchiveManager(settings)

        # Check if target folder already exists
        target_folder = archive_manager.get_trace_folder(project, date)
        if target_folder.exists() and not force:
            existing_files = [f for f in target_folder.glob("*.json") if not f.name.startswith("_")]
            if existing_files:
                console.print(
                    f"[yellow]⚠️  Target folder already contains {len(existing_files)} trace files:[/yellow]"
                )
                console.print(f"[dim]{target_folder}[/dim]")

                if not typer.confirm("Overwrite existing traces?"):
                    console.print("Fetch cancelled")
                    raise typer.Exit(0)

        # Set up API client and storage
        settings.validate_required_fields()
        client = LangSmithClient(settings)
        storage = TraceStorage(settings)

        # Use wider date range with buffer to ensure we catch all traces
        # Some traces may have timestamps slightly outside the exact 24-hour window
        from datetime import timedelta
        from lse.timezone import parse_date, to_utc, LANGSMITH_TIMEZONE

        # Parse target date and add buffer
        target_date = parse_date(date)

        # Create wide buffer: start 10 hours before target date, end 14 hours after
        buffer_start = target_date - timedelta(hours=10)
        buffer_end = target_date + timedelta(days=1, hours=14)

        # Convert to UTC for API
        start_dt = to_utc(buffer_start.replace(tzinfo=LANGSMITH_TIMEZONE))
        end_dt = to_utc(buffer_end.replace(tzinfo=LANGSMITH_TIMEZONE))

        console.print(f"[dim]Fetching traces with wide buffer: {start_dt} to {end_dt} (UTC)[/dim]")
        console.print(f"[dim]Will filter to only save traces created on {date}[/dim]")

        # Fetch traces with progress
        with ProgressContext("Fetching traces"):
            # Fetch ALL traces in the wide buffer (no limit)
            runs = client.search_runs(
                project_name=project,
                start_time=start_dt.isoformat(),
                end_time=end_dt.isoformat(),
                limit=None,  # No limit - fetch everything
            )

        console.print(f"[dim]Debug: Raw API returned {len(runs)} total runs[/dim]")

        if not runs:
            console.print(f"[yellow]No traces found for {project} on {date}[/yellow]")
            return

        console.print(
            f"[green]Found {len(runs)} traces. Filtering and saving to local storage...[/green]"
        )

        # Filter traces to only include ones created on the requested date
        from lse.timezone import to_langsmith_timezone

        requested_date_str = date

        filtered_runs = []
        for run in runs:
            # Extract creation date from the run
            creation_date = storage._extract_creation_date(run)
            creation_date_langsmith = to_langsmith_timezone(creation_date)
            creation_date_str = creation_date_langsmith.strftime("%Y-%m-%d")

            # Only keep traces that were actually created on the requested date
            if creation_date_str == requested_date_str:
                filtered_runs.append(run)

        if not filtered_runs:
            console.print(f"[yellow]No traces found that were created on {date}[/yellow]")
            console.print(
                f"[dim]Found {len(runs)} traces in date range, but none created on requested date[/dim]"
            )
            return

        discarded_count = len(runs) - len(filtered_runs)
        if discarded_count > 0:
            console.print(f"[dim]Filtered out {discarded_count} traces from other dates[/dim]")

        console.print(f"[green]Saving {len(filtered_runs)} traces created on {date}[/green]")

        # Save traces with progress
        with ProgressContext("Saving traces"):
            saved_paths = storage.save_traces(
                filtered_runs,
                project_name=project,
                timestamp=None,  # Use current timestamp for filename uniqueness
            )

        console.print(f"[green]✅ Successfully fetched and saved {len(saved_paths)} traces[/green]")
        console.print(f"[dim]Traces saved to: {target_folder}[/dim]")

    except Exception as e:
        logger.error(f"Archive fetch failed: {e}")
        console.print(f"[red]❌ Archive fetch failed: {e}[/red]")
        raise typer.Exit(1)


@archive_app.command("zip")
def archive_zip(
    date: str = typer.Option(
        ...,
        "--date",
        help="Date to create zip for (YYYY-MM-DD format)",
    ),
    project: str = typer.Option(
        ...,
        "--project",
        help="Project name to create zip for",
    ),
    output_dir: Optional[str] = typer.Option(
        "./archives",
        "--output-dir",
        help="Directory to save zip files (default: ./archives)",
    ),
) -> None:
    """Create zip file from locally stored traces for a specific date.

    Creates a zip file with naming: [project]_[date].zip containing
    all JSON trace files for that date in a flat structure.
    """
    try:
        console.print(f"[blue]📦 Creating zip file for {project} traces from {date}[/blue]")

        # Initialize archive manager
        settings = get_settings()
        archive_manager = ArchiveManager(settings)

        # Get archive stats first
        stats = archive_manager.get_archive_stats(project, date)
        if not stats["exists"]:
            console.print(f"[red]❌ No traces found for {project} on {date}[/red]")
            console.print(
                f"[yellow]Run 'lse fetch --project {project} --start-date {date} --end-date {date}' first[/yellow]"
            )
            raise typer.Exit(1)

        console.print(
            f"[green]Found {stats['trace_files']} trace files ({stats['total_size_mb']} MB)[/green]"
        )

        # Set up output directory
        zip_output_dir = Path(output_dir) if output_dir else Path("./archives")

        # Create zip archive with progress
        with Progress() as progress:
            task = progress.add_task("[green]Creating zip archive...", total=1)

            zip_path = archive_manager.create_zip_archive(project, date, zip_output_dir)

            progress.update(task, completed=1)

        console.print(f"[green]✅ Successfully created zip archive: {zip_path}[/green]")
        console.print(f"[dim]Zip file contains {stats['trace_files']} trace files[/dim]")

    except Exception as e:
        logger.error(f"Archive zip failed: {e}")
        console.print(f"[red]❌ Archive zip failed: {e}[/red]")
        raise typer.Exit(1)


@archive_app.command("upload")
def archive_upload(
    date: str = typer.Option(
        ...,
        "--date",
        help="Date of traces to upload (YYYY-MM-DD format)",
    ),
    project: str = typer.Option(
        ...,
        "--project",
        help="Project name to upload traces for",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip confirmation if file already exists on Google Drive",
    ),
) -> None:
    """Upload zip file to Google Drive.

    Uploads the zip file to the configured Google Drive folder,
    creating project subfolders as needed.
    """
    try:
        from lse.drive import GoogleDriveClient

        console.print(f"[blue]☁️  Uploading {project} traces from {date} to Google Drive[/blue]")

        # Initialize components
        settings = get_settings()
        archive_manager = ArchiveManager(settings)
        drive_client = GoogleDriveClient(settings)

        # Find the zip file
        zip_filename = archive_manager.create_zip_filename(project, date)
        zip_path = Path("./archives") / zip_filename

        if not zip_path.exists():
            console.print(f"[red]❌ Archive file not found: {zip_path}[/red]")
            console.print(
                f"[yellow]Run 'lse archive zip --project {project} --date {date}' first[/yellow]"
            )
            raise typer.Exit(1)

        console.print(
            f"[dim]Found archive file: {zip_path} ({zip_path.stat().st_size / (1024 * 1024):.1f} MB)[/dim]"
        )

        # Validate Google Drive configuration
        console.print("[dim]Validating Google Drive configuration...[/dim]")
        config_result = drive_client.validate_configuration()

        if not config_result["valid"]:
            console.print(
                f"[red]❌ Google Drive configuration invalid: {config_result['error']}[/red]"
            )
            console.print(
                "[yellow]Check your GOOGLE_DRIVE_FOLDER_URL and authentication setup[/yellow]"
            )
            raise typer.Exit(1)

        console.print(
            f"[green]✓ Connected to Google Drive folder: {config_result['folder_name']}[/green]"
        )

        # Upload with progress
        with Progress() as progress:
            task = progress.add_task("[blue]Uploading to Google Drive...", total=1)

            file_id = drive_client.upload_archive(zip_path, project, force)

            progress.update(task, completed=1)

        console.print("[green]✅ Successfully uploaded archive to Google Drive[/green]")
        console.print(f"[dim]File ID: {file_id}[/dim]")
        console.print(f"[dim]Archive: {project}/{zip_filename}[/dim]")

    except Exception as e:
        logger.error(f"Archive upload failed: {e}")
        console.print(f"[red]❌ Archive upload failed: {e}[/red]")
        raise typer.Exit(1)


@archive_app.command("restore")
def archive_restore(
    project: str = typer.Option(
        ...,
        "--project",
        help="Project name to restore traces for",
    ),
    start_date: Optional[str] = typer.Option(
        None,
        "--start-date",
        help="Start date for restore range (YYYY-MM-DD format). Default: restore all",
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end-date",
        help="End date for restore range (YYYY-MM-DD format). Default: restore all",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip confirmation when overwriting local files",
    ),
) -> None:
    """Restore archived traces from Google Drive.

    Downloads and extracts archived trace files from Google Drive
    back to the local filesystem. Can restore specific date ranges
    or all available archives for a project.
    """
    try:
        from lse.drive import GoogleDriveClient
        from datetime import datetime

        if start_date and end_date:
            console.print(
                f"[blue]🔄 Restoring {project} traces from {start_date} to {end_date}[/blue]"
            )
        elif start_date:
            console.print(f"[blue]🔄 Restoring {project} traces from {start_date} onwards[/blue]")
        else:
            console.print(
                f"[blue]🔄 Restoring all available {project} traces from Google Drive[/blue]"
            )

        # Validate date formats
        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                console.print(
                    f"[red]❌ Invalid start date format '{start_date}'. Expected YYYY-MM-DD[/red]"
                )
                raise typer.Exit(1)

        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                console.print(
                    f"[red]❌ Invalid end date format '{end_date}'. Expected YYYY-MM-DD[/red]"
                )
                raise typer.Exit(1)

        # Initialize components
        settings = get_settings()
        archive_manager = ArchiveManager(settings)
        drive_client = GoogleDriveClient(settings)

        # Validate Google Drive configuration
        console.print("[dim]Validating Google Drive configuration...[/dim]")
        config_result = drive_client.validate_configuration()

        if not config_result["valid"]:
            console.print(
                f"[red]❌ Google Drive configuration invalid: {config_result['error']}[/red]"
            )
            console.print(
                "[yellow]Check your GOOGLE_DRIVE_FOLDER_URL and authentication setup[/yellow]"
            )
            raise typer.Exit(1)

        console.print(
            f"[green]✓ Connected to Google Drive folder: {config_result['folder_name']}[/green]"
        )

        # List available archives
        console.print("[dim]Listing available archives...[/dim]")
        archives = drive_client.list_project_archives(project)

        if not archives:
            console.print(
                f"[yellow]No archives found for project '{project}' on Google Drive[/yellow]"
            )
            return

        console.print(f"[green]Found {len(archives)} archives on Google Drive[/green]")

        # Filter archives by date range if specified
        filtered_archives = []
        for archive in archives:
            # Extract date from filename: project_YYYY-MM-DD.zip
            parts = archive["name"].replace(".zip", "").split("_")
            if len(parts) >= 2:
                archive_date = parts[-1]  # Last part should be the date

                # Apply date filters
                if start_date and archive_date < start_date:
                    continue
                if end_date and archive_date > end_date:
                    continue

                filtered_archives.append({"archive": archive, "date": archive_date})

        if not filtered_archives:
            date_range_str = ""
            if start_date and end_date:
                date_range_str = f" in range {start_date} to {end_date}"
            elif start_date:
                date_range_str = f" from {start_date} onwards"

            console.print(f"[yellow]No archives found{date_range_str}[/yellow]")
            return

        console.print(f"[blue]Will restore {len(filtered_archives)} archives:[/blue]")
        for item in filtered_archives:
            size_mb = item["archive"]["size"] / (1024 * 1024)
            console.print(f"  [dim]• {item['archive']['name']} ({size_mb:.1f} MB)[/dim]")

        # Confirm restore operation
        if not force:
            confirm = typer.confirm(f"Continue with restoring {len(filtered_archives)} archives?")
            if not confirm:
                console.print("Restore cancelled")
                return

        # Restore each archive
        restored_count = 0
        for item in filtered_archives:
            archive = item["archive"]
            date = item["date"]

            console.print(f"[blue]Restoring {archive['name']}...[/blue]")

            try:
                # Download archive to temp location
                temp_path = Path(f"./temp_{archive['name']}")

                with Progress() as progress:
                    task = progress.add_task(f"[blue]Downloading {archive['name']}...", total=1)

                    drive_client.download_archive(archive["name"], project, temp_path)

                    progress.update(task, completed=1)

                # Extract archive
                with Progress() as progress:
                    task = progress.add_task(f"[green]Extracting {archive['name']}...", total=1)

                    extracted_path = archive_manager.extract_zip_archive(
                        temp_path, project, date, force
                    )

                    progress.update(task, completed=1)

                # Clean up temp file
                temp_path.unlink(missing_ok=True)

                console.print(f"[green]✓ Restored {archive['name']} to {extracted_path}[/green]")
                restored_count += 1

            except Exception as e:
                console.print(f"[red]✗ Failed to restore {archive['name']}: {e}[/red]")
                # Clean up temp file on error
                if "temp_path" in locals() and temp_path.exists():
                    temp_path.unlink(missing_ok=True)

        if restored_count > 0:
            console.print(f"[green]✅ Successfully restored {restored_count} archives[/green]")
        else:
            console.print("[red]❌ No archives were successfully restored[/red]")
            raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Archive restore failed: {e}")
        console.print(f"[red]❌ Archive restore failed: {e}[/red]")
        raise typer.Exit(1)


@archive_app.callback(invoke_without_command=True)
def archive_main(
    ctx: typer.Context,
    date: Optional[str] = typer.Option(
        None,
        "--date",
        help="Date to archive (YYYY-MM-DD format)",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        help="Project name to archive",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip all confirmation prompts",
    ),
) -> None:
    """Archive traces by performing fetch, zip, and upload in sequence.

    This is the main archive command that performs the complete workflow:
    1. Fetch all traces for the specified date and project
    2. Create a zip file from the traces
    3. Upload the zip file to Google Drive

    If any step fails, the process stops and reports the error.
    """
    # If a subcommand was invoked, don't run the main logic
    if ctx.invoked_subcommand is not None:
        return

    # Validate required parameters for main command
    if not date or not project:
        typer.echo("❌ Both --date and --project are required for the main archive command")
        typer.echo("Use 'lse archive --help' for more information")
        raise typer.Exit(1)

    try:
        typer.echo(f"🚀 Starting complete archive workflow for {project} on {date}")
        typer.echo("This will: fetch → zip → upload")

        if not force:
            confirm = typer.confirm("Continue with archive workflow?")
            if not confirm:
                typer.echo("Archive cancelled")
                raise typer.Exit(0)

        # Execute the complete workflow: fetch → zip → upload

        # Step 1: Fetch traces
        console.print("[blue]📡 Step 1: Fetching traces...[/blue]")
        try:
            # Use the same logic as archive_fetch but inline
            from lse.client import LangSmithClient
            from lse.storage import TraceStorage
            from lse.timezone import make_date_range_inclusive
            from lse.utils import ProgressContext
            from datetime import datetime

            # Validate date format
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                console.print(f"[red]❌ Invalid date format '{date}'. Expected YYYY-MM-DD[/red]")
                raise typer.Exit(1)

            # Initialize components
            settings = get_settings()
            archive_manager = ArchiveManager(settings)

            # Check if target folder already exists
            target_folder = archive_manager.get_trace_folder(project, date)
            if target_folder.exists() and not force:
                existing_files = [
                    f for f in target_folder.glob("*.json") if not f.name.startswith("_")
                ]
                if existing_files:
                    console.print(
                        f"[yellow]⚠️  Target folder already contains {len(existing_files)} trace files[/yellow]"
                    )
                    console.print(f"[dim]{target_folder}[/dim]")

                    if not typer.confirm("Overwrite existing traces?"):
                        console.print("Archive cancelled")
                        raise typer.Exit(0)

            # Set up API client and storage
            settings.validate_required_fields()
            client = LangSmithClient(settings)
            storage = TraceStorage(settings)

            # Create date range
            start_dt, end_dt = make_date_range_inclusive(date, date)
            console.print(f"[dim]Fetching traces from {start_dt} to {end_dt} (UTC)[/dim]")

            # Fetch traces
            with ProgressContext("Fetching traces") as progress_callback:
                runs = client.search_runs(
                    project_name=project,
                    start_time=start_dt.isoformat(),
                    end_time=end_dt.isoformat(),
                    limit=None,
                )

            if not runs:
                console.print(f"[yellow]No traces found for {project} on {date}[/yellow]")
                return

            console.print(f"[green]Found {len(runs)} traces[/green]")

            # Save traces
            with ProgressContext("Saving traces") as progress_callback:
                saved_paths = storage.save_traces(runs, project_name=project)
                for i, _ in enumerate(saved_paths):
                    progress_callback(i + 1, len(saved_paths))

            console.print(f"[green]✓ Step 1 complete: Saved {len(saved_paths)} traces[/green]")

        except Exception as e:
            console.print(f"[red]❌ Step 1 failed (fetch): {e}[/red]")
            raise typer.Exit(1)

        # Step 2: Create zip file
        console.print("[blue]📦 Step 2: Creating zip archive...[/blue]")
        try:
            # Get archive stats
            stats = archive_manager.get_archive_stats(project, date)
            console.print(
                f"[dim]Archiving {stats['trace_files']} trace files ({stats['total_size_mb']} MB)[/dim]"
            )

            # Create zip
            zip_output_dir = Path("./archives")
            with Progress() as progress:
                task = progress.add_task("[green]Creating zip archive...", total=1)
                zip_path = archive_manager.create_zip_archive(project, date, zip_output_dir)
                progress.update(task, completed=1)

            console.print(f"[green]✓ Step 2 complete: Created {zip_path}[/green]")

        except Exception as e:
            console.print(f"[red]❌ Step 2 failed (zip): {e}[/red]")
            raise typer.Exit(1)

        # Step 3: Upload to Google Drive
        console.print("[blue]☁️  Step 3: Uploading to Google Drive...[/blue]")
        try:
            from lse.drive import GoogleDriveClient

            drive_client = GoogleDriveClient(settings)

            # Validate Google Drive configuration
            config_result = drive_client.validate_configuration()
            if not config_result["valid"]:
                console.print(
                    f"[red]❌ Google Drive configuration invalid: {config_result['error']}[/red]"
                )
                raise typer.Exit(1)

            console.print(
                f"[dim]Connected to Google Drive folder: {config_result['folder_name']}[/dim]"
            )

            # Upload
            with Progress() as progress:
                task = progress.add_task("[blue]Uploading to Google Drive...", total=1)
                file_id = drive_client.upload_archive(zip_path, project, force)
                progress.update(task, completed=1)

            console.print(
                f"[green]✓ Step 3 complete: Uploaded to Google Drive (ID: {file_id})[/green]"
            )

        except Exception as e:
            console.print(f"[red]❌ Step 3 failed (upload): {e}[/red]")
            raise typer.Exit(1)

        # Success!
        console.print("[green]🎉 Archive workflow completed successfully![/green]")
        console.print(f"[dim]• Fetched {len(runs)} traces for {project} on {date}[/dim]")
        console.print(f"[dim]• Created zip archive: {zip_path}[/dim]")
        console.print(f"[dim]• Uploaded to Google Drive: {project}/{zip_path.name}[/dim]")

    except Exception as e:
        logger.error(f"Archive workflow failed: {e}")
        typer.echo(f"❌ Archive workflow failed: {e}", err=True)
        raise typer.Exit(1)
