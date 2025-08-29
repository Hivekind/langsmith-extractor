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
            # Try to list runs with a minimal query to test connectivity
            list(self.client.list_runs(limit=1))
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
        **kwargs
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
            # Build filter parameters
            filters = {}
            if project_name:
                filters['project_name'] = project_name
            if start_time:
                filters['start_time'] = start_time
            if end_time:
                filters['end_time'] = end_time
            
            # Merge additional filters
            filters.update(kwargs)
            
            # Execute search
            runs = list(self.client.list_runs(
                limit=limit,
                **filters
            ))
            
            logger.debug(f"Search returned {len(runs)} runs")
            return runs
            
        except Exception as e:
            raise APIError(f"Failed to search runs: {e}") from e
    
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