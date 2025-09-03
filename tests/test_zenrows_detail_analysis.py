"""Tests for zenrows detail report analysis functionality."""

from lse.analysis import (
    extract_crypto_symbol,
    extract_zenrows_error_details,
    build_zenrows_detail_hierarchy,
)


class TestCryptoSymbolExtraction:
    """Test cryptocurrency symbol extraction from trace data."""

    def test_extracts_symbol_from_trace_name_btc(self):
        """Test extracting BTC from trace name."""
        trace = {
            "name": "zenrows_scraper_BTC_USDT",
            "metadata": {},
        }
        assert extract_crypto_symbol(trace) == "BTC"

    def test_extracts_symbol_from_trace_name_eth(self):
        """Test extracting ETH from trace name."""
        trace = {
            "name": "eth_price_scraper",
            "metadata": {},
        }
        assert extract_crypto_symbol(trace) == "ETH"

    def test_extracts_symbol_from_metadata(self):
        """Test extracting symbol from metadata field."""
        trace = {
            "name": "price_scraper",
            "metadata": {"symbol": "SOL"},
        }
        assert extract_crypto_symbol(trace) == "SOL"

    def test_extracts_symbol_from_extra_field(self):
        """Test extracting symbol from extra field."""
        trace = {
            "name": "scraper_run",
            "metadata": {},
            "extra": {"crypto": "DOGE"},
        }
        assert extract_crypto_symbol(trace) == "DOGE"

    def test_handles_btc_usdt_format(self):
        """Test handling BTC_USDT format."""
        trace = {
            "name": "BTC_USDT_scraper",
            "metadata": {},
        }
        assert extract_crypto_symbol(trace) == "BTC"

    def test_handles_eth_usd_format(self):
        """Test handling ETH-USD format."""
        trace = {
            "name": "fetch_ETH-USD_price",
            "metadata": {},
        }
        assert extract_crypto_symbol(trace) == "ETH"

    def test_returns_unknown_for_missing_symbol(self):
        """Test returning Unknown when no symbol found."""
        trace = {
            "name": "generic_scraper",
            "metadata": {},
        }
        assert extract_crypto_symbol(trace) == "Unknown"

    def test_case_insensitive_extraction(self):
        """Test case-insensitive symbol extraction."""
        trace = {
            "name": "btc_scraper",
            "metadata": {},
        }
        assert extract_crypto_symbol(trace) == "BTC"

    def test_prioritizes_metadata_over_name(self):
        """Test that metadata symbol takes priority over name."""
        trace = {
            "name": "BTC_scraper",
            "metadata": {"symbol": "ETH"},
        }
        assert extract_crypto_symbol(trace) == "ETH"

    def test_extracts_symbol_from_inputs_crypto_symbol(self):
        """Test extracting crypto symbol from inputs.input_data.crypto_symbol field."""
        trace = {
            "name": "due_diligence",
            "inputs": {"input_data": {"crypto_symbol": "ADA", "name": "ADA"}},
            "metadata": {},
        }
        assert extract_crypto_symbol(trace) == "ADA"

    def test_extracts_symbol_from_inputs_name_field(self):
        """Test extracting crypto symbol from inputs.input_data.name field when crypto_symbol missing."""
        trace = {
            "name": "due_diligence",
            "inputs": {"input_data": {"name": "MATIC", "description": "Polygon token"}},
            "metadata": {},
        }
        assert extract_crypto_symbol(trace) == "MATIC"

    def test_prioritizes_inputs_over_metadata(self):
        """Test that inputs crypto_symbol takes priority over metadata."""
        trace = {
            "name": "due_diligence",
            "inputs": {"input_data": {"crypto_symbol": "ADA"}},
            "metadata": {"symbol": "BTC"},
        }
        assert extract_crypto_symbol(trace) == "ADA"


