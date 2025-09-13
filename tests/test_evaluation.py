"""Unit tests for the evaluation module."""

import json
from unittest.mock import MagicMock, Mock, patch
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
    """Tests for TraceExtractor class."""

    def test_extract_traces_no_traces(self, tmp_path):
        """Test extracting traces when no traces exist."""
        storage = Mock()
        storage.output_dir = tmp_path

        extractor = TraceExtractor(storage=storage)
        traces = extractor.extract_traces(project="test-project", date="2025-01-01")

        assert traces == []

    def test_extract_traces_ai_only_filtered_out(self, tmp_path):
        """Test that traces with only AI output are filtered out."""
        # Create test trace directory and file
        trace_dir = tmp_path / "test-project" / "2025-01-01"
        trace_dir.mkdir(parents=True)

        trace_data = {"id": "trace-123", "outputs": {"ai_recommendation": "test recommendation"}}

        trace_file = trace_dir / "trace-123_12345.json"
        with open(trace_file, "w") as f:
            json.dump(trace_data, f)

        storage = Mock()
        storage.output_dir = tmp_path

        extractor = TraceExtractor(storage=storage)
        traces = extractor.extract_traces(project="test-project", date="2025-01-01")

        # Since trace only has AI output but no human feedback, it should be filtered out
        assert len(traces) == 0

    def test_extract_traces_with_both_ai_and_human(self, tmp_path):
        """Test extracting traces that have both AI output and human feedback."""
        # Create test trace directory and file
        trace_dir = tmp_path / "test-project" / "2025-01-01"
        trace_dir.mkdir(parents=True)

        trace_data = {
            "id": "trace-456",
            "outputs": {"ai_recommendation": "test recommendation"},
            "feedback": [{"score": 1.0, "value": "correct", "comment": "Good response"}],
        }

        trace_file = trace_dir / "trace-456_12345.json"
        with open(trace_file, "w") as f:
            json.dump(trace_data, f)

        storage = Mock()
        storage.output_dir = tmp_path

        extractor = TraceExtractor(storage=storage)
        traces = extractor.extract_traces(project="test-project", date="2025-01-01")

        assert len(traces) == 1
        assert traces[0].trace_id == "trace-456"
        assert traces[0].has_ai_output is True
        assert traces[0].has_human_feedback is True

    def test_has_ai_output_detection(self):
        """Test AI output detection in traces."""
        extractor = TraceExtractor()

        # Test with AI output in outputs field
        trace_with_output = {"outputs": {"ai_recommendation": "test"}}
        assert extractor._has_ai_output(trace_with_output) is True

        # Test with AI output in run field
        trace_with_run_output = {"run": {"outputs": {"response": "test"}}}
        assert extractor._has_ai_output(trace_with_run_output) is True

        # Test without AI output
        trace_without_output = {"inputs": {"query": "test"}}
        assert extractor._has_ai_output(trace_without_output) is False

    def test_has_human_feedback_detection(self):
        """Test human feedback detection in traces."""
        extractor = TraceExtractor()

        # Test with feedback field
        trace_with_feedback = {"feedback": [{"score": 1.0}]}
        assert extractor._has_human_feedback(trace_with_feedback) is True

        # Test with human_verdict in outputs
        trace_with_verdict = {"outputs": {"human_verdict": "correct"}}
        assert extractor._has_human_feedback(trace_with_verdict) is True

        # Test without feedback
        trace_without_feedback = {"outputs": {"ai_recommendation": "test"}}
        assert extractor._has_human_feedback(trace_without_feedback) is False


