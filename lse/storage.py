"""Storage module for saving LangSmith traces as JSON files."""

import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langsmith.schemas import Run

from lse.config import Settings
from lse.exceptions import LSEError
from lse.timezone import to_langsmith_timezone

logger = logging.getLogger(__name__)


class StorageError(LSEError):
    """Error occurred during storage operations."""

    pass


class TraceStorage:
    """Handles storage of LangSmith traces to JSON files."""

    def __init__(self, settings: Settings):
        """Initialize trace storage.

        Args:
            settings: Application settings containing output directory
        """
        self.settings = settings
        self.output_dir = Path(settings.output_dir)

    def _extract_creation_date(self, run: Run) -> datetime:
        """Extract creation date from a trace run.

        Args:
            run: LangSmith run object

        Returns:
            Creation date of the trace
        """
        # Get the start_time from the run
        start_time = getattr(run, "start_time", None)

        if start_time is None:
            logger.warning(f"No start_time found for run {run.id}, using current time")
            return datetime.now()

        # Handle different start_time formats
        if isinstance(start_time, str):
            # Parse string format: "2025-08-29 06:44:12.622037"
            try:
                # Try parsing with microseconds
                dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                try:
                    # Try parsing without microseconds
                    dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    logger.warning(f"Could not parse start_time '{start_time}' for run {run.id}")
                    return datetime.now()
        elif isinstance(start_time, datetime):
            dt = start_time
        else:
            logger.warning(f"Unexpected start_time type {type(start_time)} for run {run.id}")
            return datetime.now()

        # Convert to LangSmith timezone if naive
        if dt.tzinfo is None:
            dt = to_langsmith_timezone(dt)

        return dt

    def _ensure_directory(self, path: Path) -> None:
        """Ensure directory exists, creating if necessary.

        Args:
            path: Directory path to create

        Raises:
            StorageError: If directory cannot be created
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {path}")
        except Exception as e:
            raise StorageError(f"Failed to create directory {path}: {e}") from e

    def _get_storage_path(
        self, project_name: Optional[str] = None, date: Optional[datetime] = None
    ) -> Path:
        """Get the storage path for traces.

        Args:
            project_name: Project name for organization
            date: Date for organization (should be trace creation date)

        Returns:
            Path where traces should be stored
        """
        storage_path = self.output_dir

        if project_name:
            # Sanitize project name for filesystem
            safe_project = "".join(c for c in project_name if c.isalnum() or c in "-_.")
            storage_path = storage_path / safe_project
        else:
            storage_path = storage_path / "unknown-project"

        # Add date directory - use provided date (should be trace creation date)
        if date is None:
            logger.warning("No date provided for storage path, using current date")
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")
        storage_path = storage_path / date_str

        return storage_path

    def _generate_filename(
        self, run_id: Union[str, UUID], timestamp: Optional[datetime] = None
    ) -> str:
        """Generate filename for a trace.

        Args:
            run_id: The run ID
            timestamp: Timestamp for the file (defaults to now)

        Returns:
            Filename for the trace
        """
        if timestamp is None:
            timestamp = datetime.now()

        timestamp_str = timestamp.strftime("%H%M%S")
        return f"{run_id}_{timestamp_str}.json"

    def _serialize_run(self, run: Run) -> Dict[str, Any]:
        """Serialize a LangSmith run to JSON-compatible format.

        Args:
            run: LangSmith run object

        Returns:
            JSON-serializable dictionary
        """
        try:
            # Convert the run to dictionary
            if hasattr(run, "dict"):
                # Pydantic model
                run_data = run.dict()
            elif hasattr(run, "__dict__"):
                # Regular object
                run_data = run.__dict__.copy()
            else:
                # Already a dict
                run_data = dict(run)

            # Convert UUIDs to strings
            def convert_uuids(obj):
                if isinstance(obj, UUID):
                    return str(obj)
                elif isinstance(obj, dict):
                    return {k: convert_uuids(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_uuids(item) for item in obj]
                else:
                    return obj

            return convert_uuids(run_data)

        except Exception as e:
            raise StorageError(f"Failed to serialize run: {e}") from e

    def save_trace(
        self, run: Run, project_name: Optional[str] = None, timestamp: Optional[datetime] = None
    ) -> Path:
        """Save a single trace to JSON file.

        Args:
            run: LangSmith run to save
            project_name: Project name for organization
            timestamp: Timestamp for file naming (defaults to current time)

        Returns:
            Path to the saved file

        Raises:
            StorageError: If save operation fails
        """
        try:
            # Extract creation date from the trace for storage path
            creation_date = self._extract_creation_date(run)

            # Determine storage location using creation date
            storage_path = self._get_storage_path(project_name, creation_date)
            self._ensure_directory(storage_path)

            # Generate filename using timestamp (for uniqueness)
            if timestamp is None:
                timestamp = datetime.now()
            filename = self._generate_filename(run.id, timestamp)
            file_path = storage_path / filename

            # Serialize run data
            run_data = self._serialize_run(run)

            # Add metadata
            metadata = {
                "extracted_at": datetime.now().isoformat(),
                "project_name": project_name,
                "run_id": str(run.id),
                "extractor_version": "0.1.0",
                "trace_creation_date": creation_date.isoformat(),
            }

            # Create final JSON structure
            trace_file = {
                "metadata": metadata,
                "trace": run_data,
            }

            # Write atomically using temporary file
            self._write_json_atomic(file_path, trace_file)

            logger.info(
                f"Saved trace {run.id} created on {creation_date.strftime('%Y-%m-%d')} to {file_path}"
            )
            return file_path

        except Exception as e:
            raise StorageError(f"Failed to save trace {getattr(run, 'id', 'unknown')}: {e}") from e

    def save_traces(
        self,
        runs: List[Run],
        project_name: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> List[Path]:
        """Save multiple traces to JSON files.

        Args:
            runs: List of LangSmith runs to save
            project_name: Project name for organization
            timestamp: Base timestamp for file naming

        Returns:
            List of paths to saved files

        Raises:
            StorageError: If any save operation fails
        """
        saved_paths = []
        failed_saves = []

        for i, run in enumerate(runs):
            try:
                # Use slight timestamp offset for each file to avoid conflicts
                file_timestamp = timestamp or datetime.now()
                if i > 0:
                    # Add microseconds to ensure unique timestamps
                    file_timestamp = file_timestamp.replace(microsecond=i * 1000)

                path = self.save_trace(run, project_name, file_timestamp)
                saved_paths.append(path)

            except StorageError as e:
                failed_saves.append((run.id, str(e)))
                logger.error(f"Failed to save trace {run.id}: {e}")

        # Create summary metadata file
        if saved_paths:
            self._create_summary_file(saved_paths, project_name, failed_saves)

        if failed_saves:
            raise StorageError(
                f"Failed to save {len(failed_saves)} out of {len(runs)} traces. "
                f"Successfully saved: {len(saved_paths)}"
            )

        logger.info(f"Successfully saved {len(saved_paths)} traces")
        return saved_paths

    def _write_json_atomic(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Write JSON data atomically using temporary file.

        Args:
            file_path: Target file path
            data: Data to write as JSON

        Raises:
            StorageError: If write operation fails
        """
        try:
            # Write to temporary file first
            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=file_path.parent,
                prefix=f".{file_path.name}",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                json.dump(data, temp_file, indent=2, ensure_ascii=False, default=str)
                temp_file.flush()
                temp_path = Path(temp_file.name)

            # Atomically move to final location
            temp_path.replace(file_path)
            logger.debug(f"Atomically wrote JSON to {file_path}")

        except Exception as e:
            # Clean up temp file if it exists
            if "temp_path" in locals() and temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise StorageError(f"Failed to write JSON to {file_path}: {e}") from e

    def _create_summary_file(
        self,
        saved_paths: List[Path],
        project_name: Optional[str],
        failed_saves: List[tuple[UUID, str]],
    ) -> None:
        """Create summary file with operation metadata.

        Args:
            saved_paths: Paths to successfully saved files
            project_name: Project name used for organization
            failed_saves: List of (run_id, error) for failed saves
        """
        try:
            if not saved_paths:
                return

            # Use the directory of the first saved file
            summary_dir = saved_paths[0].parent
            summary_path = summary_dir / "_summary.json"

            summary_data = {
                "operation": {
                    "timestamp": datetime.now().isoformat(),
                    "project_name": project_name,
                    "extractor_version": "0.1.0",
                },
                "results": {
                    "total_traces": len(saved_paths) + len(failed_saves),
                    "successful_saves": len(saved_paths),
                    "failed_saves": len(failed_saves),
                },
                "files": [str(path.name) for path in saved_paths],
                "failures": [
                    {"run_id": str(run_id), "error": error} for run_id, error in failed_saves
                ],
            }

            self._write_json_atomic(summary_path, summary_data)
            logger.debug(f"Created summary file: {summary_path}")

        except Exception as e:
            logger.warning(f"Failed to create summary file: {e}")
            # Don't raise - this is not critical for the main operation
