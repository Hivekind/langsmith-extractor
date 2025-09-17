"""Test dataset format compliance with expected structure."""

import json
import pytest
from unittest.mock import Mock, AsyncMock

from lse.evaluation import DatasetBuilder


class TestDatasetFormatCompliance:
    """Test dataset format compliance with expected structure."""

    def test_token_name_format_compliance(self):
        """Test that token_name dataset matches expected format exactly."""
        # Mock database with test data
        mock_db = Mock()
        mock_db.execute = AsyncMock()
        mock_db.fetch_all = AsyncMock(
            return_value=[
                {
                    "trace_id": "test-trace-1",
                    "project": "test-project",
                    "run_date": "2025-01-15",
                    "data": {
                        "inputs": {
                            "input_data": {
                                "name": "Test Token",
                                "crypto_symbol": "TEST",
                                "description": "Test token description",
                            }
                        },
                        "outputs": {
                            "name_analysis": {
                                "meme_check": {"is_meme": True},
                                "explicit_check": {"is_explicit": False},
                                "trademark_check": {"has_conflict": False},
                            }
                        },
                        "feedback_stats": {
                            "final_verdict": {
                                "n": 1,
                                "avg": 1.0,
                                "values": {},
                                "comments": ["Human verdict: PASS"],
                            }
                        },
                    },
                }
            ]
        )

        builder = DatasetBuilder(database=mock_db)

        # Test input extraction
        trace_data = {
            "trace": {
                "inputs": {
                    "input_data": {
                        "name": "Test Token",
                        "crypto_symbol": "TEST",
                        "description": "Test token description",
                    }
                }
            }
        }

        inputs = builder._extract_inputs(trace_data)

        # Validate input fields
        required_input_fields = {"name", "symbol", "description"}
        assert set(inputs.keys()) == required_input_fields
        assert inputs["name"] == "Test Token"
        assert inputs["symbol"] == "TEST"
        assert inputs["description"] == "Test token description"
        assert all(isinstance(inputs[field], str) for field in required_input_fields)

    def test_token_name_output_extraction(self):
        """Test that token_name output extraction produces clean booleans."""
        builder = DatasetBuilder()

        trace_data = {
            "trace": {
                "outputs": {
                    "name_analysis": {
                        "meme_check": {"is_meme": True},
                        "explicit_check": {"is_explicit": False},
                        "trademark_check": {"has_conflict": True},
                    },
                    "final_decision": "PASS",
                    "run": {"should_be_ignored": True},  # Should be ignored
                    "generations": [{"should_be_ignored": True}],  # Should be ignored
                }
            }
        }

        outputs = builder._extract_outputs(trace_data)

        # Validate output fields
        required_output_fields = {
            "is_meme",
            "is_explicit",
            "has_conflict",
            "has_trademark_conflict",
        }
        assert all(field in outputs for field in required_output_fields)
        assert outputs["is_meme"] is True
        assert outputs["is_explicit"] is False
        assert outputs["has_conflict"] is True
        assert outputs["has_trademark_conflict"] is True
        assert all(isinstance(outputs[field], bool) for field in required_output_fields)

    def test_website_format_compliance(self):
        """Test that website dataset matches expected format exactly."""
        builder = DatasetBuilder()

        # Test website input extraction
        trace_data = {
            "trace": {
                "inputs": {
                    "input_data": {
                        "name": "Test Token",
                        "crypto_symbol": "TEST",
                        "description": "Test token description",
                        "website_url": "https://example.com",
                        "network": "ethereum",
                        "contract_address": "0x123...",
                        "social_profiles": [],
                    }
                }
            }
        }

        inputs = builder._extract_inputs(trace_data)

        # Validate input fields
        required_input_fields = {
            "name",
            "symbol",
            "description",
            "website_url",
            "network",
            "contract_address",
            "social_profiles",
        }
        assert set(inputs.keys()) == required_input_fields
        assert isinstance(inputs["social_profiles"], list)

    def test_website_output_extraction(self):
        """Test that website output extraction produces clean booleans."""
        builder = DatasetBuilder()

        trace_data = {
            "trace": {
                "outputs": {
                    "website_analysis": {
                        "meme_check": {"is_meme": False},
                        "explicit_check": {"is_explicit": False},
                        "trademark_check": {"has_conflict": False},
                        "is_available": True,
                        "malicious_check": {"is_dangerous": False},
                    }
                }
            }
        }

        outputs = builder._extract_outputs(trace_data)

        # Validate output fields
        required_output_fields = {
            "is_meme",
            "is_explicit",
            "is_available",
            "is_malicious",
            "has_trademark_conflict",
        }
        assert all(field in outputs for field in required_output_fields)
        assert all(isinstance(outputs[field], bool) for field in required_output_fields)
        assert outputs["is_available"] is True
        assert outputs["is_malicious"] is False

    def test_no_langchain_artifacts(self):
        """Test that no LangChain artifacts appear in output."""
        builder = DatasetBuilder()

        # Test with data that contains LangChain artifacts
        trace_data = {
            "trace": {
                "inputs": {
                    "input_data": {
                        "name": "Test Token",
                        "crypto_symbol": "TEST",
                        "description": "Test description",
                    },
                    "messages": [  # This should be ignored
                        {
                            "id": ["langchain", "schema", "messages", "SystemMessage"],
                            "type": "constructor",
                            "kwargs": {"content": "system prompt"},
                        }
                    ],
                },
                "outputs": {
                    "name_analysis": {"meme_check": {"is_meme": True}},
                    "run": {"should_be_ignored": True},  # Should be ignored
                    "llm_output": {"should_be_ignored": True},  # Should be ignored
                    "generations": [{"should_be_ignored": True}],  # Should be ignored
                    "type": "LLMResult",  # Should be ignored
                },
            }
        }

        inputs = builder._extract_inputs(trace_data)
        outputs = builder._extract_outputs(trace_data)

        # Check inputs don't contain LangChain artifacts
        forbidden_input_keys = {"messages", "id", "lc", "type", "kwargs"}
        assert not any(key in inputs for key in forbidden_input_keys)

        # Check outputs don't contain LangChain artifacts
        forbidden_output_keys = {"run", "llm_output", "generations", "type"}
        assert not any(key in outputs for key in forbidden_output_keys)

    def test_format_methods_with_clean_data(self):
        """Test format methods work correctly with clean extracted data."""
        builder = DatasetBuilder()

        # Clean input data (as would be produced by updated _extract_inputs)
        inputs = {"name": "Test Token", "symbol": "TEST", "description": "Test description"}

        # Clean output data (as would be produced by updated _extract_outputs)
        outputs = {"is_meme": True, "is_explicit": False, "has_conflict": False}

        formatted_inputs, formatted_outputs, reference = builder._format_token_name(
            inputs, outputs, {}
        )

        # Should return clean data with correct structure
        expected_inputs = {
            "name": "Test Token",
            "symbol": "TEST",
            "description": "Test description",
        }
        expected_outputs = {"is_meme": True, "is_explicit": False, "has_conflict": False}

        assert formatted_inputs == expected_inputs
        assert formatted_outputs == expected_outputs
        assert all(isinstance(formatted_outputs[field], bool) for field in formatted_outputs)

    def test_website_format_methods_with_clean_data(self):
        """Test website format methods work correctly with clean extracted data."""
        builder = DatasetBuilder()

        # Clean input data for website
        inputs = {
            "name": "Test Token",
            "symbol": "TEST",
            "network": "ethereum",
            "description": "Test description",
            "website_url": "https://example.com",
            "social_profiles": [],
            "contract_address": "0x123...",
        }

        # Clean output data for website
        outputs = {
            "is_meme": False,
            "is_explicit": False,
            "is_available": True,
            "is_malicious": False,
            "has_trademark_conflict": False,
        }

        formatted_inputs, formatted_outputs, reference = builder._format_website(
            inputs, outputs, {}
        )

        # Should return clean data with correct structure
        expected_inputs = {
            "name": "Test Token",
            "symbol": "TEST",
            "network": "ethereum",
            "description": "Test description",
            "website_url": "https://example.com",
            "social_profiles": [],
            "contract_address": "0x123...",
        }
        expected_outputs = {
            "is_meme": False,
            "is_explicit": False,
            "is_available": True,
            "is_malicious": False,
            "has_trademark_conflict": False,
        }

        assert formatted_inputs == expected_inputs
        assert formatted_outputs == expected_outputs
        assert all(isinstance(formatted_outputs[field], bool) for field in formatted_outputs)


