"""Data storage operations for LangSmith runs in the database."""

import json
import logging
from datetime import date
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langsmith.schemas import Run
from sqlalchemy import text

from lse.database import DatabaseManager
from lse.exceptions import DataStorageError

logger = logging.getLogger(__name__)


class RunDataTransformer:
    """Transforms LangSmith Run objects for database storage."""

    @staticmethod
    def run_to_database_record(run: Run, project_name: str) -> Dict[str, Any]:
        """Transform a LangSmith Run to database record format.

        Args:
            run: LangSmith Run object
            project_name: Project name for the run

        Returns:
            Dictionary with database record fields
        """
        # Extract run date from start_time or use current date
        run_date = date.today()
        if run.start_time:
            run_date = run.start_time.date()

        # Convert Run object to dictionary for JSONB storage
        run_data = {
            "id": str(run.id),
            "name": run.name,
            "run_type": run.run_type,
            "start_time": run.start_time.isoformat() if run.start_time else None,
            "end_time": run.end_time.isoformat() if run.end_time else None,
            "extra": run.extra or {},
            "inputs": run.inputs or {},
            "outputs": run.outputs or {},
            "session_id": str(run.session_id) if run.session_id else None,
            "trace_id": str(run.trace_id) if run.trace_id else None,
            "dotted_order": run.dotted_order,
            "parent_run_id": str(run.parent_run_id) if run.parent_run_id else None,
            "status": run.status,
            "error": run.error,
            "total_tokens": run.total_tokens,
            "prompt_tokens": run.prompt_tokens,
            "completion_tokens": run.completion_tokens,
            "total_cost": str(run.total_cost) if run.total_cost else None,
            "prompt_cost": str(run.prompt_cost) if run.prompt_cost else None,
            "completion_cost": str(run.completion_cost) if run.completion_cost else None,
            "first_token_time": run.first_token_time.isoformat() if run.first_token_time else None,
            "tags": run.tags or [],
            "events": run.events or [],
            "reference_example_id": str(run.reference_example_id)
            if run.reference_example_id
            else None,
            "serialized": run.serialized,
            "app_path": run.app_path,
            "manifest_id": str(run.manifest_id) if run.manifest_id else None,
        }

        return {
            "run_id": str(run.id),
            "trace_id": str(run.trace_id) if run.trace_id else str(run.id),
            "project": project_name,
            "run_date": run_date,
            "data": json.dumps(run_data),
        }


