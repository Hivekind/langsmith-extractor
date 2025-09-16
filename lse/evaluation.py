"""Evaluation module for LangSmith trace analysis and external API integration."""

import json
import hashlib
from datetime import date
from typing import Any, Dict, List, Optional

import httpx
from langsmith import Client
from pydantic import BaseModel, Field
from rich.console import Console
from sqlalchemy import text

from lse.config import get_settings
from lse.database import DatabaseManager
from lse.storage import TraceStorage

console = Console()


class TraceMetadata(BaseModel):
    """Metadata for LangSmith traces.

    A Trace represents a full end-to-end workflow execution in LangSmith,
    containing one root run and potentially multiple child runs.
    """

    trace_id: str  # The actual LangSmith trace_id (not run_id)
    project: str
    date: str
    has_ai_output: bool = False  # True if any run in this trace has AI output
    has_human_feedback: bool = False  # True if any run in this trace has human feedback


class DatasetExample(BaseModel):
    """Single example in a dataset."""

    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    reference: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class EvaluationDataset(BaseModel):
    """Dataset structure for evaluation."""

    name: str
    description: Optional[str] = None
    examples: List[DatasetExample] = Field(default_factory=list)


class TraceExtractor:
    """Extract suitable traces for evaluation from local storage or database."""

    def __init__(
        self, storage: Optional[TraceStorage] = None, database: Optional[DatabaseManager] = None
    ):
        """Initialize the trace extractor.

        Args:
          storage: TraceStorage instance for accessing stored traces (file-based)
          database: DatabaseManager instance for accessing database (database-based)
        """
        self.storage = storage or TraceStorage(get_settings())
        self.database = database

    def extract_traces(self, project: str, date: str) -> List[TraceMetadata]:
        """Extract traces that meet filtering criteria from stored run data.

        Note: Each stored JSON file represents a LangSmith Run (with run_id),
        but multiple runs can belong to the same Trace (with trace_id).
        This method groups runs by trace_id and applies filtering criteria.

        Filtering criteria:
        - Must have a final verdict attached via feedback
        - Output final_decision must match feedback verdict (PASS-PASS or FAIL-FAIL)

        Args:
          project: Project name to extract traces from
          date: Date in YYYY-MM-DD format (UTC)

        Returns:
          List of unique trace metadata that meet filtering criteria
        """
        run_dir = self.storage.output_dir / project / date

        if not run_dir.exists():
            console.print(f"[yellow]No run data found for {project} on {date}[/yellow]")
            return []

        # Dictionary to store traces by trace_id, aggregating run data
        traces_by_trace_id = {}

        for run_file in run_dir.glob("*.json"):
            if run_file.name == "_summary.json":
                continue  # Skip summary file

            try:
                with open(run_file, "r") as f:
                    run_data = json.load(f)

                # Extract the actual trace_id (not run_id)
                run_info = run_data.get("trace", {})  # This field contains run info, not trace info
                trace_id = run_info.get("trace_id", "")

                if not trace_id:
                    continue

                # Extract request_id from input_data (only available in root runs typically)
                request_id = None
                inputs = run_info.get("inputs", {})
                input_data = inputs.get("input_data", {})
                if isinstance(input_data, dict):
                    request_id = input_data.get("request_id", "")

                # Extract timestamp for comparison
                run_start_time = run_info.get("start_time", "")

                # Create or update trace metadata
                if trace_id not in traces_by_trace_id:
                    metadata = TraceMetadata(trace_id=trace_id, project=project, date=date)
                    traces_by_trace_id[trace_id] = {
                        "metadata": metadata,
                        "start_time": run_start_time,
                        "request_id": request_id,
                        "has_ai_output": False,
                        "has_human_feedback": False,
                        "meets_criteria": False,
                        "runs_processed": 0,
                    }

                trace_entry = traces_by_trace_id[trace_id]
                trace_entry["runs_processed"] += 1

                # Update trace-level metadata by aggregating from all runs
                # Keep the earliest start time for the trace
                if run_start_time < trace_entry["start_time"]:
                    trace_entry["start_time"] = run_start_time

                # If we don't have a request_id yet, try to get it from this run
                if not trace_entry["request_id"] and request_id:
                    trace_entry["request_id"] = request_id

                # Check for AI output in this run
                if self._has_ai_output(run_data):
                    trace_entry["has_ai_output"] = True
                    trace_entry["metadata"].has_ai_output = True

                # Check for human feedback in this run
                if self._has_human_feedback(run_data):
                    trace_entry["has_human_feedback"] = True
                    trace_entry["metadata"].has_human_feedback = True

                # Check if this run meets the filtering criteria
                if self._meets_filtering_criteria(run_data):
                    trace_entry["meets_criteria"] = True

            except (json.JSONDecodeError, KeyError) as e:
                console.print(f"[yellow]Error processing {run_file.name}: {e}[/yellow]")
                continue

        # Filter traces that meet the filtering criteria
        filtered_traces = {
            trace_id: trace_entry
            for trace_id, trace_entry in traces_by_trace_id.items()
            if trace_entry["meets_criteria"]
        }

        # Now apply deduplication logic based on request_id if available
        final_traces = {}

        for trace_id, trace_entry in filtered_traces.items():
            request_id = trace_entry["request_id"]
            dedup_key = request_id if request_id else trace_id

            if dedup_key not in final_traces:
                final_traces[dedup_key] = trace_entry
            else:
                # Keep the trace with the earlier start time (original trace)
                existing_time = final_traces[dedup_key]["start_time"]
                current_time = trace_entry["start_time"]
                if current_time < existing_time:
                    final_traces[dedup_key] = trace_entry

        # Extract just the metadata from our final traces
        traces = [entry["metadata"] for entry in final_traces.values()]

        return traces

    async def extract_traces_from_db(
        self,
        project: str,
        start_date: str,
        end_date: Optional[str] = None,
        eval_type: Optional[str] = None,
    ) -> List[TraceMetadata]:
        """Extract traces from database that meet evaluation criteria.

        This method queries runs and aggregates them by trace_id to reconstruct traces.

        Args:
            project: Project name to extract traces from
            start_date: Start date in YYYY-MM-DD format (UTC)
            end_date: End date in YYYY-MM-DD format (UTC), defaults to start_date

        Returns:
            List of trace metadata meeting evaluation criteria
        """
        if not self.database:
            raise ValueError("DatabaseManager is required for database-based extraction")

        end_date = end_date or start_date

        # Convert string dates to date objects for PostgreSQL compatibility
        start_date_obj = date.fromisoformat(start_date)
        end_date_obj = date.fromisoformat(end_date)

        async with self.database.get_session() as session:
            # Query all runs for the date range, grouped by trace_id
            result = await session.execute(
                text("""
                SELECT 
                    trace_id, 
                    project, 
                    run_date,
                    array_agg(data ORDER BY created_at) as run_data_array,
                    COUNT(*) as run_count
                FROM runs 
                WHERE project = :project 
                  AND run_date BETWEEN :start_date AND :end_date
                  AND trace_id IS NOT NULL
                GROUP BY trace_id, project, run_date
                HAVING COUNT(*) >= 1
                ORDER BY run_date, trace_id
                """),
                {"project": project, "start_date": start_date_obj, "end_date": end_date_obj},
            )

            traces = []
            for row in result.fetchall():
                # Aggregate run data to evaluate trace-level criteria
                trace_evaluation = self._evaluate_trace_from_runs(
                    row[3], eval_type
                )  # run_data_array

                if trace_evaluation["meets_criteria"]:
                    trace_metadata = TraceMetadata(
                        trace_id=row[0],  # trace_id
                        project=row[1],  # project
                        date=row[2].strftime("%Y-%m-%d"),  # run_date
                        has_ai_output=trace_evaluation["has_ai_output"],
                        has_human_feedback=trace_evaluation["has_human_feedback"],
                    )
                    traces.append(trace_metadata)

            return traces

    def _evaluate_trace_from_runs(
        self, run_data_array: List[dict], eval_type: Optional[str] = None
    ) -> dict:
        """Evaluate a trace based on aggregated run data.

        Args:
            run_data_array: List of run data JSONB objects belonging to same trace

        Returns:
            Dict with evaluation results for the trace
        """
        has_ai_output = False
        has_human_feedback = False
        meets_criteria = False

        # Aggregate evaluation criteria across all runs in the trace
        for run_data in run_data_array:
            if self._has_ai_output(run_data):
                has_ai_output = True

            if self._has_human_feedback(run_data):
                has_human_feedback = True

            # Check if any run in this trace meets filtering criteria
            if self._meets_filtering_criteria(run_data, eval_type):
                meets_criteria = True

        return {
            "has_ai_output": has_ai_output,
            "has_human_feedback": has_human_feedback,
            "meets_criteria": meets_criteria,
        }

    def _has_ai_output(self, trace_data: Dict[str, Any]) -> bool:
        """Check if trace contains AI output.

        Args:
          trace_data: Raw trace data (either database format or file format)

        Returns:
          True if trace contains AI output
        """
        # Handle both database format (direct) and file format (wrapped in "trace" key)
        if "trace" in trace_data:
            # File format: {"metadata": ..., "trace": {...}}
            trace = trace_data["trace"]
        else:
            # Database format: direct run data
            trace = trace_data

        # Check outputs field at trace level (primary location)
        outputs = trace.get("outputs", {})
        if outputs and isinstance(outputs, dict) and outputs:
            return True

        # Check outputs field at root level (backup)
        outputs = trace_data.get("outputs", {})
        if outputs and isinstance(outputs, dict):
            # Look for common AI output fields
            ai_fields = ["ai_recommendation", "response", "output", "completion"]
            for field in ai_fields:
                if field in outputs:
                    return True

        # Check for outputs in run tree
        if "run" in trace_data:
            run_outputs = trace_data["run"].get("outputs", {})
            if run_outputs and isinstance(run_outputs, dict):
                return True

        return False

    def _has_human_feedback(self, trace_data: Dict[str, Any]) -> bool:
        """Check if trace contains human feedback.

        Args:
          trace_data: Raw trace data (either database format or file format)

        Returns:
          True if trace contains human feedback
        """
        # Handle both database format (direct) and file format (wrapped in "trace" key)
        if "trace" in trace_data:
            # File format: {"metadata": ..., "trace": {...}}
            trace = trace_data["trace"]
        else:
            # Database format: direct run data
            trace = trace_data

        # Check for feedback_stats.final_verdict (primary location for human feedback)
        feedback_stats = trace.get("feedback_stats", {})
        if feedback_stats and "final_verdict" in feedback_stats:
            return True

        # Check for feedback field
        feedback = trace_data.get("feedback", [])
        if feedback:
            return True

        # Check for feedback in specific fields
        outputs = trace_data.get("outputs", {})
        if outputs and isinstance(outputs, dict) and "human_verdict" in outputs:
            return True

        reference = trace_data.get("reference", {})
        if reference and isinstance(reference, dict) and "human_feedback" in reference:
            return True

        return False

    def _has_final_verdict_feedback(self, trace_data: Dict[str, Any]) -> bool:
        """Check if trace has final verdict feedback.

        Database format: trace_data["feedback_stats"]["final_verdict"]["comments"][0]
        File format: trace_data["trace"]["feedback_stats"]["final_verdict"]

        Args:
          trace_data: Raw trace data (either database format or file format)

        Returns:
          True if trace has final verdict feedback
        """
        # Handle both database format (direct) and file format (wrapped in "trace" key)
        if "trace" in trace_data:
            # File format: {"metadata": ..., "trace": {...}}
            trace = trace_data["trace"]
        else:
            # Database format: direct run data
            trace = trace_data

        # Check for feedback_stats.final_verdict (both database and file format)
        feedback_stats = trace.get("feedback_stats", {})
        if feedback_stats and "final_verdict" in feedback_stats:
            final_verdict = feedback_stats.get("final_verdict")
            if final_verdict:
                # Check for comments containing "Human verdict:" (primary method)
                comments = final_verdict.get("comments", [])
                if comments and any("Human verdict:" in str(comment) for comment in comments):
                    return True
                # Also check for direct verdict field (fallback)
                if "verdict" in final_verdict:
                    return True

        # Check for feedback with final_verdict (fallback)
        feedback = trace_data.get("feedback", [])
        if isinstance(feedback, list):
            for fb in feedback:
                if isinstance(fb, dict) and "final_verdict" in fb:
                    final_verdict = fb.get("final_verdict")
                    if final_verdict and "verdict" in final_verdict:
                        return True

        return False

    def _get_feedback_verdict(self, trace_data: Dict[str, Any]) -> Optional[str]:
        """Extract the verdict from feedback.

        Database format: trace_data["feedback_stats"]["final_verdict"]["comments"][0]
        File format: trace_data["trace"]["feedback_stats"]["final_verdict"]["comments"][0]
        Expected format: "Human verdict: {FINAL_VERDICT}"

        Args:
          trace_data: Raw trace data (either database format or file format)

        Returns:
          Feedback verdict string (PASS/FAIL) or None if not found
        """
        # Handle both database format (direct) and file format (wrapped in "trace" key)
        if "trace" in trace_data:
            # File format: {"metadata": ..., "trace": {...}}
            trace = trace_data["trace"]
        else:
            # Database format: direct run data
            trace = trace_data

        # Check for feedback_stats.final_verdict (primary location)
        feedback_stats = trace.get("feedback_stats", {})
        if feedback_stats and "final_verdict" in feedback_stats:
            final_verdict = feedback_stats.get("final_verdict")
            if final_verdict:
                # Check for comments containing "Human verdict:" (primary method)
                comments = final_verdict.get("comments", [])
                if comments:
                    for comment in comments:
                        comment_str = str(comment)
                        if "Human verdict:" in comment_str:
                            # Extract PASS or FAIL from "Human verdict: FAIL"
                            verdict = comment_str.split("Human verdict:")[-1].strip()
                            if verdict in ["PASS", "FAIL"]:
                                return verdict
                # Also check for direct verdict field (fallback)
                if "verdict" in final_verdict:
                    return final_verdict.get("verdict")

        # Check for feedback with final_verdict (fallback)
        feedback = trace_data.get("feedback", [])
        if isinstance(feedback, list):
            for fb in feedback:
                if isinstance(fb, dict) and "final_verdict" in fb:
                    final_verdict = fb.get("final_verdict")
                    if final_verdict and "verdict" in final_verdict:
                        return final_verdict.get("verdict")

        return None

    def _get_output_decision_and_confidence(
        self, trace_data: Dict[str, Any]
    ) -> tuple[Optional[str], Optional[float]]:
        """Extract final_decision and confidence from outputs.

        Database format: trace_data["outputs"]["final_decision"]
        File format: trace_data["trace"]["outputs"]["final_decision"]

        Args:
          trace_data: Raw trace data (either database format or file format)

        Returns:
          Tuple of (final_decision, confidence) or (None, None) if not found
        """
        # Handle both database format (direct) and file format (wrapped in "trace" key)
        if "trace" in trace_data:
            # File format: {"metadata": ..., "trace": {...}}
            trace = trace_data["trace"]
        else:
            # Database format: direct run data
            trace = trace_data

        # Check trace level outputs first (both database and file format)
        outputs = trace.get("outputs", {})

        # Fallback to top-level outputs (alternative structure)
        if not outputs:
            outputs = trace_data.get("outputs", {})

        if not outputs or outputs is None:
            return None, None

        final_decision = outputs.get("final_decision")
        confidence = outputs.get("confidence")

        # Convert confidence to float if it's a string
        if confidence is not None:
            try:
                confidence = float(confidence)
            except (ValueError, TypeError):
                confidence = None

        return final_decision, confidence

    def _meets_filtering_criteria(
        self, run_data: Dict[str, Any], eval_type: Optional[str] = None
    ) -> bool:
        """Check if a run meets filtering criteria for dataset inclusion.

        Availability eval_type uses simplified filtering - just needs website_url.
        Other eval_types use existing strict criteria.

        Args:
          run_data: Raw run data
          eval_type: Evaluation type (affects filtering criteria)

        Returns:
          True if run meets criteria for the specified eval_type
        """
        if eval_type == "availability":
            # Simplified criteria for availability: just needs website_url
            return self._has_website_url(run_data)
        else:
            # Existing strict criteria for token_name and website eval_types
            return (
                self._has_final_verdict_feedback(run_data)
                and self._has_matching_verdicts(run_data)
                and self._has_sufficient_confidence(run_data)
            )

    def _has_website_url(self, run_data: Dict[str, Any]) -> bool:
        """Check if run_data contains website_url parameter.

        Args:
          run_data: Raw run data

        Returns:
          True if website_url is found in the run data
        """
        # Check direct inputs
        inputs = run_data.get("inputs", {})
        if "website_url" in inputs:
            return True

        # Check for nested website_url in various potential locations
        # Common patterns in due-diligence API requests
        if isinstance(inputs, dict):
            # Check nested input structures
            for key, value in inputs.items():
                if isinstance(value, dict) and "website_url" in value:
                    return True

        return False

    def _has_matching_verdicts(self, run_data: Dict[str, Any]) -> bool:
        """Check if feedback verdict matches output decision.

        Returns:
          True if verdicts match (PASS-PASS or FAIL-FAIL)
        """
        feedback_verdict = self._get_feedback_verdict(run_data)
        final_decision, _ = self._get_output_decision_and_confidence(run_data)

        # Must have both feedback verdict and output decision
        if not feedback_verdict or not final_decision:
            return False

        # Must have matching verdicts (PASS-PASS or FAIL-FAIL)
        return feedback_verdict == final_decision

    def _has_sufficient_confidence(self, run_data: Dict[str, Any]) -> bool:
        """Check if run has sufficient confidence score.

        Returns:
          True if confidence >= 0.7
        """
        _, confidence = self._get_output_decision_and_confidence(run_data)
        return confidence is not None and confidence >= 0.7


