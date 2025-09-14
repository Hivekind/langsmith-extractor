"""Test data extraction methods for evaluation dataset generation."""

from lse.evaluation import DatasetBuilder


class TestInputExtraction:
    """Test input extraction methods."""

    def test_extract_inputs_token_name(self):
        """Test input extraction for token_name eval type."""
        builder = DatasetBuilder()

        trace_data = {
            "trace": {
                "inputs": {
                    "input_data": {
                        "name": "Test Token",
                        "crypto_symbol": "TEST",
                        "description": "Test description",
                    },
                    "messages": [{"id": ["langchain"], "type": "constructor"}],
                }
            }
        }

        inputs = builder._extract_inputs(trace_data)

        expected = {"name": "Test Token", "symbol": "TEST", "description": "Test description"}
        assert inputs == expected

    def test_extract_inputs_website(self):
        """Test input extraction for website eval type."""
        builder = DatasetBuilder()

        trace_data = {
            "trace": {
                "inputs": {
                    "input_data": {
                        "name": "Test Token",
                        "crypto_symbol": "TEST",
                        "description": "Test description",
                        "website_url": "https://example.com",
                        "network": "ethereum",
                        "contract_address": "0x123...",
                        "social_profiles": [
                            {"platform": "twitter", "url": "https://twitter.com/test"}
                        ],
                    }
                }
            }
        }

        inputs = builder._extract_inputs(trace_data)

        expected = {
            "name": "Test Token",
            "symbol": "TEST",
            "description": "Test description",
            "website_url": "https://example.com",
            "network": "ethereum",
            "contract_address": "0x123...",
            "social_profiles": [{"platform": "twitter", "url": "https://twitter.com/test"}],
        }
        assert inputs == expected

    def test_extract_inputs_fallback_to_direct_fields(self):
        """Test input extraction falls back to direct fields when input_data not available."""
        builder = DatasetBuilder()

        trace_data = {
            "trace": {
                "inputs": {
                    "name": "Fallback Token",
                    "crypto_symbol": "FALLBACK",
                    "description": "Fallback description",
                }
            }
        }

        inputs = builder._extract_inputs(trace_data)

        expected = {
            "name": "Fallback Token",
            "symbol": "FALLBACK",
            "description": "Fallback description",
        }
        assert inputs == expected

    def test_extract_inputs_database_format(self):
        """Test input extraction works with database format (no trace wrapper)."""
        builder = DatasetBuilder()

        trace_data = {
            "inputs": {
                "input_data": {
                    "name": "DB Token",
                    "crypto_symbol": "DB",
                    "description": "Database format",
                }
            }
        }

        inputs = builder._extract_inputs(trace_data)

        expected = {"name": "DB Token", "symbol": "DB", "description": "Database format"}
        assert inputs == expected

    def test_extract_inputs_symbol_mapping(self):
        """Test that crypto_symbol is correctly mapped to symbol."""
        builder = DatasetBuilder()

        # Test crypto_symbol mapping
        trace_data1 = {
            "trace": {
                "inputs": {
                    "input_data": {
                        "name": "Test Token",
                        "crypto_symbol": "CRYPTO_TEST",
                        "description": "Test",
                    }
                }
            }
        }

        inputs1 = builder._extract_inputs(trace_data1)
        assert inputs1["symbol"] == "CRYPTO_TEST"

        # Test direct symbol field
        trace_data2 = {
            "trace": {
                "inputs": {
                    "input_data": {
                        "name": "Test Token",
                        "symbol": "DIRECT_TEST",
                        "description": "Test",
                    }
                }
            }
        }

        inputs2 = builder._extract_inputs(trace_data2)
        assert inputs2["symbol"] == "DIRECT_TEST"