class DatabaseRunStorage:
    """Handles storage and retrieval of LangSmith runs in the database."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize storage with database manager.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.transformer = RunDataTransformer()

    async def store_run(self, run: Run, project_name: str) -> bool:
        """Store a single run in the database.

        Args:
            run: LangSmith Run object
            project_name: Project name for the run

        Returns:
            True if stored successfully

        Raises:
            DataStorageError: If storage fails
        """
        try:
            record = self.transformer.run_to_database_record(run, project_name)

            async with self.db_manager.get_session() as session:
                # Use INSERT ... ON CONFLICT DO UPDATE to handle duplicates
                await session.execute(
                    text("""
                        INSERT INTO runs (run_id, trace_id, project, run_date, data)
                        VALUES (:run_id, :trace_id, :project, :run_date, :data)
                        ON CONFLICT (run_id) DO UPDATE SET
                            trace_id = EXCLUDED.trace_id,
                            project = EXCLUDED.project,
                            run_date = EXCLUDED.run_date,
                            data = EXCLUDED.data
                    """),
                    record,
                )

            logger.debug(f"Stored run {run.id} for project {project_name}")
            return True

        except Exception as e:
            raise DataStorageError(f"Failed to store run {run.id}: {e}") from e

    async def store_runs_batch(self, runs: List[Run], project_name: str) -> Dict[str, Any]:
        """Store multiple runs in a batch operation.

        Args:
            runs: List of LangSmith Run objects
            project_name: Project name for the runs

        Returns:
            Dictionary with storage results

        Raises:
            DataStorageError: If batch storage fails
        """
        if not runs:
            return {"stored": 0, "skipped": 0, "errors": 0}

        stored_count = 0
        error_count = 0

        try:
            # Transform all runs to database records
            records = []
            for run in runs:
                try:
                    record = self.transformer.run_to_database_record(run, project_name)
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Failed to transform run {run.id}: {e}")
                    error_count += 1

            if not records:
                return {"stored": 0, "skipped": 0, "errors": error_count}

            # Batch insert with conflict resolution
            async with self.db_manager.get_session() as session:
                await session.execute(
                    text("""
                        INSERT INTO runs (run_id, trace_id, project, run_date, data)
                        VALUES (:run_id, :trace_id, :project, :run_date, :data)
                        ON CONFLICT (run_id) DO UPDATE SET
                            trace_id = EXCLUDED.trace_id,
                            project = EXCLUDED.project,
                            run_date = EXCLUDED.run_date,
                            data = EXCLUDED.data
                    """),
                    records,
                )

                stored_count = len(records)

            logger.info(f"Batch stored {stored_count} runs for project {project_name}")

            return {
                "stored": stored_count,
                "skipped": 0,
                "errors": error_count,
            }

        except Exception as e:
            raise DataStorageError(f"Failed to store batch of {len(runs)} runs: {e}") from e

    async def get_run(self, run_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Retrieve a single run from the database.

        Args:
            run_id: Run ID to retrieve

        Returns:
            Run data dictionary or None if not found
        """
        try:
            result = await self.db_manager.execute_raw_sql(
                "SELECT run_id, trace_id, project, run_date, data FROM runs WHERE run_id = :run_id",
                {"run_id": str(run_id)},
            )

            if not result:
                return None

            row = result[0]
            data = row[4]  # JSONB data column
            if isinstance(data, str):
                data = json.loads(data)

            return {
                "run_id": row[0],
                "trace_id": row[1],
                "project": row[2],
                "run_date": row[3],
                "data": data,
            }

        except Exception as e:
            logger.error(f"Failed to retrieve run {run_id}: {e}")
            return None

    async def get_runs_by_trace(self, trace_id: Union[str, UUID]) -> List[Dict[str, Any]]:
        """Retrieve all runs for a specific trace.

        Args:
            trace_id: Trace ID to retrieve runs for

        Returns:
            List of run data dictionaries
        """
        try:
            result = await self.db_manager.execute_raw_sql(
                "SELECT run_id, trace_id, project, run_date, data FROM runs WHERE trace_id = :trace_id ORDER BY run_id",
                {"trace_id": str(trace_id)},
            )

            runs = []
            for row in result:
                data = row[4]  # JSONB data column
                if isinstance(data, str):
                    data = json.loads(data)

                runs.append(
                    {
                        "run_id": row[0],
                        "trace_id": row[1],
                        "project": row[2],
                        "run_date": row[3],
                        "data": data,
                    }
                )

            return runs

        except Exception as e:
            logger.error(f"Failed to retrieve runs for trace {trace_id}: {e}")
            return []

    async def get_runs_by_project_and_date(
        self,
        project_name: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve runs by project and date range.

        Args:
            project_name: Project name to filter by
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            limit: Maximum number of runs to return

        Returns:
            List of run data dictionaries
        """
        try:
            # Build query with optional date filtering
            where_conditions = ["project = :project"]
            params = {"project": project_name}

            if start_date:
                where_conditions.append("run_date >= :start_date")
                params["start_date"] = start_date

            if end_date:
                where_conditions.append("run_date <= :end_date")
                params["end_date"] = end_date

            where_clause = " AND ".join(where_conditions)
            limit_clause = f" LIMIT {limit}" if limit else ""

            query = f"""
                SELECT run_id, trace_id, project, run_date, data
                FROM runs
                WHERE {where_clause}
                ORDER BY run_date DESC, run_id
                {limit_clause}
            """

            result = await self.db_manager.execute_raw_sql(query, params)

            runs = []
            for row in result:
                data = row[4]  # JSONB data column
                if isinstance(data, str):
                    data = json.loads(data)

                runs.append(
                    {
                        "run_id": row[0],
                        "trace_id": row[1],
                        "project": row[2],
                        "run_date": row[3],
                        "data": data,
                    }
                )

            return runs

        except Exception as e:
            logger.error(f"Failed to retrieve runs for project {project_name}: {e}")
            return []

    async def get_storage_stats(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """Get storage statistics.

        Args:
            project_name: Optional project name to filter by

        Returns:
            Dictionary with storage statistics
        """
        try:
            if project_name:
                result = await self.db_manager.execute_raw_sql(
                    """
                    SELECT 
                        COUNT(*) as total_runs,
                        COUNT(DISTINCT trace_id) as total_traces,
                        MIN(run_date) as earliest_date,
                        MAX(run_date) as latest_date
                    FROM runs 
                    WHERE project = :project
                    """,
                    {"project": project_name},
                )
            else:
                result = await self.db_manager.execute_raw_sql(
                    """
                    SELECT 
                        COUNT(*) as total_runs,
                        COUNT(DISTINCT trace_id) as total_traces,
                        COUNT(DISTINCT project) as total_projects,
                        MIN(run_date) as earliest_date,
                        MAX(run_date) as latest_date
                    FROM runs
                    """
                )

            if not result:
                return {}

            row = result[0]
            stats = {
                "total_runs": row[0],
                "total_traces": row[1],
                "earliest_date": row[-2],
                "latest_date": row[-1],
            }

            if not project_name:
                stats["total_projects"] = row[2]

            return stats

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}