class TestBooleanFieldValidation:
    """Test that all evaluation fields are properly boolean typed."""

    def test_all_output_fields_are_boolean(self):
        """Test that all output fields are converted to proper boolean types."""
        builder = DatasetBuilder()

        # Test with various truthy/falsy values
        trace_data = {
            "trace": {
                "outputs": {
                    "name_analysis": {
                        "meme_check": {"is_meme": 1},  # Should become True
                        "explicit_check": {"is_explicit": 0},  # Should become False
                        "trademark_check": {"has_conflict": "true"},  # Should become True
                    }
                }
            }
        }

        outputs = builder._extract_outputs(trace_data)

        # All should be proper boolean types
        assert outputs["is_meme"] is True
        assert outputs["is_explicit"] is False
        assert outputs["has_conflict"] is True
        assert type(outputs["is_meme"]) is bool
        assert type(outputs["is_explicit"]) is bool
        assert type(outputs["has_conflict"]) is bool


def validate_example_schema(data: dict, eval_type: str):
    """Validate example data against expected schema."""
    # Must have these top-level keys
    assert "inputs" in data
    assert "outputs" in data

    if eval_type == "token_name":
        # Token name inputs
        expected_inputs = {"name", "symbol", "description"}
        assert set(data["inputs"].keys()) == expected_inputs

        # Token name outputs
        expected_outputs = {"is_meme", "is_explicit", "has_conflict"}
        assert set(data["outputs"].keys()) == expected_outputs

    elif eval_type == "website":
        # Website inputs
        expected_inputs = {
            "name",
            "symbol",
            "network",
            "description",
            "website_url",
            "social_profiles",
            "contract_address",
        }
        assert set(data["inputs"].keys()) == expected_inputs

        # Website outputs
        expected_outputs = {
            "is_meme",
            "is_explicit",
            "is_available",
            "is_malicious",
            "has_trademark_conflict",
        }
        assert set(data["outputs"].keys()) == expected_outputs

    # All outputs must be boolean
    for field, value in data["outputs"].items():
        assert isinstance(value, bool), f"Output field {field} must be boolean, got {type(value)}"


