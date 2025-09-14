"""LangSmith client wrapper for API operations."""

import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langsmith import Client
from langsmith.schemas import Run

from lse.config import Settings
from lse.exceptions import APIError, ConfigurationError
from lse.retry import RetryConfig, with_retry

logger = logging.getLogger(__name__)


class LangSmithClient:
    """Wrapper around langsmith.Client with application-specific configuration."""

    def __init__(self, settings: Settings, retry_config: Optional[RetryConfig] = None):
        """Initialize LangSmith client with application settings.

        Args:
            settings: Application settings containing API configuration
            retry_config: Retry configuration for API operations

        Raises:
            ConfigurationError: If required configuration is missing or invalid
        """
        self.settings = settings
        self.retry_config = retry_config or RetryConfig()
        self._client: Optional[Client] = None

        # Validate required configuration
        if not settings.langsmith_api_key:
            raise ConfigurationError(
                "LangSmith API key is required. Set LANGSMITH_API_KEY environment variable."
            )

    @property
    def client(self) -> Client:
        """Get the underlying LangSmith client, initializing if needed."""
        if self._client is None:
            try:
                self._client = Client(
                    api_url=self.settings.langsmith_api_url,
                    api_key=self.settings.langsmith_api_key,
                    timeout_ms=(30000, 60000),  # (connect, read) timeout in ms
                )
                logger.debug(f"Initialized LangSmith client for {self.settings.langsmith_api_url}")
            except Exception as e:
                raise APIError(f"Failed to initialize LangSmith client: {e}") from e

        return self._client

    @with_retry()
    def validate_connection(self) -> bool:
        """Validate connection to LangSmith API.

        Returns:
            True if connection is successful

        Raises:
            APIError: If connection fails or authentication is invalid
        """
        try:
            # Try to list projects to test connectivity (doesn't require filters)
            # If this fails, try listing runs with is_root filter
            try:
                # First try to list projects - this is a simpler API call
                list(self.client.list_projects(limit=1))
            except Exception:
                # Fallback: try to list root runs from any project
                list(self.client.list_runs(is_root=True, limit=1))

            logger.info("LangSmith API connection validated successfully")
            return True
        except Exception as e:
            raise APIError(f"Failed to connect to LangSmith API: {e}") from e

    @with_retry()
    def fetch_run(self, run_id: Union[str, UUID]) -> Run:
        """Fetch a single run by ID.

        Args:
            run_id: The run ID to fetch

        Returns:
            The run data

        Raises:
            APIError: If the run cannot be fetched
        """
        try:
            run = self.client.read_run(run_id)
            logger.debug(f"Successfully fetched run {run_id}")
            return run
        except Exception as e:
            raise APIError(f"Failed to fetch run {run_id}: {e}") from e

    @with_retry()
    def search_runs(
        self,
        project_name: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> List[Run]:
        """Search for runs with optional filters.

        Args:
            project_name: Filter by project name
            start_time: Filter runs after this datetime (ISO format)
            end_time: Filter runs before this datetime (ISO format)
            limit: Maximum number of runs to return
            **kwargs: Additional filters passed to list_runs

        Returns:
            List of matching runs

        Raises:
            APIError: If the search fails
        """
        try:
            # Build filter parameters - list_runs expects specific parameter names
            list_params = {}

            if project_name:
                list_params["project_name"] = project_name

            if start_time:
                # Convert string to datetime if needed
                if isinstance(start_time, str):
                    from lse.timezone import parse_datetime_for_api

                    list_params["start_time"] = parse_datetime_for_api(start_time)
                else:
                    from lse.timezone import to_utc

                    list_params["start_time"] = to_utc(start_time)

            if end_time:
                # Convert string to datetime if needed
                if isinstance(end_time, str):
                    from lse.timezone import parse_datetime_for_api

                    list_params["end_time"] = parse_datetime_for_api(end_time)
                else:
                    from lse.timezone import to_utc

                    list_params["end_time"] = to_utc(end_time)

            # Add any additional kwargs
            list_params.update(kwargs)

            # Default to fetching root runs only (traces) to match UI behavior
            if "is_root" not in list_params:
                list_params["is_root"] = True

            # Execute search with proper pagination handling
            if limit is None:
                # When no limit specified, fetch ALL runs by iterating through pages
                runs = []
                for run in self.client.list_runs(**list_params):
                    runs.append(run)
                logger.debug(f"Search returned {len(runs)} runs (all pages)")
            else:
                # When limit specified, use it directly
                runs = list(self.client.list_runs(limit=limit, **list_params))
                logger.debug(f"Search returned {len(runs)} runs (limited)")

            return runs

        except Exception as e:
            raise APIError(f"Failed to search runs: {e}") from e

    @with_retry()
    def fetch_trace_hierarchy(self, trace_id: Union[str, UUID]) -> List[Run]:
        """Fetch all runs in a trace hierarchy (root + all child runs).

        Args:
            trace_id: The trace ID to fetch all runs for

        Returns:
            List of all runs in the trace (root + children)

        Raises:
            APIError: If the fetch fails
        """
        try:
            # Fetch all runs for this trace ID (no is_root filter)
            runs = []
            for run in self.client.list_runs(trace_id=trace_id):
                runs.append(run)

            logger.debug(f"Fetched {len(runs)} total runs for trace {trace_id}")
            return runs

        except Exception as e:
            raise APIError(f"Failed to fetch trace hierarchy for {trace_id}: {e}") from e

    @with_retry()
    def fetch_run_with_feedback(self, run_id: Union[str, UUID]) -> Dict[str, Any]:
        """Fetch a single run with enhanced feedback data.

        Args:
            run_id: The run ID to fetch

        Returns:
            Enhanced run data with feedback records in native format

        Raises:
            APIError: If the run or feedback cannot be fetched
        """
        try:
            # Fetch the base run data
            run = self.fetch_run(run_id)
            run_data = run.dict()

            # Fetch feedback records for this run
            feedback_records = self._fetch_feedback_records([str(run_id)])

            # Store feedback records in native format if any exist
            if feedback_records:
                run_data["feedback_records"] = feedback_records
                logger.debug(f"Added {len(feedback_records)} feedback records to run {run_id}")

            return run_data

        except Exception as e:
            # If feedback fetching fails, return the base run data
            logger.warning(f"Failed to fetch feedback for run {run_id}: {e}")
            return self.fetch_run(run_id).dict()

    @with_retry()
    def fetch_trace_hierarchy_with_feedback(
        self, trace_id: Union[str, UUID]
    ) -> List[Dict[str, Any]]:
        """Fetch all runs in a trace hierarchy with enhanced feedback data.

        Args:
            trace_id: The trace ID to fetch all runs for

        Returns:
            List of enhanced run data dictionaries with feedback records

        Raises:
            APIError: If the fetch fails
        """
        try:
            # Fetch the trace hierarchy
            trace_runs = self.fetch_trace_hierarchy(trace_id)

            if not trace_runs:
                return []

            # Convert runs to dictionaries
            enhanced_runs = [run.dict() for run in trace_runs]

            # Get all run IDs for batch feedback fetching
            run_ids = [str(run.id) for run in trace_runs]

            # Fetch feedback records for all runs in the trace
            feedback_records = self._fetch_feedback_records(run_ids)

            if feedback_records:
                # Group feedback by run_id for efficient lookup
                feedback_by_run = {}
                for feedback in feedback_records:
                    run_id = str(feedback.get("run_id", ""))
                    if run_id not in feedback_by_run:
                        feedback_by_run[run_id] = []
                    feedback_by_run[run_id].append(feedback)

                # Add feedback records to corresponding runs
                for run_data in enhanced_runs:
                    run_id = str(run_data.get("id", ""))
                    if run_id in feedback_by_run:
                        run_data["feedback_records"] = feedback_by_run[run_id]
                        logger.debug(
                            f"Added {len(feedback_by_run[run_id])} feedback records to run {run_id}"
                        )

            logger.debug(
                f"Enhanced {len(enhanced_runs)} runs with feedback data for trace {trace_id}"
            )
            return enhanced_runs

        except Exception as e:
            # If feedback enhancement fails, return basic trace data
            logger.warning(f"Failed to enhance trace {trace_id} with feedback: {e}")
            trace_runs = self.fetch_trace_hierarchy(trace_id)
            return [run.dict() for run in trace_runs]

    def _fetch_feedback_records(self, run_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch feedback records for the given run IDs.

        Args:
            run_ids: List of run IDs to fetch feedback for

        Returns:
            List of feedback records in native API format

        Note:
            This method includes rate limiting (1000ms delay) and graceful error handling.
        """
        if not run_ids:
            return []

        try:
            # Apply rate limiting (1000ms delay as per existing pattern)
            import time

            time.sleep(1.0)

            # Fetch feedback using the native LangSmith API
            feedback_items = list(self.client.list_feedback(run_ids=run_ids))

            # Convert feedback objects to dictionaries (native format)
            feedback_records = []
            for feedback in feedback_items:
                try:
                    feedback_dict = {
                        "id": str(feedback.id),
                        "run_id": str(feedback.run_id),
                        "key": feedback.key,
                        "score": feedback.score,
                        "value": feedback.value,
                        "comment": feedback.comment,
                        "correction": feedback.correction,
                        "feedback_source_type": feedback.feedback_source.type
                        if feedback.feedback_source
                        else None,
                        "created_at": feedback.created_at.isoformat()
                        if feedback.created_at
                        else None,
                        "modified_at": feedback.modified_at.isoformat()
                        if feedback.modified_at
                        else None,
                    }
                    feedback_records.append(feedback_dict)
                except Exception as e:
                    logger.warning(f"Failed to serialize feedback {feedback.id}: {e}")
                    continue

            logger.debug(
                f"Fetched {len(feedback_records)} feedback records for {len(run_ids)} runs"
            )
            return feedback_records

        except Exception as e:
            logger.warning(f"Failed to fetch feedback records: {e}")
            return []

    def get_client_info(self) -> Dict[str, Any]:
        """Get client configuration information for debugging.

        Returns:
            Dictionary with client configuration details
        """
        return {
            "api_url": self.settings.langsmith_api_url,
            "has_api_key": bool(self.settings.langsmith_api_key),
            "client_initialized": self._client is not None,
        }