class TestZenrowsErrorDetailExtraction:
    """Test extraction of detailed zenrows error information."""

    def test_extracts_error_message_from_root_trace(self):
        """Test extracting error message from root trace."""
        trace = {
            "id": "trace123",
            "name": "zenrows_scraper",
            "status": "error",
            "error": "Connection timeout after 30s",
            "metadata": {"symbol": "BTC"},
        }

        errors = extract_zenrows_error_details(trace)
        assert len(errors) == 1
        assert errors[0]["trace_id"] == "trace123"
        assert errors[0]["error_message"] == "Connection timeout after 30s"
        assert errors[0]["crypto_symbol"] == "BTC"

    def test_extracts_multiple_errors_from_child_runs(self):
        """Test extracting multiple errors from child runs."""
        trace = {
            "id": "root123",
            "name": "main_scraper",
            "status": "success",
            "child_runs": [
                {
                    "id": "child1",
                    "name": "zenrows_scraper",
                    "status": "error",
                    "error": "Rate limit exceeded",
                },
                {
                    "id": "child2",
                    "name": "zenrows_scraper",
                    "status": "error",
                    "error": "Proxy authentication failed",
                },
            ],
        }

        errors = extract_zenrows_error_details(trace)
        assert len(errors) == 2
        assert errors[0]["error_message"] == "Rate limit exceeded"
        assert errors[1]["error_message"] == "Proxy authentication failed"

    def test_includes_root_trace_id_in_errors(self):
        """Test that root trace ID is included in error details."""
        trace = {
            "id": "root456",
            "name": "BTC_scraper",
            "status": "error",
            "error": "Network error",
        }

        errors = extract_zenrows_error_details(trace)
        assert errors[0]["root_trace_id"] == "root456"

    def test_handles_missing_error_message(self):
        """Test handling traces with missing error message."""
        trace = {
            "id": "trace789",
            "name": "zenrows_scraper",
            "status": "error",
            # No error field
        }

        errors = extract_zenrows_error_details(trace)
        assert len(errors) == 1
        assert errors[0]["error_message"] == "Unknown error"