class TestDatasetBuilder:
    """Tests for DatasetBuilder class."""

    def test_build_dataset_empty(self):
        """Test building dataset with no traces."""
        builder = DatasetBuilder()
        dataset = builder.build_dataset(trace_metadata=[], dataset_name="test-dataset")

        assert dataset.name == "test-dataset"
        assert len(dataset.examples) == 0

    def test_build_dataset_with_traces(self, tmp_path):
        """Test building dataset with traces."""
        # Create test trace file
        trace_dir = tmp_path / "test-project" / "2025-01-01"
        trace_dir.mkdir(parents=True)

        trace_data = {
            "id": "trace-789",
            "inputs": {"query": "test query"},
            "outputs": {"ai_recommendation": "test recommendation"},
            "feedback": [{"score": 1.0, "value": "correct"}],
        }

        trace_file = trace_dir / "trace-789_12345.json"
        with open(trace_file, "w") as f:
            json.dump(trace_data, f)

        # Create metadata
        metadata = TraceMetadata(
            trace_id="trace-789",
            project="test-project",
            date="2025-01-01",
            has_ai_output=True,
            has_human_feedback=True,
        )

        storage = Mock()
        storage.output_dir = tmp_path

        builder = DatasetBuilder(storage=storage)
        dataset = builder.build_dataset(
            trace_metadata=[metadata], dataset_name="test-dataset", description="Test dataset"
        )

        assert dataset.name == "test-dataset"
        assert dataset.description == "Test dataset"
        assert len(dataset.examples) == 1

        example = dataset.examples[0]
        assert example.inputs == {"query": "test query"}
        assert example.outputs == {"ai_recommendation": "test recommendation"}
        assert example.reference["feedback_score"] == 1.0
        assert example.reference["feedback_value"] == "correct"

    def test_extract_inputs(self):
        """Test input extraction from trace data."""
        builder = DatasetBuilder()

        # Test direct inputs
        trace_data = {"inputs": {"query": "test"}}
        inputs = builder._extract_inputs(trace_data)
        assert inputs == {"query": "test"}

        # Test run inputs
        trace_data = {"run": {"inputs": {"context": "test context"}}}
        inputs = builder._extract_inputs(trace_data)
        assert inputs == {"context": "test context"}

    def test_extract_outputs(self):
        """Test output extraction from trace data."""
        builder = DatasetBuilder()

        # Test direct outputs
        trace_data = {"outputs": {"response": "test response"}}
        outputs = builder._extract_outputs(trace_data)
        assert outputs == {"response": "test response"}

        # Test run outputs
        trace_data = {"run": {"outputs": {"result": "test result"}}}
        outputs = builder._extract_outputs(trace_data)
        assert outputs == {"result": "test result"}

    def test_extract_reference(self):
        """Test reference extraction from trace data."""
        builder = DatasetBuilder()

        # Test feedback extraction
        trace_data = {"feedback": [{"score": 0.8, "value": "mostly correct", "comment": "Good"}]}
        reference = builder._extract_reference(trace_data)
        assert reference["feedback_score"] == 0.8
        assert reference["feedback_value"] == "mostly correct"
        assert reference["feedback_comment"] == "Good"

        # Test human verdict extraction
        trace_data = {"outputs": {"human_verdict": "approved"}}
        reference = builder._extract_reference(trace_data)
        assert reference["human_verdict"] == "approved"