class TestOutputExtraction:
    """Test output extraction methods."""

    def test_extract_outputs_boolean_conversion(self):
        """Test output extraction converts nested results to booleans."""
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

        expected = {
            "is_meme": True,
            "is_explicit": False,
            "has_conflict": True,
            "has_trademark_conflict": True,
        }

        # Check core fields are extracted correctly
        assert outputs["is_meme"] == expected["is_meme"]
        assert outputs["is_explicit"] == expected["is_explicit"]
        assert outputs["has_conflict"] == expected["has_conflict"]
        assert outputs["has_trademark_conflict"] == expected["has_trademark_conflict"]

        # Check all are proper boolean types
        assert type(outputs["is_meme"]) is bool
        assert type(outputs["is_explicit"]) is bool
        assert type(outputs["has_conflict"]) is bool
        assert type(outputs["has_trademark_conflict"]) is bool

    def test_extract_outputs_website_analysis(self):
        """Test output extraction for website analysis."""
        builder = DatasetBuilder()

        trace_data = {
            "trace": {
                "outputs": {
                    "website_analysis": {
                        "meme_check": {"is_meme": False},
                        "explicit_check": {"is_explicit": False},
                        "trademark_check": {"has_conflict": False},
                        "is_available": True,
                        "malicious_check": {"is_dangerous": True},
                    }
                }
            }
        }

        outputs = builder._extract_outputs(trace_data)

        assert outputs["is_meme"] is False
        assert outputs["is_explicit"] is False
        assert outputs["has_conflict"] is False
        assert outputs["has_trademark_conflict"] is False
        assert outputs["is_available"] is True
        assert outputs["is_malicious"] is True

    def test_extract_outputs_mixed_analysis(self):
        """Test output extraction with both name_analysis and website_analysis."""
        builder = DatasetBuilder()

        trace_data = {
            "trace": {
                "outputs": {
                    "name_analysis": {
                        "meme_check": {"is_meme": True},
                        "trademark_check": {"has_conflict": False},
                    },
                    "website_analysis": {
                        "explicit_check": {"is_explicit": True},
                        "is_available": False,
                        "malicious_check": {"is_dangerous": False},
                    },
                }
            }
        }

        outputs = builder._extract_outputs(trace_data)

        # Should get meme from name_analysis
        assert outputs["is_meme"] is True
        # Should get explicit from website_analysis
        assert outputs["is_explicit"] is True
        # Should get conflict from name_analysis
        assert outputs["has_conflict"] is False
        # Should get website-specific fields
        assert outputs["is_available"] is False
        assert outputs["is_malicious"] is False

    def test_extract_outputs_fallback_to_direct_fields(self):
        """Test output extraction falls back to direct fields when nested analysis not available."""
        builder = DatasetBuilder()

        trace_data = {
            "trace": {
                "outputs": {
                    "is_meme": True,
                    "is_explicit": False,
                    "has_conflict": True,
                    "is_available": True,
                    "is_malicious": False,
                }
            }
        }

        outputs = builder._extract_outputs(trace_data)

        assert outputs["is_meme"] is True
        assert outputs["is_explicit"] is False
        assert outputs["has_conflict"] is True
        assert outputs["has_trademark_conflict"] is True  # Should copy from has_conflict

    def test_extract_outputs_database_format(self):
        """Test output extraction works with database format (no trace wrapper)."""
        builder = DatasetBuilder()

        trace_data = {
            "outputs": {
                "name_analysis": {
                    "meme_check": {"is_meme": False},
                    "explicit_check": {"is_explicit": True},
                    "trademark_check": {"has_conflict": False},
                }
            }
        }

        outputs = builder._extract_outputs(trace_data)

        assert outputs["is_meme"] is False
        assert outputs["is_explicit"] is True
        assert outputs["has_conflict"] is False

    def test_extract_boolean_results_method(self):
        """Test the _extract_boolean_results helper method."""
        builder = DatasetBuilder()
        outputs = {}

        name_analysis = {"meme_check": {"is_meme": True}, "explicit_check": {"is_explicit": False}}
        website_analysis = {
            "trademark_check": {"has_conflict": True},
            "is_available": False,
            "malicious_check": {"is_dangerous": True},
        }
        trace_outputs = {}

        builder._extract_boolean_results(outputs, name_analysis, website_analysis, trace_outputs)

        assert outputs["is_meme"] is True
        assert outputs["is_explicit"] is False
        assert outputs["has_conflict"] is True
        assert outputs["has_trademark_conflict"] is True
        assert outputs["is_available"] is False
        assert outputs["is_malicious"] is True

    def test_extract_boolean_results_with_non_dict_values(self):
        """Test _extract_boolean_results handles non-dict values correctly."""
        builder = DatasetBuilder()
        outputs = {}

        name_analysis = {
            "meme_check": True,  # Not a dict - should be used directly as boolean
            "explicit_check": False,  # Not a dict - should be used directly as boolean
        }
        website_analysis = {}
        trace_outputs = {
            "is_meme": False,  # Should be ignored since meme_check has a value
            "is_explicit": True,  # Should be ignored since explicit_check has a value
        }

        builder._extract_boolean_results(outputs, name_analysis, website_analysis, trace_outputs)

        # Should use non-dict values directly as booleans
        assert outputs["is_meme"] is True
        assert outputs["is_explicit"] is False


