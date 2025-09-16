"""Tests for eval CLI commands."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from lse.commands.eval import app
from lse.evaluation import EvaluationDataset, DatasetExample

runner = CliRunner()


class TestCreateDatasetCommand:
    """Tests for create-dataset command (database-based)."""

    @patch("lse.database.create_database_manager")
    @patch("lse.commands.eval.DatasetBuilder")
    def test_create_dataset_success(self, mock_builder_class, mock_db_manager, tmp_path):
        """Test successful dataset creation from database."""
        # Setup mock database manager
        mock_db = AsyncMock()
        mock_db_manager.return_value = mock_db

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
        mock_builder.create_dataset_from_db = AsyncMock(return_value=mock_dataset)

        output_file = tmp_path / "dataset.jsonl"

        result = runner.invoke(
            app,
            [
                "create-dataset",
                "--project",
                "test-project",
                "--eval-type",
                "token_name",
                "--date",
                "2025-01-01",
                "--output",
                str(output_file),
                "--name",
                "test-dataset",
            ],
        )

        assert result.exit_code == 0
        assert "Created dataset 'test-dataset'" in result.stdout
        assert "1 examples" in result.stdout

        # Check output file exists
        assert output_file.exists()

    @patch("lse.database.create_database_manager")
    @patch("lse.commands.eval.DatasetBuilder")
    def test_create_dataset_date_range(self, mock_builder_class, mock_db_manager, tmp_path):
        """Test dataset creation with date range."""
        # Setup mock database manager
        mock_db = AsyncMock()
        mock_db_manager.return_value = mock_db

        # Setup mock builder
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder

        mock_dataset = EvaluationDataset(
            name="test-dataset-range",
            description="Test description",
            examples=[
                DatasetExample(
                    inputs={"query": "test"},
                    outputs={"response": "test"},
                    metadata={"trace_id": "trace-1"},
                )
            ],
        )
        mock_builder.create_dataset_from_db = AsyncMock(return_value=mock_dataset)

        output_file = tmp_path / "dataset.jsonl"

        result = runner.invoke(
            app,
            [
                "create-dataset",
                "--project",
                "test-project",
                "--eval-type",
                "token_name",
                "--start-date",
                "2025-01-01",
                "--end-date",
                "2025-01-03",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0

    def test_create_dataset_invalid_eval_type(self):
        """Test dataset creation with invalid eval type."""
        result = runner.invoke(
            app,
            [
                "create-dataset",
                "--project",
                "test-project",
                "--eval-type",
                "invalid_type",
                "--date",
                "2025-01-01",
            ],
        )

        assert result.exit_code == 1
        assert "must be 'token_name', 'website', or 'availability'" in result.stdout

    def test_create_dataset_availability_eval_type_validation(self):
        """Test that availability eval type passes CLI validation."""
        with patch("lse.commands.eval.DatasetBuilder") as mock_builder_class:
            # Mock successful dataset creation to avoid database dependency
            mock_builder = MagicMock()
            mock_builder_class.return_value = mock_builder

            mock_dataset = MagicMock()
            mock_dataset.name = "test_availability_dataset"
            mock_builder.create_dataset_from_db = AsyncMock(return_value=mock_dataset)

            result = runner.invoke(
                app,
                [
                    "create-dataset",
                    "--project",
                    "test-project",
                    "--eval-type",
                    "availability",  # This should pass validation
                    "--date",
                    "2025-01-01",
                ],
            )

            # Should pass validation (no exit with error code 1)
            # Note: May still fail due to database connection, but validation should pass
            assert "must be 'token_name', 'website', or 'availability'" not in result.stdout

    def test_create_dataset_conflicting_date_params(self):
        """Test dataset creation with conflicting date parameters."""
        result = runner.invoke(
            app,
            [
                "create-dataset",
                "--project",
                "test-project",
                "--eval-type",
                "token_name",
                "--date",
                "2025-01-01",
                "--start-date",
                "2025-01-01",
            ],
        )

        assert result.exit_code == 1
        assert "Cannot specify both --date and date range options" in result.stdout

    def test_create_dataset_missing_date(self):
        """Test dataset creation with missing date parameters."""
        result = runner.invoke(
            app,
            [
                "create-dataset",
                "--project",
                "test-project",
                "--eval-type",
                "token_name",
            ],
        )

        assert result.exit_code == 1
        assert "Must specify either --date or --start-date" in result.stdout


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

    @patch("lse.commands.eval.LangSmithUploader")
    def test_upload_jsonl_format(self, mock_uploader_class, tmp_path):
        """Test upload with JSONL format detection."""
        # Create JSONL dataset file
        dataset_file = tmp_path / "dataset.jsonl"
        with open(dataset_file, "w") as f:
            f.write('{"inputs": {"query": "test1"}, "outputs": {"response": "test1"}}\n')
            f.write('{"inputs": {"query": "test2"}, "outputs": {"response": "test2"}}\n')

        # Setup mock uploader
        mock_uploader = MagicMock()
        mock_uploader_class.return_value = mock_uploader
        mock_uploader.upload_dataset.return_value = "dataset-456"

        result = runner.invoke(app, ["upload", "--dataset", str(dataset_file)])

        assert result.exit_code == 0
        assert "Successfully uploaded dataset" in result.stdout

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
