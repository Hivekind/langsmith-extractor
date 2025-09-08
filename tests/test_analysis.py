"""Tests for trace analysis functionality."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from lse.analysis import (
    TraceAnalyzer,
    find_trace_files,
    parse_trace_file,
    extract_zenrows_errors,
    group_by_date,
    calculate_error_rates,
)
from lse.exceptions import ValidationError


class TestTraceFileDiscovery:
    """Test trace file discovery and filtering functionality."""

    def test_find_trace_files_single_date(self):
        """Test finding trace files for a single date."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)

            # Create test directory structure
            date_dir = base_path / "test-project" / "2025-08-29"
            date_dir.mkdir(parents=True)

            # Create test trace files
            (date_dir / "trace1_123456.json").touch()
            (date_dir / "trace2_234567.json").touch()
            (date_dir / "_summary.json").touch()  # Should be ignored

            files = find_trace_files(base_path, "test-project", datetime(2025, 8, 29))

            assert len(files) == 2
            assert all(f.name.endswith(".json") for f in files)
            assert all(not f.name.startswith("_") for f in files)

    def test_find_trace_files_missing_directory(self):
        """Test handling of missing project directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)

            files = find_trace_files(base_path, "nonexistent-project", datetime(2025, 8, 29))

            assert files == []

    def test_find_trace_files_requires_date_parameter(self):
        """Test that date parameter is required."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)

            with pytest.raises(ValidationError, match="Date parameter is required"):
                find_trace_files(base_path, "test-project")