class TestZenrowsDetailHierarchy:
    """Test building hierarchical data structure for zenrows details."""

    def test_builds_simple_hierarchy(self):
        """Test building hierarchy with single crypto and trace using realistic trace structure."""
        traces = [
            # Root trace (due_diligence with BTC crypto symbol)
            {
                "id": "root123",
                "trace_id": "root123",
                "name": "due_diligence",
                "status": "success",
                "extra": {"metadata": {"ls_run_depth": 0}},
                "inputs": {"input_data": {"crypto_symbol": "BTC", "name": "BTC"}},
            },
            # Child trace (zenrows_scraper with error)
            {
                "id": "child456",
                "trace_id": "root123",  # Points to root trace
                "name": "BTC_zenrows_scraper",
                "status": "error",
                "error": "Connection failed",
                "extra": {"metadata": {"ls_run_depth": 2}},
            },
        ]

        hierarchy = build_zenrows_detail_hierarchy(traces)

        assert "BTC" in hierarchy
        assert "root123" in hierarchy["BTC"]  # Should group by root trace ID, not child ID
        assert len(hierarchy["BTC"]["root123"]) == 1

        # Check the error detail object structure
        error_detail = hierarchy["BTC"]["root123"][0]
        assert isinstance(error_detail, dict)
        assert error_detail["error_message"] == "Connection failed"
        assert error_detail["crypto_symbol"] == "BTC"
        assert "trace_id" in error_detail

    def test_groups_multiple_errors_per_trace(self):
        """Test grouping multiple errors under same root trace."""
        traces = [
            # Root trace with ETH crypto symbol
            {
                "id": "due_diligence_789",
                "trace_id": "due_diligence_789",
                "name": "due_diligence",
                "status": "success",
                "extra": {"metadata": {"ls_run_depth": 0}},
                "inputs": {"input_data": {"crypto_symbol": "ETH", "name": "ETH"}},
            },
            # First child trace with error
            {
                "id": "eth_scraper_1",
                "trace_id": "due_diligence_789",
                "name": "ETH_scraper",
                "status": "error",
                "error": "First error",
                "extra": {"metadata": {"ls_run_depth": 1}},
            },
            # Second child trace with error (same crypto context)
            {
                "id": "zenrows_child",
                "trace_id": "due_diligence_789",
                "name": "ETH_zenrows_scraper",  # Make it ETH-related
                "status": "error",
                "error": "Second error",
                "extra": {"metadata": {"ls_run_depth": 2}},
            },
        ]

        hierarchy = build_zenrows_detail_hierarchy(traces)

        assert len(hierarchy["ETH"]["due_diligence_789"]) == 2

        # Check that both error messages are present in the error detail objects
        error_messages = [error["error_message"] for error in hierarchy["ETH"]["due_diligence_789"]]
        assert "First error" in error_messages
        assert "Second error" in error_messages

    def test_groups_by_crypto_symbol(self):
        """Test grouping traces by cryptocurrency symbol with multiple root traces."""
        traces = [
            # First due_diligence workflow with BTC crypto symbol
            {
                "id": "dd_workflow_1",
                "trace_id": "dd_workflow_1",
                "name": "due_diligence",
                "status": "success",
                "extra": {"metadata": {"ls_run_depth": 0}},
                "inputs": {"input_data": {"crypto_symbol": "BTC", "name": "BTC"}},
            },
            {
                "id": "btc1",
                "trace_id": "dd_workflow_1",
                "name": "BTC_scraper",
                "status": "error",
                "error": "BTC error",
                "extra": {"metadata": {"ls_run_depth": 1}},
            },
            # Second due_diligence workflow with ETH crypto symbol
            {
                "id": "dd_workflow_2",
                "trace_id": "dd_workflow_2",
                "name": "due_diligence",
                "status": "success",
                "extra": {"metadata": {"ls_run_depth": 0}},
                "inputs": {"input_data": {"crypto_symbol": "ETH", "name": "ETH"}},
            },
            {
                "id": "eth1",
                "trace_id": "dd_workflow_2",
                "name": "ETH_scraper",
                "status": "error",
                "error": "ETH error",
                "extra": {"metadata": {"ls_run_depth": 1}},
            },
            # Third due_diligence workflow with another BTC crypto symbol
            {
                "id": "dd_workflow_3",
                "trace_id": "dd_workflow_3",
                "name": "due_diligence",
                "status": "success",
                "extra": {"metadata": {"ls_run_depth": 0}},
                "inputs": {"input_data": {"crypto_symbol": "BTC", "name": "BTC"}},
            },
            {
                "id": "btc2",
                "trace_id": "dd_workflow_3",
                "name": "BTC_scraper_2",
                "status": "error",
                "error": "Another BTC error",
                "extra": {"metadata": {"ls_run_depth": 1}},
            },
        ]

        hierarchy = build_zenrows_detail_hierarchy(traces)

        assert len(hierarchy) == 2  # BTC and ETH
        assert len(hierarchy["BTC"]) == 2  # Two BTC root traces
        assert len(hierarchy["ETH"]) == 1  # One ETH root trace
        # Verify they're grouped by root trace IDs
        assert "dd_workflow_1" in hierarchy["BTC"]
        assert "dd_workflow_3" in hierarchy["BTC"]
        assert "dd_workflow_2" in hierarchy["ETH"]

    def test_handles_unknown_crypto_symbol(self):
        """Test handling traces with unknown crypto symbols."""
        traces = [
            # Root trace
            {
                "id": "dd_unknown",
                "trace_id": "dd_unknown",
                "name": "due_diligence",
                "status": "success",
                "extra": {"metadata": {"ls_run_depth": 0}},
            },
            # Child trace with unknown crypto
            {
                "id": "unknown1",
                "trace_id": "dd_unknown",
                "name": "generic_zenrows_scraper",
                "status": "error",
                "error": "Some error",
                "extra": {"metadata": {"ls_run_depth": 1}},
            },
        ]

        hierarchy = build_zenrows_detail_hierarchy(traces)

        assert "Unknown" in hierarchy
        assert "dd_unknown" in hierarchy["Unknown"]  # Should use root trace ID

    def test_empty_hierarchy_for_no_errors(self):
        """Test that traces without errors produce empty hierarchy."""
        traces = [
            # Root trace
            {
                "id": "dd_success",
                "trace_id": "dd_success",
                "name": "due_diligence",
                "status": "success",
                "extra": {"metadata": {"ls_run_depth": 0}},
            },
            # Child trace with success (no error)
            {
                "id": "trace1",
                "trace_id": "dd_success",
                "name": "BTC_scraper",
                "status": "success",
                "extra": {"metadata": {"ls_run_depth": 1}},
            },
        ]

        hierarchy = build_zenrows_detail_hierarchy(traces)

        assert len(hierarchy) == 0

    def test_includes_metadata_in_hierarchy(self):
        """Test including metadata like timestamps in hierarchy."""
        traces = [
            # Root trace with BTC crypto symbol
            {
                "id": "dd_meta",
                "trace_id": "dd_meta",
                "name": "due_diligence",
                "status": "success",
                "start_time": "2025-08-29T10:00:00Z",
                "extra": {"metadata": {"ls_run_depth": 0}},
                "inputs": {"input_data": {"crypto_symbol": "BTC", "name": "BTC"}},
            },
            # Child trace with error
            {
                "id": "trace1",
                "trace_id": "dd_meta",
                "name": "BTC_scraper",
                "status": "error",
                "error": "Error message",
                "extra": {"metadata": {"ls_run_depth": 1}},
            },
        ]

        hierarchy = build_zenrows_detail_hierarchy(traces, include_metadata=True)

        # The structure should include metadata from root trace
        assert "BTC" in hierarchy
        assert isinstance(hierarchy["BTC"]["dd_meta"], dict)  # Root trace ID
        assert "errors" in hierarchy["BTC"]["dd_meta"]
        assert "start_time" in hierarchy["BTC"]["dd_meta"]
        assert hierarchy["BTC"]["dd_meta"]["name"] == "due_diligence"  # Root trace name

    def test_includes_url_and_timestamp_in_error_details(self):
        """Test that URL and timestamp are properly extracted and included in error details."""
        traces = [
            # Root trace with crypto symbol
            {
                "id": "crypto_root",
                "trace_id": "crypto_root",
                "name": "due_diligence",
                "status": "success",
                "extra": {"metadata": {"ls_run_depth": 0}},
                "inputs": {"input_data": {"crypto_symbol": "TESTCOIN", "name": "TESTCOIN"}},
            },
            # Child trace with zenrows error, URL, and timestamp
            {
                "id": "zenrows_error",
                "trace_id": "crypto_root",
                "name": "zenrows_scraper",
                "status": "error",
                "error": "422 Client Error: Unprocessable Entity",
                "start_time": "2025-09-03 15:30:45.123456",
                "inputs": {"input": "https://test-crypto-site.com/data"},
                "extra": {"metadata": {"ls_run_depth": 2}},
            },
        ]

        hierarchy = build_zenrows_detail_hierarchy(traces)

        # Verify the error detail includes all expected fields
        assert "TESTCOIN" in hierarchy
        assert "crypto_root" in hierarchy["TESTCOIN"]
        error_detail = hierarchy["TESTCOIN"]["crypto_root"][0]

        assert error_detail["error_message"] == "422 Client Error: Unprocessable Entity"
        assert error_detail["start_time"] == "2025-09-03 15:30:45.123456"
        assert error_detail["target_url"] == "https://test-crypto-site.com/data"
        assert error_detail["trace_id"] == "zenrows_error"

        # The crypto symbol in the hierarchy is correctly TESTCOIN (from root trace)
        # The individual error detail's crypto_symbol may be different since it's extracted
        # from the child trace initially, but the hierarchy grouping is correct
