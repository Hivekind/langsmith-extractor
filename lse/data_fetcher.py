"""LangSmith data fetcher for database storage."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


from lse.client import LangSmithClient
from lse.config import Settings
from lse.data_storage import DatabaseRunStorage
from lse.database import DatabaseManager
from lse.exceptions import DataFetchError

logger = logging.getLogger(__name__)


class LangSmithDataFetcher:
    """Fetches LangSmith data and stores it in the database."""

    def __init__(self, settings: Settings, db_manager: DatabaseManager):
        """Initialize the data fetcher.

        Args:
            settings: Application settings
            db_manager: Database manager for storage
        """
        self.settings = settings
        self.client = LangSmithClient(settings)
        self.storage = DatabaseRunStorage(db_manager)

    async def fetch_and_store_runs(
        self,
        project_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
        include_children: bool = False,
        include_feedback: bool = True,
    ) -> Dict[str, Any]:
        """Fetch runs from LangSmith and store them in the database.

        Args:
            project_name: Project name to fetch runs from
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            limit: Maximum number of root runs to fetch
            include_children: Whether to fetch child runs for each trace
            include_feedback: Whether to include feedback records (Phase 12 enhancement)

        Returns:
            Dictionary with fetch and storage results

        Raises:
            DataFetchError: If fetch operation fails
        """
        try:
            # Validate connection first
            if not self.client.validate_connection():
                raise DataFetchError("Cannot connect to LangSmith API")

            # Parse date filters
            start_time = None
            end_time = None
            if start_date:
                start_time = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
            if end_date:
                end_time = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

            # Fetch root runs
            logger.info(f"Fetching runs for project: {project_name}")
            root_runs = self.client.search_runs(
                project_name=project_name,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
                is_root=True,  # Only fetch root runs initially
            )

            logger.info(f"Found {len(root_runs)} root runs")

            root_count = len(root_runs)

            # Choose extraction method based on feedback inclusion (Phase 12)
            if include_feedback:
                logger.info("Using enhanced extraction with feedback records...")
                all_enhanced_runs = []

                # Process each root run with enhanced feedback extraction
                for root_run in root_runs:
                    if root_run.trace_id and include_children:
                        try:
                            # Fetch complete trace hierarchy with feedback
                            enhanced_trace_runs = self.client.fetch_trace_hierarchy_with_feedback(
                                str(root_run.trace_id)
                            )
                            all_enhanced_runs.extend(enhanced_trace_runs)
                            logger.debug(
                                f"Enhanced {len(enhanced_trace_runs)} runs for trace {root_run.trace_id}"
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to fetch enhanced trace {root_run.trace_id}: {e}"
                            )
                            # Fallback: add just the root run without feedback
                            all_enhanced_runs.append(root_run.dict())
                    else:
                        try:
                            # Fetch single run with feedback
                            enhanced_run = self.client.fetch_run_with_feedback(str(root_run.id))
                            all_enhanced_runs.append(enhanced_run)
                        except Exception as e:
                            logger.warning(f"Failed to fetch enhanced run {root_run.id}: {e}")
                            # Fallback: add without feedback
                            all_enhanced_runs.append(root_run.dict())

                # Store enhanced runs using enhanced storage method
                logger.info(f"Storing {len(all_enhanced_runs)} enhanced runs in database...")
                storage_result = await self.storage.store_enhanced_runs_batch(
                    all_enhanced_runs, project_name
                )

            else:
                # Use legacy method without feedback enhancement
                all_runs = list(root_runs)

                # Optionally fetch child runs for each trace
                if include_children:
                    logger.info("Fetching child runs for traces...")
                    for root_run in root_runs:
                        if root_run.trace_id:
                            try:
                                # Fetch complete trace hierarchy
                                trace_runs = self.client.fetch_trace_hierarchy(
                                    str(root_run.trace_id)
                                )
                                # Add only the child runs (exclude root run we already have)
                                child_runs = [run for run in trace_runs if run.id != root_run.id]
                                all_runs.extend(child_runs)
                                logger.debug(
                                    f"Added {len(child_runs)} child runs for trace {root_run.trace_id}"
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to fetch children for trace {root_run.trace_id}: {e}"
                                )

                # Store all runs in database using legacy method
                logger.info(f"Storing {len(all_runs)} runs in database...")
                storage_result = await self.storage.store_runs_batch(all_runs, project_name)

            # Calculate total runs based on which method was used
            if include_feedback:
                total_runs = len(all_enhanced_runs) if "all_enhanced_runs" in locals() else 0
            else:
                total_runs = len(all_runs) if "all_runs" in locals() else 0

            result = {
                "root_runs_fetched": root_count,
                "total_runs_fetched": total_runs,
                "runs_stored": storage_result["stored"],
                "errors": storage_result["errors"],
                "feedback_enhanced": include_feedback,
            }

            logger.info(f"Fetch complete: {result}")
            return result

        except Exception as e:
            raise DataFetchError(f"Failed to fetch and store runs: {e}") from e

    async def fetch_and_store_trace(
        self, trace_id: str, include_feedback: bool = True
    ) -> Dict[str, Any]:
        """Fetch a complete trace and store it in the database.

        Args:
            trace_id: Trace ID to fetch
            include_feedback: Whether to include feedback records (Phase 12 enhancement)

        Returns:
            Dictionary with fetch and storage results

        Raises:
            DataFetchError: If fetch operation fails
        """
        try:
            # Validate connection first
            if not self.client.validate_connection():
                raise DataFetchError("Cannot connect to LangSmith API")

            logger.info(f"Fetching complete trace: {trace_id}")

            # Choose extraction method based on feedback inclusion (Phase 12)
            if include_feedback:
                logger.info("Using enhanced trace extraction with feedback records...")

                # Fetch all runs in the trace with feedback
                enhanced_trace_runs = self.client.fetch_trace_hierarchy_with_feedback(trace_id)
                logger.info(f"Found {len(enhanced_trace_runs)} enhanced runs in trace")

                if not enhanced_trace_runs:
                    return {
                        "runs_fetched": 0,
                        "runs_stored": 0,
                        "errors": 0,
                        "feedback_enhanced": True,
                    }

                # Determine project name from the first run (it's a dict now)
                project_name = enhanced_trace_runs[0].get("session_id", "unknown")

                # Try to get a better project name from run metadata
                for run_dict in enhanced_trace_runs:
                    extra = run_dict.get("extra", {})
                    metadata = extra.get("metadata", {})
                    if "LANGSMITH_PROJECT" in metadata:
                        project_name = metadata["LANGSMITH_PROJECT"]
                        break

                # Store enhanced runs in database
                storage_result = await self.storage.store_enhanced_runs_batch(
                    enhanced_trace_runs, project_name
                )

            else:
                # Use legacy method without feedback enhancement
                trace_runs = self.client.fetch_trace_hierarchy(trace_id)
                logger.info(f"Found {len(trace_runs)} runs in trace")

                if not trace_runs:
                    return {
                        "runs_fetched": 0,
                        "runs_stored": 0,
                        "errors": 0,
                        "feedback_enhanced": False,
                    }

                # Determine project name from the first run
                project_name = getattr(trace_runs[0], "session_id", "unknown")

                # Try to get a better project name from run metadata
                for run in trace_runs:
                    if hasattr(run, "extra") and run.extra:
                        metadata = run.extra.get("metadata", {})
                        if "LANGSMITH_PROJECT" in metadata:
                            project_name = metadata["LANGSMITH_PROJECT"]
                            break

                # Store all runs in database
                storage_result = await self.storage.store_runs_batch(trace_runs, project_name)

            # Calculate runs based on which method was used
            if include_feedback:
                runs_count = len(enhanced_trace_runs) if "enhanced_trace_runs" in locals() else 0
            else:
                runs_count = len(trace_runs) if "trace_runs" in locals() else 0

            result = {
                "runs_fetched": runs_count,
                "runs_stored": storage_result["stored"],
                "errors": storage_result["errors"],
                "feedback_enhanced": include_feedback,
            }

            logger.info(f"Trace fetch complete: {result}")
            return result

        except Exception as e:
            raise DataFetchError(f"Failed to fetch and store trace {trace_id}: {e}") from e

    async def get_stored_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Retrieve a stored trace from the database.

        Args:
            trace_id: Trace ID to retrieve

        Returns:
            List of run data dictionaries
        """
        return await self.storage.get_runs_by_trace(trace_id)

    async def get_stored_runs(
        self,
        project_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve stored runs from the database.

        Args:
            project_name: Project name to filter by
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            limit: Maximum number of runs to return

        Returns:
            List of run data dictionaries
        """
        from datetime import date

        start_date_obj = None
        end_date_obj = None

        if start_date:
            start_date_obj = date.fromisoformat(start_date)
        if end_date:
            end_date_obj = date.fromisoformat(end_date)

        return await self.storage.get_runs_by_project_and_date(
            project_name, start_date_obj, end_date_obj, limit
        )

    async def get_storage_stats(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """Get storage statistics.

        Args:
            project_name: Optional project name to filter by

        Returns:
            Dictionary with storage statistics
        """
        return await self.storage.get_storage_stats(project_name)