class TestTraceFileParsing:
    """Test JSON trace file parsing functionality."""

    def test_parse_valid_trace_file(self):
        """Test parsing a valid trace file."""
        trace_data = {
            "metadata": {
                "extracted_at": "2025-08-29T16:37:45.101243",
                "project_name": "test-project",
                "run_id": "test-run-id",
            },
            "trace": {
                "id": "test-run-id",
                "name": "test_trace",
                "start_time": "2025-08-29 06:44:12.622037",
                "status": "success",
                "child_runs": [],
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
            json.dump(trace_data, temp_file)
            temp_file.flush()

            result = parse_trace_file(Path(temp_file.name))

            assert result["id"] == "test-run-id"
            assert result["name"] == "test_trace"
            assert "start_time" in result

    def test_parse_malformed_json_file(self):
        """Test handling of malformed JSON files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
            temp_file.write('{"invalid": json}')
            temp_file.flush()

            result = parse_trace_file(Path(temp_file.name))

            assert result is None

    def test_parse_missing_trace_key(self):
        """Test handling of JSON files missing trace key."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
            json.dump({"metadata": {"run_id": "test"}}, temp_file)
            temp_file.flush()

            result = parse_trace_file(Path(temp_file.name))

            assert result is None


class TestZenrowsErrorDetection:
    """Test zenrows_scraper error detection logic."""

    def test_detect_zenrows_error_in_child_runs(self):
        """Test detection of zenrows_scraper errors in child runs."""
        trace_data = {
            "id": "parent-trace",
            "name": "due_diligence",
            "status": "success",
            "child_runs": [
                {"id": "child-1", "name": "website_check", "status": "success"},
                {
                    "id": "child-2",
                    "name": "zenrows_scraper",
                    "status": "error",
                    "error": "HTTP 429 Too Many Requests",
                },
            ],
        }

        errors = extract_zenrows_errors(trace_data)

        assert len(errors) == 1
        assert errors[0]["id"] == "child-2"
        assert errors[0]["error"] == "HTTP 429 Too Many Requests"

    def test_detect_nested_zenrows_errors(self):
        """Test detection of zenrows errors in nested child runs."""
        trace_data = {
            "id": "parent-trace",
            "name": "due_diligence",
            "status": "success",
            "child_runs": [
                {
                    "id": "level1-child",
                    "name": "analysis_step",
                    "status": "success",
                    "child_runs": [
                        {
                            "id": "level2-child",
                            "name": "zenrows_scraper",
                            "status": "error",
                            "error": "Rate limit exceeded",
                        }
                    ],
                }
            ],
        }

        errors = extract_zenrows_errors(trace_data)

        assert len(errors) == 1
        assert errors[0]["id"] == "level2-child"

    def test_case_insensitive_name_matching(self):
        """Test case-insensitive matching for zenrows_scraper names."""
        trace_data = {
            "id": "parent-trace",
            "child_runs": [
                {
                    "id": "child-1",
                    "name": "ZENROWS_SCRAPER",  # Uppercase
                    "status": "error",
                },
                {
                    "id": "child-2",
                    "name": "Zenrows_Scraper",  # Mixed case
                    "status": "error",
                },
            ],
        }

        errors = extract_zenrows_errors(trace_data)

        assert len(errors) == 2

    def test_no_errors_when_zenrows_success(self):
        """Test that successful zenrows runs are not counted as errors."""
        trace_data = {
            "id": "parent-trace",
            "child_runs": [{"id": "child-1", "name": "zenrows_scraper", "status": "success"}],
        }

        errors = extract_zenrows_errors(trace_data)

        assert len(errors) == 0

    def test_handles_missing_child_runs(self):
        """Test handling of traces without child_runs field."""
        trace_data = {"id": "parent-trace", "name": "simple_trace", "status": "success"}

        errors = extract_zenrows_errors(trace_data)

        assert len(errors) == 0

    def test_handles_none_child_runs(self):
        """Test handling of traces with null child_runs field."""
        trace_data = {
            "id": "parent-trace",
            "name": "simple_trace",
            "status": "success",
            "child_runs": None,
        }

        errors = extract_zenrows_errors(trace_data)

        assert len(errors) == 0

    def test_detect_root_level_zenrows_error(self):
        """Test detection of zenrows_scraper error at root trace level."""
        trace_data = {
            "id": "root-trace",
            "name": "zenrows_scraper",
            "status": "error",
            "error": "HTTPError('422 Unprocessable Entity')",
            "start_time": "2025-08-20 03:29:35.040455",
            "end_time": "2025-08-20 03:29:39.371309",
            "child_runs": None,
        }

        errors = extract_zenrows_errors(trace_data)

        assert len(errors) == 1
        assert errors[0]["id"] == "root-trace"
        assert errors[0]["name"] == "zenrows_scraper"
        assert errors[0]["status"] == "error"
        assert "422" in errors[0]["error"]

    def test_detect_root_and_child_zenrows_errors(self):
        """Test detection of zenrows errors at both root and child levels."""
        trace_data = {
            "id": "root-trace",
            "name": "zenrows_scraper",
            "status": "error",
            "error": "Root level error",
            "child_runs": [
                {
                    "id": "child-1",
                    "name": "zenrows_scraper",
                    "status": "error",
                    "error": "Child level error",
                }
            ],
        }

        errors = extract_zenrows_errors(trace_data)

        assert len(errors) == 2
        # Root error should be first
        assert errors[0]["id"] == "root-trace"
        assert errors[0]["error"] == "Root level error"
        # Child error should be second
        assert errors[1]["id"] == "child-1"
        assert errors[1]["error"] == "Child level error"

    def test_root_level_success_not_counted(self):
        """Test that successful root-level zenrows_scraper is not counted as error."""
        trace_data = {
            "id": "root-trace",
            "name": "zenrows_scraper",
            "status": "success",
            "child_runs": None,
        }

        errors = extract_zenrows_errors(trace_data)

        assert len(errors) == 0

    def test_root_level_case_insensitive(self):
        """Test case-insensitive detection at root level."""
        trace_data = {
            "id": "root-trace",
            "name": "ZENROWS_SCRAPER",  # Uppercase
            "status": "ERROR",  # Uppercase
            "error": "Some error",
            "child_runs": None,
        }

        errors = extract_zenrows_errors(trace_data)

        assert len(errors) == 1
        assert errors[0]["name"] == "ZENROWS_SCRAPER"


class TestDateGrouping:
    """Test date-based grouping of trace data."""

    def test_group_traces_by_date(self):
        """Test grouping traces by their date."""
        traces = [
            {"start_time": "2025-08-29 06:44:12.622037", "id": "trace1"},
            {"start_time": "2025-08-29 10:30:45.123456", "id": "trace2"},
            {"start_time": "2025-08-30 08:15:30.987654", "id": "trace3"},
        ]

        grouped = group_by_date(traces)

        assert len(grouped) == 2
        assert "2025-08-29" in grouped
        assert "2025-08-30" in grouped
        assert len(grouped["2025-08-29"]) == 2
        assert len(grouped["2025-08-30"]) == 1

    def test_group_handles_various_datetime_formats(self):
        """Test grouping with different datetime formats in traces."""
        traces = [
            {"start_time": "2025-08-29T06:44:12.622037Z", "id": "trace1"},  # ISO format
            {"start_time": "2025-08-29 06:44:12", "id": "trace2"},  # Simple format
        ]

        grouped = group_by_date(traces)

        assert len(grouped) == 1
        assert "2025-08-29" in grouped
        assert len(grouped["2025-08-29"]) == 2

    def test_group_handles_missing_start_time(self):
        """Test handling of traces missing start_time field."""
        traces = [
            {"id": "trace1"},  # Missing start_time
            {"start_time": "2025-08-29 06:44:12", "id": "trace2"},
        ]

        grouped = group_by_date(traces)

        # Should only include the trace with valid start_time
        assert len(grouped) == 1
        assert len(grouped["2025-08-29"]) == 1


class TestErrorRateCalculation:
    """Test error rate calculation functionality."""

    def test_calculate_error_rates_basic(self):
        """Test basic error rate calculation."""
        daily_data = {
            "2025-08-29": {"total_traces": 10, "zenrows_errors": 2},
            "2025-08-30": {"total_traces": 5, "zenrows_errors": 0},
        }

        rates = calculate_error_rates(daily_data)

        assert rates["2025-08-29"]["error_rate"] == 20.0
        assert rates["2025-08-30"]["error_rate"] == 0.0

    def test_calculate_error_rates_zero_traces(self):
        """Test error rate calculation when no traces exist."""
        daily_data = {"2025-08-29": {"total_traces": 0, "zenrows_errors": 0}}

        rates = calculate_error_rates(daily_data)

        assert rates["2025-08-29"]["error_rate"] == 0.0

    def test_calculate_error_rates_precision(self):
        """Test error rate calculation precision."""
        daily_data = {
            "2025-08-29": {
                "total_traces": 3,
                "zenrows_errors": 1,  # 33.333...%
            }
        }

        rates = calculate_error_rates(daily_data)

        # Should round to 1 decimal place
        assert abs(rates["2025-08-29"]["error_rate"] - 33.3) < 0.1


class TestTraceAnalyzer:
    """Test the main TraceAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = TraceAnalyzer()

    def test_analyzer_processes_single_date(self):
        """Test analyzer processing traces for a single date."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)

            # Create test directory and trace file
            date_dir = base_path / "test-project" / "2025-08-29"
            date_dir.mkdir(parents=True)

            # Create test trace with zenrows error
            trace_data = {
                "metadata": {"project_name": "test-project", "run_id": "test-id"},
                "trace": {
                    "id": "test-id",
                    "name": "test_trace",
                    "start_time": "2025-08-29 10:00:00",
                    "status": "success",
                    "child_runs": [
                        {
                            "id": "child-1",
                            "name": "zenrows_scraper",
                            "status": "error",
                            "error": "HTTP 429",
                        }
                    ],
                },
            }

            trace_file = date_dir / "test_trace_100000.json"
            with open(trace_file, "w") as f:
                json.dump(trace_data, f)

            # Process the traces
            result = self.analyzer.analyze_zenrows_errors(
                data_dir=base_path, project_name="test-project", single_date=datetime(2025, 8, 29)
            )

            assert "2025-08-29" in result
            assert result["2025-08-29"]["total_traces"] == 1
            assert result["2025-08-29"]["zenrows_errors"] == 1
            assert result["2025-08-29"]["error_rate"] == 100.0

    def test_analyzer_handles_large_trace_files(self):
        """Test that analyzer can handle large trace files efficiently."""
        # This is a placeholder test for memory efficiency
        # In a real implementation, we would test with very large files
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            date_dir = base_path / "test-project" / "2025-08-29"
            date_dir.mkdir(parents=True)

            # Create a trace with many child runs
            child_runs = []
            for i in range(100):
                child_runs.append(
                    {
                        "id": f"child-{i}",
                        "name": "zenrows_scraper" if i % 10 == 0 else "other_tool",
                        "status": "error" if i % 20 == 0 else "success",
                    }
                )

            trace_data = {
                "metadata": {"project_name": "test-project", "run_id": "large-trace"},
                "trace": {
                    "id": "large-trace",
                    "start_time": "2025-08-29 10:00:00",
                    "child_runs": child_runs,
                },
            }

            with open(date_dir / "large_trace.json", "w") as f:
                json.dump(trace_data, f)

            result = self.analyzer.analyze_zenrows_errors(
                data_dir=base_path, project_name="test-project", single_date=datetime(2025, 8, 29)
            )

            # Should have found 10 zenrows_scraper runs, with 5 errors (every 20th, which includes 0, 20, 40, 60, 80)
            expected_errors = len([i for i in range(100) if i % 10 == 0 and i % 20 == 0])
            assert result["2025-08-29"]["zenrows_errors"] == expected_errors


class TestIntegrationScenarios:
    """Test integration scenarios with realistic data."""

    def test_real_trace_structure_compatibility(self):
        """Test compatibility with real trace file structure."""
        # Based on the actual trace structure we observed
        real_trace_data = {
            "metadata": {
                "extracted_at": "2025-08-29T16:37:45.101243",
                "project_name": "test-project",
                "run_id": "352853a7-328b-4466-9ddf-45369c2b6bb5",
            },
            "trace": {
                "id": "352853a7-328b-4466-9ddf-45369c2b6bb5",
                "name": "due_diligence",
                "start_time": "2025-08-29 06:44:12.622037",
                "run_type": "chain",
                "status": "success",
                "child_runs": None,  # Real traces might have null child_runs
                "child_run_ids": None,
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            date_dir = base_path / "test-project" / "2025-08-29"
            date_dir.mkdir(parents=True)

            trace_file = date_dir / "real_trace.json"
            with open(trace_file, "w") as f:
                json.dump(real_trace_data, f)

            analyzer = TraceAnalyzer()
            result = analyzer.analyze_zenrows_errors(
                data_dir=base_path,
                project_name="test-project",
                single_date=datetime(2025, 8, 29),
            )

            # Should handle null child_runs gracefully
            assert result["2025-08-29"]["total_traces"] == 1
            assert result["2025-08-29"]["zenrows_errors"] == 0
            assert result["2025-08-29"]["error_rate"] == 0.0

    def test_mixed_trace_formats(self):
        """Test handling mixed trace formats in same directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            date_dir = base_path / "test-project" / "2025-08-29"
            date_dir.mkdir(parents=True)

            # Create traces with different formats
            traces = [
                {
                    "trace": {
                        "id": "trace1",
                        "start_time": "2025-08-29 10:00:00",
                        "child_runs": [{"name": "zenrows_scraper", "status": "error"}],
                    }
                },
                {
                    "trace": {
                        "id": "trace2",
                        "start_time": "2025-08-29 11:00:00",
                        "child_runs": None,
                    }
                },
                # Malformed trace file - should be skipped
                {"invalid": "structure"},
            ]

            for i, trace_data in enumerate(traces):
                with open(date_dir / f"trace{i}.json", "w") as f:
                    json.dump(trace_data, f)

            analyzer = TraceAnalyzer()
            result = analyzer.analyze_zenrows_errors(
                data_dir=base_path, project_name="test-project", single_date=datetime(2025, 8, 29)
            )

            # Should process valid traces and skip malformed ones
            assert result["2025-08-29"]["total_traces"] == 2
            assert result["2025-08-29"]["zenrows_errors"] == 1
            assert result["2025-08-29"]["error_rate"] == 50.0

    def test_root_vs_child_trace_counting(self):
        """Test that error rate uses root trace count, not total trace count."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            date_dir = base_path / "test-project" / "2025-08-29"
            date_dir.mkdir(parents=True)

            # Create 2 root traces and 3 child traces (5 total)
            traces = [
                {
                    "metadata": {"trace_id": "root1"},
                    "trace": {
                        "id": "root1",
                        "name": "root_trace_1",
                        "start_time": "2025-08-29 10:00:00",
                        # No parent_run_id = root trace
                    },
                },
                {
                    "metadata": {"trace_id": "root2"},
                    "trace": {
                        "id": "root2",
                        "name": "root_trace_2",
                        "start_time": "2025-08-29 11:00:00",
                        # No parent_run_id = root trace
                    },
                },
                {
                    "metadata": {"trace_id": "child1"},
                    "trace": {
                        "id": "child1",
                        "name": "zenrows_scraper",
                        "status": "error",
                        "start_time": "2025-08-29 10:05:00",
                        "parent_run_id": "root1",  # Child of root1
                    },
                },
                {
                    "metadata": {"trace_id": "child2"},
                    "trace": {
                        "id": "child2",
                        "name": "zenrows_scraper",
                        "status": "error",
                        "start_time": "2025-08-29 11:05:00",
                        "parent_run_id": "root2",  # Child of root2
                    },
                },
                {
                    "metadata": {"trace_id": "child3"},
                    "trace": {
                        "id": "child3",
                        "name": "other_operation",
                        "status": "success",
                        "start_time": "2025-08-29 12:00:00",
                        "parent_run_id": "root2",  # Child of root2
                    },
                },
            ]

            for i, trace_data in enumerate(traces):
                with open(date_dir / f"trace{i}.json", "w") as f:
                    json.dump(trace_data, f)

            analyzer = TraceAnalyzer()
            result = analyzer.analyze_zenrows_errors(
                data_dir=base_path, project_name="test-project", single_date=datetime(2025, 8, 29)
            )

            # Should count only 2 root traces for total, but find 2 errors across all traces
            assert result["2025-08-29"]["total_traces"] == 2  # Only root traces
            assert result["2025-08-29"]["zenrows_errors"] == 2  # Errors from child traces
            assert result["2025-08-29"]["error_rate"] == 100.0  # 2/2 = 100%
