"""Unit tests for the evaluation module."""

import json
from datetime import date
from unittest.mock import AsyncMock, Mock, patch
import pytest

from lse.evaluation import (
    DatasetBuilder,
    DatasetExample,
    EvaluationAPIClient,
    EvaluationDataset,
    LangSmithUploader,
    TraceExtractor,
    TraceMetadata,
)


class TestTraceExtractor:
    """Tests for TraceExtractor class (database-based)."""

    @pytest.mark.asyncio
    @patch("lse.evaluation.text")
    async def test_extract_traces_from_db_no_traces(self, mock_text):
        """Test extracting traces from database when no traces exist."""
        mock_db = AsyncMock()
        mock_session = AsyncMock()

        # Create a proper async context manager mock
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_db.get_session = Mock(return_value=MockAsyncContextManager())

        # Mock empty result
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        extractor = TraceExtractor(database=mock_db)
        traces = await extractor.extract_traces_from_db(
            project="test-project", start_date="2025-01-01", end_date="2025-01-01"
        )

        assert traces == []

    @pytest.mark.asyncio
    @patch("lse.evaluation.text")
    async def test_extract_traces_from_db_with_traces(self, mock_text):
        """Test extracting traces from database with valid traces."""
        mock_db = AsyncMock()
        mock_session = AsyncMock()

        # Create a proper async context manager mock
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_db.get_session = Mock(return_value=MockAsyncContextManager())

        # Mock database result with trace data
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            (
                "trace-123",
                "test-project",
                date(2025, 1, 1),  # Return actual date object
                [
                    {
                        "id": "run-1",
                        "trace_id": "trace-123",
                        "outputs": {"final_decision": "PASS", "confidence": 0.8},
                        "feedback_stats": {"final_verdict": {"comments": ["Human verdict: PASS"]}},
                        "inputs": {"query": "test query"},
                    }
                ],
                1,
            )
        ]
        mock_session.execute.return_value = mock_result

        extractor = TraceExtractor(database=mock_db)
        traces = await extractor.extract_traces_from_db(
            project="test-project",
            start_date="2025-01-01",
            end_date="2025-01-01",
            eval_type="token_name",
        )

        assert len(traces) == 1
        assert traces[0].trace_id == "trace-123"
        assert traces[0].project == "test-project"
        assert traces[0].date == "2025-01-01"

    def test_has_ai_output_detection_database_format(self):
        """Test AI output detection with database format."""
        extractor = TraceExtractor()

        # Test with AI output in outputs field (database format)
        trace_with_output = {"outputs": {"final_decision": "PASS"}}
        assert extractor._has_ai_output(trace_with_output) is True

        # Test with AI output in file format
        trace_with_file_format = {"trace": {"outputs": {"ai_recommendation": "test"}}}
        assert extractor._has_ai_output(trace_with_file_format) is True

        # Test without AI output
        trace_without_output = {"inputs": {"query": "test"}}
        assert extractor._has_ai_output(trace_without_output) is False

    def test_has_human_feedback_detection_database_format(self):
        """Test human feedback detection with database format."""
        extractor = TraceExtractor()

        # Test with feedback_stats in database format
        trace_with_feedback = {
            "feedback_stats": {"final_verdict": {"comments": ["Human verdict: PASS"]}}
        }
        assert extractor._has_human_feedback(trace_with_feedback) is True

        # Test with feedback field (file format)
        trace_with_file_feedback = {"feedback": [{"score": 1.0}]}
        assert extractor._has_human_feedback(trace_with_file_feedback) is True

        # Test without feedback
        trace_without_feedback = {"inputs": {"query": "test"}}
        assert extractor._has_human_feedback(trace_without_feedback) is False

    def test_has_final_verdict_feedback_database_format(self):
        """Test final verdict feedback detection with database format."""
        extractor = TraceExtractor()

        # Test with final verdict in database format
        trace_with_verdict = {
            "feedback_stats": {"final_verdict": {"comments": ["Human verdict: FAIL"]}}
        }
        assert extractor._has_final_verdict_feedback(trace_with_verdict) is True

        # Test with file format
        trace_with_file_verdict = {
            "trace": {"feedback_stats": {"final_verdict": {"comments": ["Human verdict: PASS"]}}}
        }
        assert extractor._has_final_verdict_feedback(trace_with_file_verdict) is True

        # Test without verdict
        trace_without_verdict = {"inputs": {"query": "test"}}
        assert extractor._has_final_verdict_feedback(trace_without_verdict) is False

    def test_get_feedback_verdict_database_format(self):
        """Test verdict extraction with database format."""
        extractor = TraceExtractor()

        # Test verdict extraction from database format
        trace_with_pass = {
            "feedback_stats": {"final_verdict": {"comments": ["Human verdict: PASS"]}}
        }
        assert extractor._get_feedback_verdict(trace_with_pass) == "PASS"

        trace_with_fail = {
            "feedback_stats": {"final_verdict": {"comments": ["Human verdict: FAIL"]}}
        }
        assert extractor._get_feedback_verdict(trace_with_fail) == "FAIL"

        # Test with file format
        trace_with_file_verdict = {
            "trace": {"feedback_stats": {"final_verdict": {"comments": ["Human verdict: PASS"]}}}
        }
        assert extractor._get_feedback_verdict(trace_with_file_verdict) == "PASS"

        # Test no verdict
        trace_without_verdict = {"inputs": {"query": "test"}}
        assert extractor._get_feedback_verdict(trace_without_verdict) is None