class TestLangSmithUploader:
    """Tests for LangSmithUploader class."""

    @patch("lse.evaluation.Client")
    def test_upload_new_dataset(self, mock_client_class):
        """Test uploading a new dataset."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock dataset doesn't exist
        mock_client.read_dataset.side_effect = Exception("Dataset not found")

        # Mock dataset creation
        mock_dataset = Mock()
        mock_dataset.id = "dataset-123"
        mock_client.create_dataset.return_value = mock_dataset

        # Create test dataset
        dataset = EvaluationDataset(
            name="test-dataset",
            description="Test description",
            examples=[
                DatasetExample(
                    inputs={"query": "test"},
                    outputs={"response": "test"},
                    metadata={"trace_id": "123"},
                )
            ],
        )

        uploader = LangSmithUploader(api_key="test-key")
        dataset_id = uploader.upload_dataset(dataset)

        assert dataset_id == "dataset-123"
        mock_client.create_dataset.assert_called_once_with(
            dataset_name="test-dataset", description="Test description"
        )
        mock_client.create_example.assert_called_once()

    @patch("lse.evaluation.Client")
    def test_upload_existing_dataset_no_overwrite(self, mock_client_class):
        """Test uploading to existing dataset without overwrite."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock dataset exists
        mock_dataset = Mock()
        mock_dataset.id = "dataset-456"
        mock_client.read_dataset.return_value = mock_dataset

        dataset = EvaluationDataset(name="existing-dataset", examples=[])

        uploader = LangSmithUploader(api_key="test-key")

        with pytest.raises(ValueError, match="already exists"):
            uploader.upload_dataset(dataset, overwrite=False)

    @patch("lse.evaluation.Client")
    def test_upload_existing_dataset_with_overwrite(self, mock_client_class):
        """Test uploading to existing dataset with overwrite."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock dataset exists
        mock_dataset = Mock()
        mock_dataset.id = "dataset-789"
        mock_client.read_dataset.return_value = mock_dataset

        dataset = EvaluationDataset(
            name="existing-dataset",
            examples=[
                DatasetExample(
                    inputs={"query": "test"},
                    outputs={"response": "test"},
                    metadata={"trace_id": "456"},
                )
            ],
        )

        uploader = LangSmithUploader(api_key="test-key")
        dataset_id = uploader.upload_dataset(dataset, overwrite=True)

        assert dataset_id == "dataset-789"
        mock_client.create_example.assert_called_once()


class TestEvaluationAPIClient:
    """Tests for EvaluationAPIClient class."""

    def test_init_no_endpoint(self):
        """Test initialization without endpoint."""
        with patch("lse.evaluation.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_settings.eval_api_endpoint = None
            mock_get_settings.return_value = mock_settings

            with pytest.raises(ValueError, match="EVAL_API_ENDPOINT"):
                EvaluationAPIClient()

    def test_init_with_endpoint(self):
        """Test initialization with endpoint."""
        client = EvaluationAPIClient(endpoint="https://example.com/api")
        assert client.endpoint == "https://example.com/api"

    @patch("httpx.Client")
    def test_run_evaluation_success(self, mock_httpx_client):
        """Test successful evaluation run."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "id": "eval-123"}
        mock_response.raise_for_status = Mock()

        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client_instance

        client = EvaluationAPIClient(endpoint="https://example.com/api")
        response = client.run_evaluation(
            dataset_name="test-dataset", experiment_prefix="exp-001", eval_type="accuracy"
        )

        assert response["status"] == "success"
        assert response["id"] == "eval-123"

        # Verify API call
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        assert call_args[0][0] == "https://example.com/api"
        assert call_args[1]["json"]["dataset_name"] == "test-dataset"
        assert call_args[1]["json"]["experiment_prefix"] == "exp-001"
        assert call_args[1]["json"]["eval_type"] == "accuracy"

    @patch("httpx.Client")
    def test_run_evaluation_failure(self, mock_httpx_client):
        """Test evaluation run with API error."""
        # Setup mock error response
        mock_client_instance = MagicMock()
        mock_client_instance.post.side_effect = Exception("API Error")
        mock_httpx_client.return_value.__enter__.return_value = mock_client_instance

        client = EvaluationAPIClient(endpoint="https://example.com/api")

        with pytest.raises(Exception, match="API Error"):
            client.run_evaluation(
                dataset_name="test-dataset", experiment_prefix="exp-001", eval_type="accuracy"
            )

    def test_generate_signature(self):
        """Test signature generation."""
        client = EvaluationAPIClient(endpoint="https://example.com/api")

        payload = {"dataset_name": "test", "experiment_prefix": "exp", "eval_type": "accuracy"}

        signature = client._generate_signature(payload)

        # Should be a valid hex string
        assert len(signature) == 64  # SHA256 produces 64 hex characters
        assert all(c in "0123456789abcdef" for c in signature)
