"""Archive commands for backing up traces to Google Drive."""

import logging
import time
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
    include_children: bool = typer.Option(
        False,
        "--include-children",
        help="Fetch all child runs for each trace (complete hierarchy)",
    ),
    delay_ms: int = typer.Option(
        200,
        "--delay-ms",
        help="Delay in milliseconds between trace hierarchy requests (default: 200)",
    ),
) -> None:
    """Fetch all traces for a specific date and project.

    This command fetches ALL traces (no limit) for the given date
    and stores them in the local filesystem organized by creation date.
    Use --include-children to fetch complete trace hierarchies with all child runs.
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

        # Use exact UTC day boundaries for precise trace fetching
        from lse.timezone import make_date_range_inclusive

        # Create exact UTC day range (same date for start and end to get that specific day)
        start_dt, end_dt = make_date_range_inclusive(date, date)

        console.print(f"[dim]Fetching traces for exact UTC day: {start_dt} to {end_dt}[/dim]")

        # Fetch traces with progress
        with ProgressContext("Fetching root traces"):
            # Fetch ALL root traces for this exact UTC day (no limit)
            root_runs = client.search_runs(
                project_name=project,
                start_time=start_dt.isoformat(),
                end_time=end_dt.isoformat(),
                limit=None,  # No limit - fetch everything
            )

        if not root_runs:
            console.print(f"[yellow]No traces found for {project} on {date} (UTC)[/yellow]")
            return

        console.print(f"[green]Found {len(root_runs)} root traces for {date} (UTC)[/green]")

        # If include_children is True, fetch all child runs for each trace
        all_runs = []
        if include_children:
            console.print("[blue]Fetching child runs for complete trace hierarchies...[/blue]")
            if delay_ms > 0:
                estimated_time = (len(root_runs) * delay_ms) / 1000 / 60  # minutes
                console.print(
                    f"[dim]Using {delay_ms}ms delay between requests (est. {estimated_time:.1f}min)[/dim]"
                )

            with ProgressContext(f"Fetching child runs for {len(root_runs)} traces") as progress:
                task_id = progress.add_task("Processing traces", total=len(root_runs))

                for i, root_run in enumerate(root_runs):
                    progress.update(
                        task_id,
                        advance=1,
                        description=f"Fetching hierarchy {i + 1}/{len(root_runs)}",
                    )

                    # Fetch complete hierarchy for this trace
                    trace_runs = client.fetch_trace_hierarchy(root_run.id)
                    all_runs.extend(trace_runs)

                    # Add configurable delay to avoid rate limits
                    if delay_ms > 0:
                        time.sleep(delay_ms / 1000.0)

            console.print(
                f"[green]Total runs including children: {len(all_runs)} "
                f"(avg {len(all_runs) // len(root_runs) if root_runs else 0} runs per trace)[/green]"
            )
        else:
            all_runs = root_runs
            console.print("[dim]Use --include-children to fetch complete trace hierarchies[/dim]")

        # Save all runs with progress
        console.print(f"[blue]Saving {len(all_runs)} runs to local storage...[/blue]")
        with ProgressContext("Saving runs"):
            saved_paths = storage.save_traces(
                all_runs,
                project_name=project,
                timestamp=None,  # Use current timestamp for filename uniqueness
            )

        console.print(f"[green]✅ Successfully fetched and saved {len(saved_paths)} runs[/green]")
        console.print(f"[dim]Runs saved to: {target_folder}[/dim]")

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
                f"[yellow]Run 'lse archive fetch --project {project} --date {date}' first[/yellow]"
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
    date: str = typer.Option(
        ...,
        "--date",
        help="Date to restore traces for (YYYY-MM-DD format)",
    ),
    project: str = typer.Option(
        ...,
        "--project",
        help="Project name to restore traces for",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip confirmation when overwriting local files",
    ),
) -> None:
    """Restore archived traces from Google Drive.

    Downloads and extracts archived trace files from Google Drive
    back to the local filesystem for a specific date.
    """
    try:
        from lse.drive import GoogleDriveClient
        from datetime import datetime

        console.print(f"[blue]🔄 Restoring {project} traces for {date}[/blue]")

        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            console.print(f"[red]❌ Invalid date format '{date}'. Expected YYYY-MM-DD[/red]")
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

        # Filter archives by date
        filtered_archives = []
        for archive in archives:
            # Extract date from filename: project_YYYY-MM-DD.zip
            parts = archive["name"].replace(".zip", "").split("_")
            if len(parts) >= 2:
                archive_date = parts[-1]  # Last part should be the date

                # Check if this archive matches the requested date
                if archive_date == date:
                    filtered_archives.append({"archive": archive, "date": archive_date})
                    break  # Only need one archive for the specific date

        if not filtered_archives:
            console.print(f"[yellow]No archive found for {project} on {date}[/yellow]")
            console.print("[dim]Available archives on Google Drive:[/dim]")
            for archive in archives[:5]:  # Show first 5 available
                console.print(f"  [dim]• {archive['name']}[/dim]")
            if len(archives) > 5:
                console.print(f"  [dim]... and {len(archives) - 5} more[/dim]")
            return

        console.print(f"[blue]Will restore archive for {date}:[/blue]")
        for item in filtered_archives:
            size_mb = item["archive"]["size"] / (1024 * 1024)
            console.print(f"  [dim]• {item['archive']['name']} ({size_mb:.1f} MB)[/dim]")

        # Confirm restore operation
        if not force:
            confirm = typer.confirm(f"Continue with restoring archive for {date}?")
            if not confirm:
                console.print("Restore cancelled")
                return

        # Restore the archive
        restored_count = 0
        for item in filtered_archives:
            archive = item["archive"]
            archive_date = item["date"]

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
                        temp_path, project, archive_date, force
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
            console.print(f"[green]✅ Successfully restored archive for {date}[/green]")
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