class TestJSONLFormatValidation:
    """Test JSONL output format validation."""

    def test_json_serialization(self):
        """Test that extracted data can be serialized to JSON without errors."""
        # Test data with various types
        inputs = {"name": "Test Token", "symbol": "TEST", "description": "Test description"}

        outputs = {"is_meme": True, "is_explicit": False, "has_conflict": False}

        # Should serialize without errors
        try:
            inputs_json = json.dumps(inputs)
            outputs_json = json.dumps(outputs)

            # Should deserialize back to same values
            assert json.loads(inputs_json) == inputs
            assert json.loads(outputs_json) == outputs

        except (TypeError, ValueError) as e:
            pytest.fail(f"JSON serialization failed: {e}")

    def test_complete_example_structure(self):
        """Test complete example structure matches expected format."""
        expected_token_name = {
            "inputs": {"name": "Test Token", "symbol": "TEST", "description": "Test description"},
            "outputs": {"is_meme": False, "is_explicit": False, "has_conflict": True},
        }

        expected_website = {
            "inputs": {
                "name": "Test Token",
                "symbol": "TEST",
                "network": "ethereum",
                "description": "Test description",
                "website_url": "https://example.com",
                "social_profiles": [],
                "contract_address": "0x123...",
            },
            "outputs": {
                "is_meme": False,
                "is_explicit": False,
                "is_available": True,
                "is_malicious": False,
                "has_trademark_conflict": False,
            },
        }

        # Validate schemas
        validate_example_schema(expected_token_name, "token_name")
        validate_example_schema(expected_website, "website")

        # Should serialize to valid JSON
        assert json.dumps(expected_token_name)
        assert json.dumps(expected_website)
