"""Fetch command for retrieving LangSmith traces."""

import logging
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console

from lse.cli import get_langsmith_client
from lse.config import get_settings
from lse.exceptions import APIError, ValidationError
from lse.storage import TraceStorage
from lse.utils import create_spinner, ProgressContext, OperationTimer

logger = logging.getLogger("lse.fetch")
console = Console()


def validate_date(date_str: str) -> datetime:
    """Validate and parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValidationError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD.")


def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> tuple[Optional[datetime], Optional[datetime]]:
    """Validate date range parameters."""
    start_dt = None
    end_dt = None
    
    if start_date:
        start_dt = validate_date(start_date)
    
    if end_date:
        end_dt = validate_date(end_date)
    
    if start_dt and end_dt and start_dt >= end_dt:
        raise ValidationError("Start date must be before end date.")
    
    return start_dt, end_dt


def fetch_traces(
    trace_id: Optional[str] = None,
    project: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> dict:
    """Fetch traces from LangSmith API and save them locally."""
    logger.info("Executing LangSmith trace fetch")
    
    # Initialize client and storage
    client = get_langsmith_client()
    settings = get_settings()
    storage = TraceStorage(settings)
    
    with OperationTimer("Trace fetch operation"):
        traces_data = []
        saved_files = []
        
        if trace_id:
            # Single trace fetch with spinner
            with create_spinner(f"Fetching trace {trace_id}..."):
                try:
                    run = client.fetch_run(trace_id)
                    traces_data = [run]
                    logger.info(f"Successfully fetched trace {trace_id}")
                except APIError as e:
                    logger.error(f"Failed to fetch trace {trace_id}: {e}")
                    raise
            
            # Save single trace
            with create_spinner("Saving trace..."):
                try:
                    file_path = storage.save_trace(run, project)
                    saved_files = [file_path]
                except Exception as e:
                    logger.error(f"Failed to save trace: {e}")
                    raise
            
        else:
            # Multiple trace search with progress bar
            with ProgressContext("Fetching and saving traces") as progress:
                # Phase 1: Search
                search_task = progress.add_task("Searching LangSmith...", total=100)
                
                try:
                    # Build search parameters
                    search_params = {}
                    if project:
                        search_params['project_name'] = project
                    if start_date:
                        search_params['start_time'] = start_date.isoformat()
                    if end_date:
                        search_params['end_time'] = end_date.isoformat()
                    
                    # Execute search
                    runs = client.search_runs(limit=limit, **search_params)
                    traces_data = runs
                    progress.update(search_task, completed=100)
                    
                    # Phase 2: Save results
                    if runs:
                        save_task = progress.add_task("Saving traces...", total=len(runs))
                        
                        try:
                            saved_files = storage.save_traces(runs, project)
                            progress.update(save_task, completed=len(runs))
                        except Exception as e:
                            logger.error(f"Failed to save traces: {e}")
                            raise
                    
                    logger.info(f"Successfully fetched and saved {len(traces_data)} traces")
                    
                except APIError as e:
                    logger.error(f"Failed to search traces: {e}")
                    raise
    
    # Return results
    result = {
        "status": "success",
        "message": "Fetch and save operation completed",
        "parameters": {
            "trace_id": trace_id,
            "project": project,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "limit": limit,
        },
        "traces_found": len(traces_data),
        "files_saved": len(saved_files),
        "saved_paths": [str(path) for path in saved_files],
    }
    
    return result


def fetch_command(
    trace_id: Optional[str] = typer.Option(
        None,
        "--trace-id",
        "-t",
        help="Fetch a specific trace by ID"
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Filter by project name"
    ),
    start_date: Optional[str] = typer.Option(
        None,
        "--start-date",
        help="Start date for trace filtering (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end-date",
        help="End date for trace filtering (YYYY-MM-DD)"
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of traces to fetch"
    ),
) -> None:
    """
    Fetch trace data from LangSmith.
    
    Retrieve trace data from your LangSmith account and save it locally
    for analysis. You can fetch specific traces by ID, filter by project,
    or retrieve traces within a date range.
    
    Examples:
    
      # Fetch a specific trace
      lse fetch --trace-id abc123
      
      # Fetch traces from a project
      lse fetch --project my-project --limit 10
      
      # Fetch traces from date range
      lse fetch --start-date 2024-01-01 --end-date 2024-01-02
    """
    logger.info("Starting fetch command")
    
    # Load and validate configuration
    settings = get_settings()
    settings.validate_required_fields()
    settings.ensure_output_dir()
    
    # Validate parameters
    if limit is not None and limit <= 0:
        raise ValidationError("Limit must be a positive integer.")
    
    start_dt, end_dt = validate_date_range(start_date, end_date)
    
    # Check that at least one filter is provided
    if not any([trace_id, project, start_date, end_date]):
        console.print("[yellow]Warning:[/yellow] No filters specified. This will fetch all available traces.")
        console.print("Consider using --limit to restrict the number of results.")
    
    # Log the operation
    logger.info(f"Fetch parameters: trace_id={trace_id}, project={project}, "
                f"date_range={start_date} to {end_date}, limit={limit}")
    
    try:
        # Execute fetch operation
        result = fetch_traces(
            trace_id=trace_id,
            project=project,
            start_date=start_dt,
            end_date=end_dt,
            limit=limit
        )
        
        # Display results
        if result["status"] == "success":
            console.print(f"[green]✓[/green] {result['message']}")
            
            if trace_id:
                console.print(f"Requested trace ID: {trace_id}")
            
            if result.get("traces_found") is not None:
                console.print(f"Traces found: {result['traces_found']}")
            
            if result.get("files_saved") is not None:
                console.print(f"Files saved: {result['files_saved']}")
            
            console.print(f"Output directory: {settings.output_dir}")
            
            # Show first few saved file paths
            if result.get("saved_paths"):
                paths = result["saved_paths"]
                if len(paths) <= 3:
                    for path in paths:
                        console.print(f"  Saved: {path}")
                else:
                    for path in paths[:2]:
                        console.print(f"  Saved: {path}")
                    console.print(f"  ... and {len(paths) - 2} more files")
            
            if result.get("note"):
                console.print(f"\n[dim]{result['note']}[/dim]")
        else:
            console.print(f"[red]✗[/red] Fetch operation failed: {result.get('message', 'Unknown error')}")
            raise typer.Exit(1)
    
    except Exception as e:
        logger.error(f"Fetch operation failed: {e}")
        raise