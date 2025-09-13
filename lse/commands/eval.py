"""Evaluation commands for LangSmith trace analysis."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from lse.evaluation import (
    DatasetBuilder,
    EvaluationAPIClient,
    EvaluationDataset,
    LangSmithUploader,
)

app = typer.Typer(help="Evaluation commands for dataset creation and external API integration")
console = Console()


@app.command()
def create_dataset(
    project: str = typer.Option(
        ..., "--project", help="Project name to create dataset from", show_default=False
    ),
    eval_type: str = typer.Option(
        ..., "--eval-type", help="Evaluation type: 'token_name' or 'website'", show_default=False
    ),
    date: Optional[str] = typer.Option(
        None, "--date", help="Single date in YYYY-MM-DD format (UTC)"
    ),
    start_date: Optional[str] = typer.Option(
        None, "--start-date", help="Start date for range in YYYY-MM-DD format (UTC)"
    ),
    end_date: Optional[str] = typer.Option(
        None, "--end-date", help="End date for range in YYYY-MM-DD format (UTC)"
    ),
    output: str = typer.Option("/tmp/dataset.jsonl", "--output", help="Output dataset JSONL file"),
    name: Optional[str] = typer.Option(
        None, "--name", help="Dataset name (auto-generated if not provided)"
    ),
):
    """Create evaluation dataset directly from database with date range support.

    This command queries the database to extract suitable traces and creates
    evaluation datasets. Supports single dates or date ranges.

    Examples:
      # Single date
      lse eval create-dataset --project my-project --date 2025-01-15 --eval-type accuracy

      # Date range
      lse eval create-dataset --project my-project --start-date 2025-01-01 --end-date 2025-01-15 --eval-type accuracy
    """
    # Validate eval_type parameter
    if eval_type not in ["token_name", "website"]:
        console.print(
            f"[red]Error: --eval-type must be either 'token_name' or 'website', got '{eval_type}'[/red]"
        )
        raise typer.Exit(1)

    # Validate date parameters
    if date and (start_date or end_date):
        console.print("[red]Cannot specify both --date and date range options[/red]")
        raise typer.Exit(1)

    if not date and not start_date:
        console.print("[red]Must specify either --date or --start-date[/red]")
        raise typer.Exit(1)

    # Set date range
    if date:
        start_date = end_date = date
    elif start_date and not end_date:
        end_date = start_date

    # Import here to avoid circular imports and make database optional
    from lse.database import create_database_manager

    async def create_dataset_async():
        # Create database-aware dataset builder
        db_manager = await create_database_manager()

        try:
            builder = DatasetBuilder(database=db_manager)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Creating dataset from database for {project}...")

                dataset = await builder.create_dataset_from_db(
                    project=project,
                    start_date=start_date,
                    end_date=end_date,
                    eval_type=eval_type,
                )

                progress.update(task, completed=True)

                # Override dataset name if provided
                if name:
                    dataset.name = name

                return dataset
        finally:
            await db_manager.close()

    dataset = asyncio.run(create_dataset_async())

    # Save dataset to JSONL format (one JSON object per line)
    output_path = Path(output)

    with open(output_path, "w") as f:
        for example in dataset.examples:
            simplified_example = {"inputs": example.inputs, "outputs": example.outputs}
            json.dump(simplified_example, f, separators=(",", ":"))
            f.write("\n")

    console.print(
        f"[green]✓[/green] Created dataset '{dataset.name}' with {len(dataset.examples)} examples"
    )
    console.print(f"  - Saved to: {output}")


@app.command()
def upload(
    dataset: str = typer.Option(
        ..., "--dataset", help="Input dataset JSON or JSONL file", show_default=False
    ),
    name: Optional[str] = typer.Option(None, "--name", help="Override dataset name for upload"),
    description: Optional[str] = typer.Option(
        None, "--description", help="Override dataset description"
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite existing dataset if it exists"
    ),
):
    """Upload dataset to LangSmith."""
    dataset_path = Path(dataset)

    if not dataset_path.exists():
        console.print(f"[red]Error: Dataset file '{dataset}' not found[/red]")
        raise typer.Exit(1)

    # Load dataset - detect format based on content, not just extension
    examples = []

    # Try to detect if it's JSONL format by attempting to parse as single JSON first
    with open(dataset_path, "r") as f:
        content = f.read().strip()

    # Check if it looks like JSONL (multiple lines with JSON objects)
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    is_jsonl = False

    if len(lines) > 1:
        try:
            # Try parsing each line as JSON - if successful, it's likely JSONL
            for line in lines[:2]:  # Check first 2 lines
                json.loads(line)
            is_jsonl = True
        except json.JSONDecodeError:
            is_jsonl = False

    if is_jsonl or dataset_path.suffix.lower() == ".jsonl":
        # JSONL format: one JSON object per line
        for line in lines:
            if line:  # Skip empty lines
                example_data = json.loads(line)
                examples.append(example_data)

        eval_dataset = EvaluationDataset(
            name=name or dataset_path.stem,
            description=description or f"Dataset from {dataset_path.name}",
            examples=examples,
        )
    else:
        # JSON format: single JSON object or array
        dataset_data = json.loads(content)

        # Handle different dataset formats
        if isinstance(dataset_data, list):
            # If dataset_data is a list, it contains examples directly
            eval_dataset = EvaluationDataset(
                name=name or dataset_path.stem, description=description, examples=dataset_data
            )
        else:
            # If dataset_data is a dict, it's already in the expected format
            # Override name/description if provided
            if name:
                dataset_data["name"] = name
            if description:
                dataset_data["description"] = description

            # Reconstruct dataset object
            eval_dataset = EvaluationDataset(**dataset_data)

    # Upload to LangSmith
    uploader = LangSmithUploader()

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        task = progress.add_task(f"Uploading dataset '{eval_dataset.name}' to LangSmith...")

        try:
            dataset_id = uploader.upload_dataset(dataset=eval_dataset, overwrite=overwrite)
            progress.update(task, completed=True)

            console.print("[green]✓[/green] Successfully uploaded dataset")
            console.print(f"  - Dataset ID: {dataset_id}")
            console.print(f"  - Dataset Name: {eval_dataset.name}")
            console.print(f"  - Examples: {len(eval_dataset.examples)}")

        except ValueError as e:
            progress.update(task, completed=True)
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[red]Error uploading dataset: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def run(
    dataset_name: str = typer.Option(
        ..., "--dataset-name", help="Name of dataset in LangSmith", show_default=False
    ),
    experiment_prefix: str = typer.Option(
        ..., "--experiment-prefix", help="Experiment prefix for naming", show_default=False
    ),
    eval_type: str = typer.Option(
        ..., "--eval-type", help="Type of evaluation to run", show_default=False
    ),
    endpoint: Optional[str] = typer.Option(
        None, "--endpoint", help="Override evaluation API endpoint"
    ),
):
    """Initiate evaluation via external evaluation API."""
    client = EvaluationAPIClient(endpoint=endpoint)

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        task = progress.add_task("Sending evaluation request to external API...")

        try:
            response = client.run_evaluation(
                dataset_name=dataset_name, experiment_prefix=experiment_prefix, eval_type=eval_type
            )
            progress.update(task, completed=True)

            console.print("[green]✓[/green] Evaluation request sent successfully!")
            console.print(f"  - Endpoint: {client.endpoint}")
            console.print(f"  - Dataset: {dataset_name}")
            console.print(f"  - Experiment Prefix: {experiment_prefix}")
            console.print(f"  - Eval Type: {eval_type}")
            console.print("  - Status: Initiated")

            if response:
                console.print("\n[bold]API Response:[/bold]")
                console.print(json.dumps(response, indent=2))

        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[red]Error initiating evaluation: {e}[/red]")
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