class TestDatasetBuilder:
    """Tests for DatasetBuilder class."""

    @pytest.mark.asyncio
    @patch("lse.evaluation.text")
    async def test_create_dataset_from_db(self, mock_text):
        """Test dataset creation from database."""
        mock_db = AsyncMock()
        mock_session = AsyncMock()

        # Create a proper async context manager mock
        class MockAsyncContextManager:
            async def __aenter__(self):
                return mock_session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_db.get_session = Mock(return_value=MockAsyncContextManager())

        # Mock database result with trace data that would create examples
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            (
                "trace-1",
                "test-project",
                date(2025, 1, 1),  # Return actual date object
                [
                    {
                        "id": "run-1",
                        "trace_id": "trace-1",
                        "outputs": {"final_decision": "PASS", "confidence": 0.8},
                        "feedback_stats": {"final_verdict": {"comments": ["Human verdict: PASS"]}},
                        "inputs": {"query": "test query"},
                    }
                ],
                1,
            )
        ]
        mock_session.execute.return_value = mock_result

        builder = DatasetBuilder(database=mock_db)

        # Mock the second execute call for run data fetching
        mock_run_result = Mock()
        mock_run_row = Mock()
        mock_run_row.data = {
            "id": "run-1",
            "trace_id": "trace-1",
            "outputs": {"final_decision": "PASS", "confidence": 0.8},
            "feedback_stats": {"final_verdict": {"comments": ["Human verdict: PASS"]}},
            "inputs": {"query": "test query"},
        }
        mock_run_result.fetchall.return_value = [mock_run_row]

        # Set up mock session to return different results for different calls
        call_count = 0

        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_result
            else:
                return mock_run_result

        mock_session.execute.side_effect = mock_execute

        dataset = await builder.create_dataset_from_db(
            project="test-project",
            start_date="2025-01-01",
            end_date="2025-01-01",
            eval_type="token_name",
        )

        assert isinstance(dataset, EvaluationDataset)
        assert dataset.name.startswith("test-project_token_name_")

    def test_build_dataset_with_traces(self):
        """Test building dataset from trace metadata (legacy support)."""
        builder = DatasetBuilder()

        traces = [
            TraceMetadata(
                trace_id="trace-1",
                project="test-project",
                date="2025-01-01",
                has_ai_output=True,
                has_human_feedback=True,
            )
        ]

        # Mock the file loading and directory structure
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.glob") as mock_glob,
            patch("builtins.open", mock_open_trace_file()),
        ):
            # Mock glob to return a single json file
            mock_file_path = Mock()
            mock_file_path.name = "trace-1.json"
            mock_glob.return_value = [mock_file_path]
            dataset = builder.build_dataset(
                trace_metadata=traces, dataset_name="test-dataset", eval_type="token_name"
            )

        assert isinstance(dataset, EvaluationDataset)
        assert len(dataset.examples) == 1


