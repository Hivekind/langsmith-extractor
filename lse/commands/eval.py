"""Evaluation commands for LangSmith trace analysis."""

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
    TraceExtractor,
    TraceMetadata,
)

app = typer.Typer(help="Evaluation commands for dataset creation and external API integration")
console = Console()


@app.command()
def extract_traces(
    date: str = typer.Option(
        ..., "--date", help="Date in YYYY-MM-DD format (UTC)", show_default=False
    ),
    project: str = typer.Option(
        ..., "--project", help="Project name to extract traces from", show_default=False
    ),
    output: str = typer.Option(
        "/tmp/traces.json", "--output", help="Output JSON file path for trace IDs"
    ),
):
    """Extract trace IDs from local storage that have both AI outputs and human feedback."""
    extractor = TraceExtractor()

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        task = progress.add_task(f"Extracting traces from {project} for {date}...")

        traces = extractor.extract_traces(project=project, date=date)

        progress.update(task, completed=True)

    if not traces:
        console.print("[yellow]No matching traces found[/yellow]")
        raise typer.Exit(1)

    # Save trace metadata to JSON
    output_path = Path(output)
    output_data = {
        "date": date,
        "project": project,
        "trace_count": len(traces),
        "trace_ids": [t.trace_id for t in traces],
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    console.print(f"[green]✓[/green] Extracted {len(traces)} traces to {output}")
    console.print(f"  - Traces with AI output: {sum(1 for t in traces if t.has_ai_output)}")
    console.print(
        f"  - Traces with human feedback: {sum(1 for t in traces if t.has_human_feedback)}"
    )


@app.command()
def create_dataset(
    traces: str = typer.Option(
        ..., "--traces", help="Input JSON file from extract-traces command", show_default=False
    ),
    output: str = typer.Option("/tmp/dataset.jsonl", "--output", help="Output dataset JSONL file"),
    name: str = typer.Option(..., "--name", help="Dataset name", show_default=False),
    eval_type: str = typer.Option(
        ..., "--eval-type", help="Evaluation type: 'token_name' or 'website'", show_default=False
    ),
):
    """Transform extracted traces into LangSmith dataset format."""
    # Validate eval_type parameter
    if eval_type not in ["token_name", "website"]:
        console.print(
            f"[red]Error: --eval-type must be either 'token_name' or 'website', got '{eval_type}'[/red]"
        )
        raise typer.Exit(1)

    traces_path = Path(traces)

    if not traces_path.exists():
        console.print(f"[red]Error: Traces file '{traces}' not found[/red]")
        raise typer.Exit(1)

    # Load trace metadata from JSON
    with open(traces_path, "r") as f:
        traces_data = json.load(f)

    # Create TraceMetadata objects from trace IDs
    trace_metadata = [
        TraceMetadata(trace_id=trace_id, project=traces_data["project"], date=traces_data["date"])
        for trace_id in traces_data["trace_ids"]
    ]

    # Build dataset
    builder = DatasetBuilder()

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        task = progress.add_task(f"Building dataset from {len(trace_metadata)} traces...")

        dataset = builder.build_dataset(
            trace_metadata=trace_metadata,
            dataset_name=name,
            eval_type=eval_type,
        )

        progress.update(task, completed=True)

    # Save dataset to JSONL format (one JSON object per line)
    output_path = Path(output)

    with open(output_path, "w") as f:
        for example in dataset.examples:
            simplified_example = {"inputs": example.inputs, "outputs": example.outputs}
            json.dump(simplified_example, f, separators=(",", ":"))
            f.write("\n")

    console.print(
        f"[green]✓[/green] Created dataset '{name}' with {len(dataset.examples)} examples"
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