class DatasetBuilder:
    """Build evaluation datasets from extracted traces."""

    def __init__(
        self, storage: Optional[TraceStorage] = None, database: Optional[DatabaseManager] = None
    ):
        """Initialize the dataset builder.

        Args:
          storage: TraceStorage instance for accessing stored traces
          database: DatabaseManager instance for accessing database
        """
        self.storage = storage or TraceStorage(get_settings())
        self.database = database

    def build_dataset(
        self,
        trace_metadata: List[TraceMetadata],
        dataset_name: str,
        description: Optional[str] = None,
        eval_type: Optional[str] = None,
    ) -> EvaluationDataset:
        """Build a dataset from trace metadata.

        Args:
          trace_metadata: List of trace metadata to include
          dataset_name: Name for the dataset
          description: Optional dataset description
          eval_type: Optional evaluation type for format-specific generation

        Returns:
          Built evaluation dataset
        """
        dataset = EvaluationDataset(
            name=dataset_name,
            description=description or f"Dataset created from {len(trace_metadata)} traces",
        )

        for metadata in trace_metadata:
            example = self._build_example(metadata, eval_type)
            if example:
                dataset.examples.append(example)

        return dataset

    async def create_dataset_from_db(
        self,
        project: str,
        start_date: str,
        end_date: str,
        eval_type: str,
    ) -> EvaluationDataset:
        """Create evaluation dataset directly from database.

        Args:
            project: Project name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            eval_type: Evaluation type for formatting

        Returns:
            Complete evaluation dataset ready for upload
        """
        if not self.database:
            raise ValueError("DatabaseManager is required for database-based dataset creation")

        # Use the TraceExtractor to get suitable traces
        extractor = TraceExtractor(database=self.database)
        trace_metadata = await extractor.extract_traces_from_db(
            project=project, start_date=start_date, end_date=end_date, eval_type=eval_type
        )

        # Build dataset examples
        examples = []
        async with self.database.get_session() as session:
            for metadata in trace_metadata:
                # Get all runs for this trace from database
                result = await session.execute(
                    text("""
                    SELECT data FROM runs 
                    WHERE trace_id = :trace_id 
                      AND project = :project 
                      AND run_date = :date
                    ORDER BY created_at
                    """),
                    {
                        "trace_id": metadata.trace_id,
                        "project": metadata.project,
                        "date": date.fromisoformat(metadata.date),
                    },
                )

                run_data_list = [row.data for row in result.fetchall()]
                if run_data_list:
                    example = self._build_example_from_runs(
                        trace_metadata=metadata, run_data_list=run_data_list, eval_type=eval_type
                    )
                    if example:
                        examples.append(example)

        # Create dataset
        dataset_name = f"{project}_{eval_type}_{start_date}_{end_date}"
        return EvaluationDataset(
            name=dataset_name,
            description=f"Evaluation dataset for {project} from {start_date} to {end_date}",
            examples=examples,
        )

    def _build_example_from_runs(
        self,
        trace_metadata: TraceMetadata,
        run_data_list: List[dict],
        eval_type: Optional[str] = None,
    ) -> Optional[DatasetExample]:
        """Build dataset example from database run data.

        Args:
            trace_metadata: Trace metadata
            run_data_list: List of run data from database
            eval_type: Evaluation type for formatting

        Returns:
            Dataset example or None if trace cannot be processed
        """
        try:
            # Use root run priority extraction for availability eval_type
            if eval_type == "availability":
                root_run, child_runs = self._identify_trace_hierarchy(run_data_list)
                all_inputs, all_outputs, all_reference = self._extract_with_priority(
                    root_run, child_runs, eval_type
                )
            else:
                # Use existing logic for other eval_types (token_name, website)
                all_inputs = {}
                all_outputs = {}
                all_reference = {}

                for run_data in run_data_list:
                    # Extract inputs (typically from root run only)
                    run_inputs = self._extract_inputs(run_data)
                    self._deep_merge_dict(all_inputs, run_inputs)

                    # Extract outputs (from all runs, but prioritize final outputs)
                    run_outputs = self._extract_outputs(run_data)
                    self._deep_merge_dict(all_outputs, run_outputs)

                    # Extract reference data (human feedback, verdicts)
                    run_reference = self._extract_reference(run_data)
                    self._deep_merge_dict(all_reference, run_reference)

            # Apply format-specific transformations if needed
            if eval_type:
                all_inputs, all_outputs, all_reference = self._apply_format(
                    all_inputs, all_outputs, all_reference, eval_type
                )

            return DatasetExample(
                inputs=all_inputs,
                outputs=all_outputs,
                reference=all_reference if all_reference else None,
                metadata={
                    "trace_id": trace_metadata.trace_id,
                    "project": trace_metadata.project,
                    "date": trace_metadata.date,
                    "eval_type": eval_type,
                },
            )

        except (json.JSONDecodeError, KeyError) as e:
            console.print(
                f"[yellow]Error building example for {trace_metadata.trace_id}: {e}[/yellow]"
            )
            return None

    def _build_example(
        self, metadata: TraceMetadata, eval_type: Optional[str] = None
    ) -> Optional[DatasetExample]:
        """Build a single dataset example from trace metadata.

        Aggregates data from all runs belonging to the trace.

        Args:
          metadata: Trace metadata
          eval_type: Optional evaluation type for format-specific generation

        Returns:
          Dataset example or None if trace cannot be processed
        """
        # Find all run files belonging to this trace
        run_dir = self.storage.output_dir / metadata.project / metadata.date

        if not run_dir.exists():
            return None

        # Collect all run files that belong to this trace_id
        trace_runs = []
        for run_file in run_dir.glob("*.json"):
            if run_file.name == "_summary.json":
                continue

            try:
                with open(run_file, "r") as f:
                    run_data = json.load(f)

                # Check if this run belongs to our trace
                run_info = run_data.get("trace", {})
                run_trace_id = run_info.get("trace_id", "")

                if run_trace_id == metadata.trace_id:
                    trace_runs.append(run_data)
            except (json.JSONDecodeError, KeyError):
                continue

        if not trace_runs:
            return None

        try:
            # Aggregate inputs, outputs, and reference from all runs
            all_inputs = {}
            all_outputs = {}
            all_reference = {}

            for run_data in trace_runs:
                # Extract inputs (typically from root run only)
                run_inputs = self._extract_inputs(run_data)
                # Deep merge input_data to preserve all fields
                if "input_data" in run_inputs and "input_data" in all_inputs:
                    # Merge input_data dictionaries, preserving existing fields
                    for key, value in run_inputs["input_data"].items():
                        if value:  # Only update if the value is not empty/None
                            all_inputs["input_data"][key] = value
                elif "input_data" in run_inputs:
                    # First input_data encountered
                    all_inputs["input_data"] = run_inputs["input_data"].copy()
                # Update other top-level input fields
                for key, value in run_inputs.items():
                    if key != "input_data":
                        all_inputs[key] = value

                # Extract outputs (aggregate from all runs)
                run_outputs = self._extract_outputs(run_data)
                all_outputs.update(run_outputs)

                # Extract reference (aggregate from all runs)
                run_reference = self._extract_reference(run_data)
                all_reference.update(run_reference)

            # Build metadata
            example_metadata = {
                "trace_id": metadata.trace_id,
                "project": metadata.project,
                "date": metadata.date,
                "runs_count": len(trace_runs),
            }

            # Apply format-specific transformations if needed
            if eval_type:
                all_inputs, all_outputs, all_reference = self._apply_format(
                    all_inputs, all_outputs, all_reference, eval_type
                )

            return DatasetExample(
                inputs=all_inputs,
                outputs=all_outputs,
                reference=all_reference,
                metadata=example_metadata,
            )

        except (json.JSONDecodeError, KeyError) as e:
            console.print(f"[yellow]Error building example for {metadata.trace_id}: {e}[/yellow]")
            return None

    def _extract_inputs(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract clean input fields from trace data."""
        inputs = {}

        # Handle both database format (direct) and file format (wrapped)
        if "trace" in trace_data:
            trace = trace_data["trace"]
        else:
            trace = trace_data

        # Extract from input_data (primary location)
        trace_inputs = trace.get("inputs", {})
        input_data = trace_inputs.get("input_data", {})

        if isinstance(input_data, dict):
            # Extract standard fields that appear in both eval types
            for field in ["name", "description"]:
                if field in input_data:
                    inputs[field] = input_data[field]

            # Extract crypto_symbol as symbol
            if "crypto_symbol" in input_data:
                inputs["symbol"] = input_data["crypto_symbol"]
            elif "symbol" in input_data:
                inputs["symbol"] = input_data["symbol"]

            # Extract website-specific fields
            for field in ["website_url", "network", "contract_address", "social_profiles"]:
                if field in input_data:
                    inputs[field] = input_data[field]

        # Fallback: try to extract from direct fields if input_data not available
        if not inputs and trace_inputs:
            # Try direct field extraction as backup
            for field in [
                "name",
                "description",
                "website_url",
                "network",
                "contract_address",
                "social_profiles",
            ]:
                if field in trace_inputs:
                    inputs[field] = trace_inputs[field]

            # Handle symbol/crypto_symbol mapping
            if "crypto_symbol" in trace_inputs:
                inputs["symbol"] = trace_inputs["crypto_symbol"]
            elif "symbol" in trace_inputs:
                inputs["symbol"] = trace_inputs["symbol"]

        return inputs

    def _extract_outputs(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract clean evaluation outputs from trace data."""
        outputs = {}

        # Handle both database format (direct) and file format (wrapped)
        if "trace" in trace_data:
            trace = trace_data["trace"]
        else:
            trace = trace_data

        # Get outputs from trace level
        trace_outputs = trace.get("outputs", {})
        if not trace_outputs:
            # Fallback to top-level outputs
            trace_outputs = trace_data.get("outputs", {})

        # Handle None outputs (e.g., from error traces)
        if trace_outputs is None:
            trace_outputs = {}

        # Navigate through nested analysis structures
        name_analysis = trace_outputs.get("name_analysis", {}) or {}
        website_analysis = trace_outputs.get("website_analysis", {}) or {}

        # Extract boolean evaluation results
        self._extract_boolean_results(outputs, name_analysis, website_analysis, trace_outputs)

        return outputs

    def _extract_boolean_results(
        self, outputs: dict, name_analysis: dict, website_analysis: dict, trace_outputs: dict
    ):
        """Extract boolean evaluation results from nested structures."""

        # Extract is_meme - use the first available value (don't rely on 'or' for False values)
        meme_check = None
        if "meme_check" in name_analysis:
            meme_check = name_analysis["meme_check"]
        elif "meme_check" in website_analysis:
            meme_check = website_analysis["meme_check"]
        elif "meme_check" in trace_outputs:
            meme_check = trace_outputs["meme_check"]

        if isinstance(meme_check, dict):
            outputs["is_meme"] = bool(meme_check.get("is_meme", False))
        elif meme_check is not None:
            outputs["is_meme"] = bool(meme_check)
        else:
            outputs["is_meme"] = bool(trace_outputs.get("is_meme", False))

        # Extract is_explicit - use the first available value
        explicit_check = None
        if "explicit_check" in name_analysis:
            explicit_check = name_analysis["explicit_check"]
        elif "explicit_check" in website_analysis:
            explicit_check = website_analysis["explicit_check"]
        elif "explicit_check" in trace_outputs:
            explicit_check = trace_outputs["explicit_check"]

        if isinstance(explicit_check, dict):
            outputs["is_explicit"] = bool(explicit_check.get("is_explicit", False))
        elif explicit_check is not None:
            outputs["is_explicit"] = bool(explicit_check)
        else:
            outputs["is_explicit"] = bool(trace_outputs.get("is_explicit", False))

        # Extract trademark/conflict info - use the first available value
        trademark_check = None
        if "trademark_check" in name_analysis:
            trademark_check = name_analysis["trademark_check"]
        elif "trademark_check" in website_analysis:
            trademark_check = website_analysis["trademark_check"]
        elif "trademark_check" in trace_outputs:
            trademark_check = trace_outputs["trademark_check"]

        if isinstance(trademark_check, dict):
            outputs["has_conflict"] = bool(trademark_check.get("has_conflict", False))
            outputs["has_trademark_conflict"] = bool(trademark_check.get("has_conflict", False))
        else:
            outputs["has_conflict"] = bool(trace_outputs.get("has_conflict", False))
            outputs["has_trademark_conflict"] = bool(
                trace_outputs.get(
                    "has_trademark_conflict", trace_outputs.get("has_conflict", False)
                )
            )

        # Website-specific fields - check both analysis and direct fields
        if website_analysis or trace_outputs.get("is_available") is not None:
            outputs["is_available"] = bool(
                website_analysis.get("is_available", trace_outputs.get("is_available", True))
            )

            malicious_check = website_analysis.get("malicious_check")
            if isinstance(malicious_check, dict):
                outputs["is_malicious"] = bool(malicious_check.get("is_dangerous", False))
            else:
                outputs["is_malicious"] = bool(trace_outputs.get("is_malicious", False))

        # Availability-specific fields (for notes/error messages)
        self._extract_availability_notes(outputs, website_analysis, trace_outputs)

    def _extract_availability_notes(
        self, outputs: dict, website_analysis: dict, trace_outputs: dict
    ):
        """Extract availability notes/error messages for availability evaluation.

        Note: As of Phase 15, this method operates on root-run-prioritized data,
        ensuring that availability status and notes reflect the authoritative
        root run assessment rather than being contaminated by incomplete child runs.
        """
        notes = ""

        # Check for availability notes in website_analysis
        if website_analysis:
            # Look for error messages or availability notes
            if "error_message" in website_analysis:
                notes = website_analysis["error_message"]
            elif "availability_notes" in website_analysis:
                notes = website_analysis["availability_notes"]
            elif "notes" in website_analysis:
                notes = website_analysis["notes"]

        # Fallback to trace outputs
        if not notes and trace_outputs:
            if "error_message" in trace_outputs:
                notes = trace_outputs["error_message"]
            elif "availability_notes" in trace_outputs:
                notes = trace_outputs["availability_notes"]
            elif "notes" in trace_outputs:
                notes = trace_outputs["notes"]

        # Generate descriptive notes based on available data and inferred availability
        if not notes:
            is_available = outputs.get("is_available", False)

            # Try to infer availability from the presence of scraped data or analysis results
            has_project_info = bool(trace_outputs.get("project_info"))
            has_social_links = bool(trace_outputs.get("social_links"))
            has_page_links = bool(trace_outputs.get("page_links"))
            has_website_analysis = bool(trace_outputs.get("website_analysis"))
            has_name_analysis = bool(trace_outputs.get("name_analysis"))

            # Check if this appears to be a successful scraping/analysis result
            if has_project_info or has_social_links or has_page_links:
                notes = "Website accessible - content successfully scraped"
                outputs["is_available"] = True
            elif has_website_analysis or has_name_analysis:
                notes = "Website accessible - analysis completed successfully"
                outputs["is_available"] = True
            elif trace_outputs.get("final_decision") == "PASS":
                notes = "Website accessible - evaluation completed with PASS decision"
                outputs["is_available"] = True
            elif trace_outputs.get("final_decision") == "FAIL":
                notes = "Website accessibility issues - evaluation resulted in FAIL decision"
                outputs["is_available"] = False
            elif is_available:
                notes = "Website appears to be accessible"
            else:
                # Check for potential error indicators
                outputs_str = str(trace_outputs).lower()
                if "error" in outputs_str or "failed" in outputs_str or "timeout" in outputs_str:
                    notes = "Website may be unavailable - errors detected during access"
                    outputs["is_available"] = False
                else:
                    notes = "Website availability status unclear"

        outputs["notes"] = str(notes) if notes else ""

    def _extract_reference(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract human feedback/reference from trace data."""
        reference = {}

        # Check feedback field
        if "feedback" in trace_data and trace_data["feedback"]:
            # Assuming feedback is a list of feedback objects
            for feedback in trace_data["feedback"]:
                if isinstance(feedback, dict):
                    reference["feedback_score"] = feedback.get("score")
                    reference["feedback_value"] = feedback.get("value")
                    reference["feedback_comment"] = feedback.get("comment")

        # Check for human verdict in outputs
        if (
            "outputs" in trace_data
            and trace_data["outputs"] is not None
            and "human_verdict" in trace_data["outputs"]
        ):
            reference["human_verdict"] = trace_data["outputs"]["human_verdict"]

        return reference

    def _apply_format(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        reference: Dict[str, Any],
        eval_type: str,
    ) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Apply format-specific transformations based on eval_type.

        Args:
          inputs: Input data
          outputs: Output data
          reference: Reference data
          eval_type: Evaluation type

        Returns:
          Transformed inputs, outputs, and reference
        """
        if eval_type == "token_name":
            return self._format_token_name(inputs, outputs, reference)
        elif eval_type == "website":
            return self._format_website(inputs, outputs, reference)
        elif eval_type == "availability":
            return self._format_availability(inputs, outputs, reference)
        else:
            # For unknown eval_types, return as-is
            return inputs, outputs, reference

    def _format_token_name(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        reference: Dict[str, Any],
    ) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Format data for token_name evaluation type with clean extracted data.

        Args:
          inputs: Clean input data (already extracted by _extract_inputs)
          outputs: Clean output data (already extracted by _extract_outputs)
          reference: Reference data

        Returns:
          Formatted inputs, outputs, and reference for token_name evaluation
        """
        # Format inputs - data is already clean from _extract_inputs()
        formatted_inputs = {
            "name": inputs.get("name", ""),
            "symbol": inputs.get("symbol", ""),
            "description": inputs.get("description", ""),
        }

        # Format outputs - data is already clean from _extract_outputs()
        formatted_outputs = {
            "is_meme": outputs.get("is_meme", False),
            "is_explicit": outputs.get("is_explicit", False),
            "has_conflict": outputs.get("has_conflict", False),
        }

        formatted_reference = reference

        return formatted_inputs, formatted_outputs, formatted_reference

    def _format_website(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        reference: Dict[str, Any],
    ) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Format data for website evaluation type with clean extracted data.

        Args:
          inputs: Clean input data (already extracted by _extract_inputs)
          outputs: Clean output data (already extracted by _extract_outputs)
          reference: Reference data

        Returns:
          Formatted inputs, outputs, and reference for website evaluation
        """
        # Format inputs - data is already clean from _extract_inputs()
        formatted_inputs = {
            "name": inputs.get("name", ""),
            "symbol": inputs.get("symbol", ""),
            "network": inputs.get("network", ""),
            "description": inputs.get("description", ""),
            "website_url": inputs.get("website_url", ""),
            "social_profiles": inputs.get("social_profiles", []),
            "contract_address": inputs.get("contract_address", ""),
        }

        # Format outputs - data is already clean from _extract_outputs()
        formatted_outputs = {
            "is_meme": outputs.get("is_meme", False),
            "is_explicit": outputs.get("is_explicit", False),
            "is_available": outputs.get("is_available", True),
            "is_malicious": outputs.get("is_malicious", False),
            "has_trademark_conflict": outputs.get("has_trademark_conflict", False),
        }

        return formatted_inputs, formatted_outputs, reference

    def _format_availability(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        reference: Dict[str, Any],
    ) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Format data for availability evaluation type.

        Args:
          inputs: Clean input data (already extracted by _extract_inputs)
          outputs: Clean output data (already extracted by _extract_outputs)
          reference: Reference data

        Returns:
          Formatted inputs, outputs, and reference for availability evaluation
        """
        # Format inputs - extract website_url only
        formatted_inputs = {"website_url": inputs.get("website_url", "")}

        # Format outputs - boolean availability with notes
        formatted_outputs = {
            "is_available": outputs.get("is_available", False),
            "notes": outputs.get("notes", ""),
        }

        # Reference data minimal (availability doesn't use complex feedback)
        formatted_reference = reference

        return formatted_inputs, formatted_outputs, formatted_reference

    def _deep_merge_dict(self, target: dict, source: dict) -> None:
        """Deep merge source dictionary into target dictionary.

        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge_dict(target[key], value)
            else:
                target[key] = value

    def _identify_trace_hierarchy(
        self, run_data_list: List[dict]
    ) -> tuple[Optional[dict], List[dict]]:
        """Separate root run from child runs in trace processing.

        Args:
            run_data_list: List of run data from database

        Returns:
            Tuple of (root_run, child_runs_list)
        """
        root_run = None
        child_runs = []

        for run_data in run_data_list:
            # Root run is identified when trace_id equals the run's id (not run_id)
            if run_data.get("trace_id") == run_data.get("id"):
                if root_run is not None:
                    console.print(
                        f"[yellow]Warning: Multiple root runs found in trace {run_data.get('trace_id')}[/yellow]"
                    )
                root_run = run_data
            else:
                child_runs.append(run_data)

        if root_run is None and run_data_list:
            # Debug level - common case where traces don't have root runs
            # Using fallback logic (child runs) is normal and working correctly
            pass  # Removed noisy warning - fallback behavior is functioning as intended

        return root_run, child_runs

    def _get_critical_fields(self, eval_type: str) -> Dict[str, List[str]]:
        """Define fields that must maintain root run priority.

        Args:
            eval_type: Evaluation type (availability, token_name, website)

        Returns:
            Dictionary mapping field categories to protected field names
        """
        if eval_type == "availability":
            return {
                "inputs": [],  # No critical input fields for availability
                "outputs": ["is_available", "notes"],  # These must come from root run
                "reference": [],
            }
        else:
            # Other eval types use existing logic (no protection)
            return {"inputs": [], "outputs": [], "reference": []}

    def _merge_with_protection(
        self, primary_data: dict, supplement_data: dict, protected_fields: List[str]
    ) -> None:
        """Merge supplement data into primary without overriding protected fields.

        Args:
            primary_data: Primary data dictionary (will be modified)
            supplement_data: Supplement data to merge in
            protected_fields: List of field names that cannot be overridden
        """
        for key, value in supplement_data.items():
            if key in protected_fields and key in primary_data:
                # Skip: Root run data takes priority for protected fields
                continue
            elif key not in primary_data:
                # Allow: Fill missing fields from child runs
                primary_data[key] = value
            elif key not in protected_fields:
                # Override non-protected existing fields
                if isinstance(value, dict) and isinstance(primary_data.get(key), dict):
                    # Recurse: Deep merge for nested structures (no protection at nested levels)
                    self._deep_merge_dict(primary_data[key], value)
                else:
                    # Override with supplement data
                    primary_data[key] = value

    def _extract_with_priority(
        self, root_run: Optional[dict], child_runs: List[dict], eval_type: str
    ) -> tuple[dict, dict, dict]:
        """Extract data with root run priority for critical fields.

        Args:
            root_run: Root run data (trace_id == run_id)
            child_runs: List of child run data
            eval_type: Evaluation type for priority rules

        Returns:
            Tuple of (inputs, outputs, reference) dictionaries
        """
        # Phase 1: Extract from root run (authoritative)
        primary_inputs = self._extract_inputs(root_run) if root_run else {}
        primary_outputs = self._extract_outputs(root_run) if root_run else {}
        primary_reference = self._extract_reference(root_run) if root_run else {}

        # Phase 2: Supplement with child run data (gap filling only)
        critical_fields = self._get_critical_fields(eval_type)

        for child_run in child_runs:
            child_inputs = self._extract_inputs(child_run)
            child_outputs = self._extract_outputs(child_run)
            child_reference = self._extract_reference(child_run)

            # Merge with protection for critical fields
            self._merge_with_protection(
                primary_inputs, child_inputs, critical_fields.get("inputs", [])
            )
            self._merge_with_protection(
                primary_outputs, child_outputs, critical_fields.get("outputs", [])
            )
            self._merge_with_protection(
                primary_reference, child_reference, critical_fields.get("reference", [])
            )

        return primary_inputs, primary_outputs, primary_reference


class LangSmithUploader:
    """Upload datasets to LangSmith."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LangSmith uploader.

        Args:
          api_key: Optional LangSmith API key (uses settings if not provided)
        """
        self.client = Client(api_key=api_key or get_settings().langsmith_api_key)

    def upload_dataset(self, dataset: EvaluationDataset, overwrite: bool = False) -> str:
        """Upload a dataset to LangSmith.

        Args:
          dataset: Dataset to upload
          overwrite: Whether to overwrite existing dataset

        Returns:
          Dataset ID
        """
        # Check if dataset exists
        existing_dataset = None
        try:
            existing_dataset = self.client.read_dataset(dataset_name=dataset.name)
        except Exception:
            pass  # Dataset doesn't exist

        if existing_dataset and not overwrite:
            raise ValueError(
                f"Dataset '{dataset.name}' already exists. Use overwrite=True to replace."
            )

        # Create or update dataset
        if existing_dataset:
            dataset_obj = existing_dataset
            console.print(f"[yellow]Updating existing dataset '{dataset.name}'[/yellow]")
        else:
            dataset_obj = self.client.create_dataset(
                dataset_name=dataset.name, description=dataset.description
            )
            console.print(f"[green]Created new dataset '{dataset.name}'[/green]")

        # Upload examples
        for example in dataset.examples:
            self.client.create_example(
                dataset_id=dataset_obj.id,
                inputs=example.inputs,
                outputs=example.outputs,
                metadata=example.metadata,
            )

        console.print(f"[green]Uploaded {len(dataset.examples)} examples to dataset[/green]")
        return str(dataset_obj.id)


class EvaluationAPIClient:
    """Client for external evaluation API integration."""

    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the evaluation API client.

        Args:
          endpoint: API endpoint URL (uses EVAL_API_ENDPOINT env var if not provided)
          api_key: Optional API key for authentication
        """
        settings = get_settings()
        self.endpoint = endpoint or settings.eval_api_endpoint
        self.api_key = api_key
        self.username = settings.eval_api_username
        self.password = settings.eval_api_password

        if not self.endpoint:
            raise ValueError("EVAL_API_ENDPOINT environment variable must be set")

    def run_evaluation(
        self, dataset_name: str, experiment_prefix: str, eval_type: str
    ) -> Dict[str, Any]:
        """Run an evaluation via the external API.

        Args:
          dataset_name: Name of the dataset in LangSmith
          experiment_prefix: Prefix for the experiment
          eval_type: Type of evaluation to run

        Returns:
          API response data
        """
        # Prepare query parameters
        params = {
            "dataset_name": dataset_name,
            "experiment_prefix": experiment_prefix,
            "eval_type": eval_type,
        }

        # Debug: Print the parameters being sent
        console.print(f"[blue]Debug: Sending query params: {params}[/blue]")

        # Generate signature for authentication (using params for consistency)
        signature = self._generate_signature(params)

        headers = {"Content-Type": "application/json", "X-Signature": signature}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Setup authentication
        auth = None
        if self.username and self.password:
            auth = (self.username, self.password)

        # Make API request
        with httpx.Client() as client:
            try:
                console.print(f"[blue]Debug: Sending request to: {self.endpoint}[/blue]")
                response = client.post(
                    self.endpoint, params=params, headers=headers, auth=auth, timeout=30.0
                )
                console.print(f"[blue]Debug: Response status: {response.status_code}[/blue]")
                if response.status_code != 200:
                    console.print(f"[blue]Debug: Response body: {response.text}[/blue]")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                console.print(f"[red]Error calling evaluation API: {e}[/red]")
                raise

    def _generate_signature(self, payload: Dict[str, Any]) -> str:
        """Generate signature for payload authentication.

        Args:
          payload: Request payload

        Returns:
          Signature string
        """
        # Convert payload to canonical JSON string
        payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))

        # Generate signature (placeholder implementation)
        # Actual implementation will be provided during integration
        signature = hashlib.sha256(payload_str.encode()).hexdigest()

        return signature