def mock_open_trace_file():
    """Mock file opening for trace data."""

    def mock_open(*args, **kwargs):
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)

        # Mock trace data that would pass evaluation criteria
        trace_data = {
            "trace": {
                "id": "trace-1",
                "trace_id": "trace-1",
                "outputs": {"final_decision": "PASS", "confidence": 0.8},
                "feedback_stats": {"final_verdict": {"comments": ["Human verdict: PASS"]}},
                "inputs": {"query": "test query"},
            }
        }
        mock_file.read.return_value = json.dumps(trace_data)
        return mock_file

    return mock_open


class TestEvaluationAPIClient:
    """Tests for EvaluationAPIClient class."""

    @patch("lse.evaluation.httpx.Client")
    def test_run_evaluation_success(self, mock_client_class):
        """Test successful evaluation run."""
        # Setup mock client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "id": "eval-123"}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        # Set up context manager behavior
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client_class.return_value = mock_client

        with patch("lse.evaluation.get_settings") as mock_settings:
            mock_settings.return_value.eval_api_endpoint = "https://test-api.example.com"
            mock_settings.return_value.eval_api_username = None
            mock_settings.return_value.eval_api_password = None
            client = EvaluationAPIClient(endpoint="https://test-api.example.com")
            result = client.run_evaluation(
                dataset_name="test-dataset", experiment_prefix="exp-001", eval_type="token_name"
            )

        assert result == {"status": "success", "id": "eval-123"}
        mock_client.post.assert_called_once()

    @patch("lse.evaluation.httpx.post")
    def test_run_evaluation_api_error(self, mock_post):
        """Test evaluation with API error."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        client = EvaluationAPIClient()

        with pytest.raises(Exception):
            client.run_evaluation(
                dataset_name="test-dataset", experiment_prefix="exp-001", eval_type="accuracy"
            )


class TestLangSmithUploader:
    """Tests for LangSmithUploader class."""

    @patch("lse.evaluation.Client")
    def test_upload_dataset_success(self, mock_client_class):
        """Test successful dataset upload."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.create_dataset.return_value.id = "dataset-123"

        # Mock read_dataset to raise exception (dataset doesn't exist)
        mock_client.read_dataset.side_effect = Exception("Dataset not found")

        uploader = LangSmithUploader()
        dataset = EvaluationDataset(
            name="test-dataset",
            examples=[DatasetExample(inputs={"query": "test"}, outputs={"response": "test"})],
        )

        result = uploader.upload_dataset(dataset=dataset)

        assert result == "dataset-123"
        mock_client.create_dataset.assert_called_once()

    @patch("lse.evaluation.Client")
    def test_upload_dataset_with_overwrite(self, mock_client_class):
        """Test dataset upload with overwrite."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock existing dataset
        existing_dataset = Mock()
        existing_dataset.id = "dataset-456"
        mock_client.read_dataset.return_value = existing_dataset
        mock_client.update_dataset.return_value = existing_dataset

        uploader = LangSmithUploader()
        dataset = EvaluationDataset(name="test-dataset", examples=[])

        result = uploader.upload_dataset(dataset=dataset, overwrite=True)

        assert result == "dataset-456"
        # Verify read_dataset was called to check existing dataset
        mock_client.read_dataset.assert_called_once_with(dataset_name="test-dataset")