class TestFormatMethodIntegration:
    """Test format methods work correctly with clean extracted data."""

    def test_format_token_name_with_clean_data(self):
        """Test _format_token_name works with clean extracted data."""
        builder = DatasetBuilder()

        # Clean input data (as would be produced by updated _extract_inputs)
        inputs = {"name": "Test Token", "symbol": "TEST", "description": "Test description"}

        # Clean output data (as would be produced by updated _extract_outputs)
        outputs = {"is_meme": True, "is_explicit": False, "has_conflict": False}

        formatted_inputs, formatted_outputs, reference = builder._format_token_name(
            inputs, outputs, {"test": "reference"}
        )

        # Should return clean data unchanged
        expected_inputs = {
            "name": "Test Token",
            "symbol": "TEST",
            "description": "Test description",
        }
        expected_outputs = {"is_meme": True, "is_explicit": False, "has_conflict": False}

        assert formatted_inputs == expected_inputs
        assert formatted_outputs == expected_outputs
        assert reference == {"test": "reference"}

    def test_format_website_with_clean_data(self):
        """Test _format_website works with clean extracted data."""
        builder = DatasetBuilder()

        # Clean input data for website
        inputs = {
            "name": "Test Token",
            "symbol": "TEST",
            "network": "ethereum",
            "description": "Test description",
            "website_url": "https://example.com",
            "social_profiles": [{"platform": "twitter"}],
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

        # Should return clean data unchanged
        expected_inputs = {
            "name": "Test Token",
            "symbol": "TEST",
            "network": "ethereum",
            "description": "Test description",
            "website_url": "https://example.com",
            "social_profiles": [{"platform": "twitter"}],
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

    def test_format_methods_handle_missing_fields(self):
        """Test format methods handle missing fields gracefully."""
        builder = DatasetBuilder()

        # Incomplete input data
        inputs = {
            "name": "Test Token"
            # Missing symbol, description
        }

        # Incomplete output data
        outputs = {
            "is_meme": True
            # Missing other fields
        }

        formatted_inputs, formatted_outputs, reference = builder._format_token_name(
            inputs, outputs, {}
        )

        # Should fill in missing fields with defaults
        assert formatted_inputs["name"] == "Test Token"
        assert formatted_inputs["symbol"] == ""  # Default empty string
        assert formatted_inputs["description"] == ""  # Default empty string

        assert formatted_outputs["is_meme"] is True
        assert formatted_outputs["is_explicit"] is False  # Default False
        assert formatted_outputs["has_conflict"] is False  # Default False


class TestDataConsistency:
    """Test data consistency across extraction and formatting."""

    def test_end_to_end_token_name_processing(self):
        """Test complete token_name processing pipeline."""
        builder = DatasetBuilder()

        # Raw trace data as it comes from database/files
        trace_data = {
            "trace": {
                "inputs": {
                    "input_data": {
                        "name": "End To End Token",
                        "crypto_symbol": "E2E",
                        "description": "Full pipeline test",
                    },
                    "messages": [  # Should be ignored
                        {
                            "id": ["langchain", "schema", "messages", "SystemMessage"],
                            "type": "constructor",
                        }
                    ],
                },
                "outputs": {
                    "name_analysis": {
                        "meme_check": {"is_meme": True},
                        "explicit_check": {"is_explicit": False},
                        "trademark_check": {"has_conflict": True},
                    },
                    "run": {"should_be_ignored": True},
                    "llm_output": {"should_be_ignored": True},
                },
            }
        }

        # Extract clean data
        inputs = builder._extract_inputs(trace_data)
        outputs = builder._extract_outputs(trace_data)

        # Format for token_name eval type
        formatted_inputs, formatted_outputs, reference = builder._format_token_name(
            inputs, outputs, {}
        )

        # Final result should match expected format exactly
        expected_result = {
            "inputs": {
                "name": "End To End Token",
                "symbol": "E2E",
                "description": "Full pipeline test",
            },
            "outputs": {"is_meme": True, "is_explicit": False, "has_conflict": True},
        }

        assert formatted_inputs == expected_result["inputs"]
        assert formatted_outputs == expected_result["outputs"]

        # Ensure no artifacts remain
        assert "messages" not in formatted_inputs
        assert "run" not in formatted_outputs
        assert "llm_output" not in formatted_outputs
        assert "name_analysis" not in formatted_outputs

    def test_end_to_end_website_processing(self):
        """Test complete website processing pipeline."""
        builder = DatasetBuilder()

        trace_data = {
            "trace": {
                "inputs": {
                    "input_data": {
                        "name": "Website Token",
                        "crypto_symbol": "WEB",
                        "description": "Website evaluation test",
                        "website_url": "https://website-token.com",
                        "network": "polygon",
                        "contract_address": "0xwebsite123",
                        "social_profiles": [
                            {"platform": "telegram", "url": "https://t.me/websitetoken"}
                        ],
                    }
                },
                "outputs": {
                    "website_analysis": {
                        "meme_check": {"is_meme": False},
                        "explicit_check": {"is_explicit": False},
                        "trademark_check": {"has_conflict": False},
                        "is_available": True,
                        "malicious_check": {"is_dangerous": False},
                    }
                },
            }
        }

        # Process through pipeline
        inputs = builder._extract_inputs(trace_data)
        outputs = builder._extract_outputs(trace_data)
        formatted_inputs, formatted_outputs, reference = builder._format_website(
            inputs, outputs, {}
        )

        # Verify final format
        expected_inputs = {
            "name": "Website Token",
            "symbol": "WEB",
            "network": "polygon",
            "description": "Website evaluation test",
            "website_url": "https://website-token.com",
            "social_profiles": [{"platform": "telegram", "url": "https://t.me/websitetoken"}],
            "contract_address": "0xwebsite123",
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
