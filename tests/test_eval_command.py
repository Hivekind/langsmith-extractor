"""Tests for eval CLI commands."""

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from lse.commands.eval import app
from lse.evaluation import TraceMetadata, EvaluationDataset, DatasetExample

runner = CliRunner()


class TestExtractTracesCommand:
    """Tests for extract-traces command."""

    @patch("lse.commands.eval.TraceExtractor")
    def test_extract_traces_success(self, mock_extractor_class, tmp_path):
        """Test successful trace extraction."""
        # Setup mock extractor
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        # Mock extracted traces
        mock_traces = [
            TraceMetadata(
                trace_id="trace-1",
                project="test-project",
                date="2025-01-01",
                has_ai_output=True,
                has_human_feedback=False,
            ),
            TraceMetadata(
                trace_id="trace-2",
                project="test-project",
                date="2025-01-01",
                has_ai_output=True,
                has_human_feedback=True,
            ),
        ]
        mock_extractor.extract_traces.return_value = mock_traces

        output_file = tmp_path / "traces.json"

        result = runner.invoke(
            app,
            [
                "extract-traces",
                "--date",
                "2025-01-01",
                "--project",
                "test-project",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert "Extracted 2 traces" in result.stdout

        # Check output file
        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)

        assert data["date"] == "2025-01-01"
        assert data["project"] == "test-project"
        assert data["trace_count"] == 2
        assert len(data["trace_ids"]) == 2
        assert "trace-1" in data["trace_ids"]
        assert "trace-2" in data["trace_ids"]

    @patch("lse.commands.eval.TraceExtractor")
    def test_extract_traces_no_matches(self, mock_extractor_class):
        """Test extraction with no matching traces."""
        # Setup mock extractor
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.extract_traces.return_value = []

        result = runner.invoke(
            app, ["extract-traces", "--date", "2025-01-01", "--project", "test-project"]
        )

        assert result.exit_code == 1
        assert "No matching traces found" in result.stdout

    @patch("lse.commands.eval.TraceExtractor")
    def test_extract_traces_simplified_call(self, mock_extractor_class):
        """Test that extraction uses simplified call without filter parameters."""
        # Setup mock extractor
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        mock_traces = [
            TraceMetadata(
                trace_id="trace-1",
                project="test-project",
                date="2025-01-01",
                has_ai_output=True,
                has_human_feedback=True,
            )
        ]
        mock_extractor.extract_traces.return_value = mock_traces

        result = runner.invoke(
            app,
            [
                "extract-traces",
                "--date",
                "2025-01-01",
                "--project",
                "test-project",
            ],
        )

        assert result.exit_code == 0

        # Verify simplified call without filter parameters
        mock_extractor.extract_traces.assert_called_once_with(
            project="test-project", date="2025-01-01"
        )


class TestCreateDatasetCommand:
    """Tests for create-dataset command."""

    @patch("lse.commands.eval.DatasetBuilder")
    def test_create_dataset_success(self, mock_builder_class, tmp_path):
        """Test successful dataset creation."""
        # Create input traces file
        traces_file = tmp_path / "traces.json"
        traces_data = {
            "date": "2025-01-01",
            "project": "test-project",
            "trace_count": 2,
            "trace_ids": ["trace-1", "trace-2"],
            "traces": [
                {
                    "trace_id": "trace-1",
                    "project": "test-project",
                    "date": "2025-01-01",
                    "has_ai_output": True,
                    "has_human_feedback": False,
                },
                {
                    "trace_id": "trace-2",
                    "project": "test-project",
                    "date": "2025-01-01",
                    "has_ai_output": True,
                    "has_human_feedback": True,
                },
            ],
        }
        with open(traces_file, "w") as f:
            json.dump(traces_data, f)

        # Setup mock builder
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder

        mock_dataset = EvaluationDataset(
            name="test-dataset",
            description="Test description",
            examples=[
                DatasetExample(
                    inputs={"query": "test"},
                    outputs={"response": "test"},
                    metadata={"trace_id": "trace-1"},
                )
            ],
        )
        mock_builder.build_dataset.return_value = mock_dataset

        output_file = tmp_path / "dataset.json"

        result = runner.invoke(
            app,
            [
                "create-dataset",
                "--traces",
                str(traces_file),
                "--output",
                str(output_file),
                "--name",
                "test-dataset",
            ],
        )

        assert result.exit_code == 0
        assert "Created dataset 'test-dataset'" in result.stdout
        assert "1 examples" in result.stdout

        # Check output file
        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)

        assert data["name"] == "test-dataset"
        assert len(data["examples"]) == 1

    def test_create_dataset_missing_traces_file(self):
        """Test dataset creation with missing traces file."""
        result = runner.invoke(app, ["create-dataset", "--traces", "nonexistent.json"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    @patch("lse.commands.eval.DatasetBuilder")
    def test_create_dataset_with_eval_type(self, mock_builder_class, tmp_path):
        """Test dataset creation with eval_type."""
        # Create input traces file
        traces_file = tmp_path / "traces.json"
        traces_data = {
            "date": "2025-01-01",
            "project": "test-project",
            "trace_count": 1,
            "trace_ids": ["trace-1"],
            "traces": [
                {
                    "trace_id": "trace-1",
                    "project": "test-project",
                    "date": "2025-01-01",
                    "has_ai_output": True,
                    "has_human_feedback": True,
                }
            ],
        }
        with open(traces_file, "w") as f:
            json.dump(traces_data, f)

        # Setup mock builder
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder

        mock_dataset = EvaluationDataset(name="test-dataset", examples=[])
        mock_builder.build_dataset.return_value = mock_dataset

        result = runner.invoke(
            app, ["create-dataset", "--traces", str(traces_file), "--eval-type", "accuracy"]
        )

        assert result.exit_code == 0

        # Verify eval_type was passed
        mock_builder.build_dataset.assert_called_once()
        call_args = mock_builder.build_dataset.call_args
        assert call_args[1]["eval_type"] == "accuracy"


class TestUploadCommand:
    """Tests for upload command."""

    @patch("lse.commands.eval.LangSmithUploader")
    def test_upload_success(self, mock_uploader_class, tmp_path):
        """Test successful dataset upload."""
        # Create dataset file
        dataset_file = tmp_path / "dataset.json"
        dataset_data = {
            "name": "test-dataset",
            "description": "Test description",
            "examples": [
                {
                    "inputs": {"query": "test"},
                    "outputs": {"response": "test"},
                    "reference": None,
                    "metadata": {"trace_id": "trace-1"},
                }
            ],
        }
        with open(dataset_file, "w") as f:
            json.dump(dataset_data, f)

        # Setup mock uploader
        mock_uploader = MagicMock()
        mock_uploader_class.return_value = mock_uploader
        mock_uploader.upload_dataset.return_value = "dataset-123"

        result = runner.invoke(app, ["upload", "--dataset", str(dataset_file)])

        assert result.exit_code == 0
        assert "Successfully uploaded dataset" in result.stdout
        assert "dataset-123" in result.stdout

    def test_upload_missing_dataset_file(self):
        """Test upload with missing dataset file."""
        result = runner.invoke(app, ["upload", "--dataset", "nonexistent.json"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    @patch("lse.commands.eval.LangSmithUploader")
    def test_upload_with_overwrite(self, mock_uploader_class, tmp_path):
        """Test upload with overwrite flag."""
        # Create dataset file
        dataset_file = tmp_path / "dataset.json"
        dataset_data = {"name": "test-dataset", "examples": []}
        with open(dataset_file, "w") as f:
            json.dump(dataset_data, f)

        # Setup mock uploader
        mock_uploader = MagicMock()
        mock_uploader_class.return_value = mock_uploader
        mock_uploader.upload_dataset.return_value = "dataset-456"

        result = runner.invoke(app, ["upload", "--dataset", str(dataset_file), "--overwrite"])

        assert result.exit_code == 0

        # Verify overwrite was passed
        mock_uploader.upload_dataset.assert_called_once()
        call_args = mock_uploader.upload_dataset.call_args
        assert call_args[1]["overwrite"] is True


class TestRunCommand:
    """Tests for run command."""

    @patch("lse.commands.eval.EvaluationAPIClient")
    def test_run_success(self, mock_client_class):
        """Test successful evaluation run."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.endpoint = "https://example.com/api"
        mock_client.run_evaluation.return_value = {"status": "success", "id": "eval-123"}

        result = runner.invoke(
            app,
            [
                "run",
                "--dataset-name",
                "test-dataset",
                "--experiment-prefix",
                "exp-001",
                "--eval-type",
                "accuracy",
            ],
        )

        assert result.exit_code == 0
        assert "Evaluation request sent successfully" in result.stdout
        assert "test-dataset" in result.stdout
        assert "exp-001" in result.stdout
        assert "accuracy" in result.stdout

    @patch("lse.commands.eval.EvaluationAPIClient")
    def test_run_with_custom_endpoint(self, mock_client_class):
        """Test run with custom endpoint."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.endpoint = "https://custom.com/api"
        mock_client.run_evaluation.return_value = {"status": "success"}

        result = runner.invoke(
            app,
            [
                "run",
                "--dataset-name",
                "test-dataset",
                "--experiment-prefix",
                "exp-001",
                "--eval-type",
                "accuracy",
                "--endpoint",
                "https://custom.com/api",
            ],
        )

        assert result.exit_code == 0

        # Verify custom endpoint was used
        mock_client_class.assert_called_once_with(endpoint="https://custom.com/api")

    @patch("lse.commands.eval.EvaluationAPIClient")
    def test_run_api_error(self, mock_client_class):
        """Test run with API error."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.endpoint = "https://example.com/api"
        mock_client.run_evaluation.side_effect = Exception("API Error")

        result = runner.invoke(
            app,
            [
                "run",
                "--dataset-name",
                "test-dataset",
                "--experiment-prefix",
                "exp-001",
                "--eval-type",
                "accuracy",
            ],
        )

        assert result.exit_code == 1
        assert "Error initiating evaluation" in result.stdout
