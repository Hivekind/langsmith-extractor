"""Tests for enhanced formatters with error categorization support."""

from lse.formatters import ReportFormatter, format_csv_report
from lse.error_categories import get_category_breakdown_columns


class TestEnhancedCSVFormatting:
    """Test cases for enhanced CSV formatting with category columns."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ReportFormatter()

    def create_test_data_with_categories(self) -> dict:
        """Create test analysis data with category breakdowns."""
        return {
            "2025-09-04": {
                "total_traces": 100,
                "zenrows_errors": 15,
                "error_rate": 0.15,
                "categories": {
                    "http_404_not_found": 8,  # 53.3% of errors
                    "http_422_unprocessable": 3,  # 20.0% of errors
                    "read_timeout": 2,  # 13.3% of errors
                    "http_413_too_large": 1,  # 6.7% of errors
                    "http_400_bad_request": 1,  # 6.7% of errors
                    "http_503_service_unavailable": 0,
                    "unknown_errors": 0,
                },
            },
            "2025-09-05": {
                "total_traces": 80,
                "zenrows_errors": 8,
                "error_rate": 0.1,
                "categories": {
                    "http_404_not_found": 3,
                    "http_422_unprocessable": 2,
                    "read_timeout": 1,
                    "http_413_too_large": 1,
                    "http_400_bad_request": 0,
                    "http_503_service_unavailable": 1,
                    "unknown_errors": 0,
                },
            },
        }

    def test_enhanced_csv_includes_category_columns(self):
        """Test that enhanced CSV output includes category columns."""
        test_data = self.create_test_data_with_categories()

        csv_output = self.formatter.format_zenrows_report(test_data)
        lines = csv_output.strip().split("\n")

        # Check header includes all category columns
        header = lines[0]
        assert header.startswith("Date,Total Traces,Zenrows Errors")

        # Should include all category columns
        expected_categories = get_category_breakdown_columns()
        for category in expected_categories:
            assert category in header

    def test_category_columns_ordered_by_frequency(self):
        """Test that category columns are ordered by frequency (most common first)."""
        test_data = self.create_test_data_with_categories()

        csv_output = self.formatter.format_zenrows_report(test_data)
        header = csv_output.split("\n")[0]

        # Categories should be ordered by their production frequency
        # http_404_not_found (50.4%) should come before http_422_unprocessable (18.2%)
        pos_404 = header.find("http_404_not_found")
        pos_422 = header.find("http_422_unprocessable")
        assert pos_404 < pos_422, "404 errors should come before 422 errors in header"

        pos_timeout = header.find("read_timeout")
        assert pos_422 < pos_timeout, "422 errors should come before timeouts"

    def test_csv_data_rows_include_category_counts(self):
        """Test that CSV data rows include category counts."""
        test_data = self.create_test_data_with_categories()

        csv_output = self.formatter.format_zenrows_report(test_data)
        lines = csv_output.strip().split("\n")

        # Check first data row (2025-09-04)
        data_row_1 = lines[1]
        assert data_row_1.startswith("2025-09-04,100,15")

        # Should include category counts: 8,3,2,1,1,0,0 (in frequency order)
        # The exact order depends on get_category_breakdown_columns()
        assert "8" in data_row_1  # http_404_not_found
        assert "3" in data_row_1  # http_422_unprocessable
        assert "2" in data_row_1  # read_timeout

        # Check second data row (2025-09-05)
        data_row_2 = lines[2]
        assert data_row_2.startswith("2025-09-05,80,8")

    def test_category_counts_sum_validation(self):
        """Test that category counts sum to total error count."""
        test_data = self.create_test_data_with_categories()

        csv_output = self.formatter.format_zenrows_report(test_data)
        lines = csv_output.strip().split("\n")

        header_parts = lines[0].split(",")

        # Find the indices of category count columns
        category_count_indices = []
        category_columns = get_category_breakdown_columns()

        # All columns are now count columns
        for count_column in category_columns:
            if count_column in header_parts:
                category_count_indices.append(header_parts.index(count_column))

        # Check each data row
        for i, line in enumerate(lines[1:], 1):
            parts = line.split(",")
            total_errors = int(parts[2])  # zenrows_errors column

            # Sum category counts
            category_sum = sum(int(parts[idx]) for idx in category_count_indices)

            assert category_sum == total_errors, (
                f"Row {i}: category sum ({category_sum}) != total errors ({total_errors})"
            )

    def test_backward_compatibility_preserved(self):
        """Test that existing fields are preserved in original order."""
        test_data = self.create_test_data_with_categories()

        csv_output = self.formatter.format_zenrows_report(test_data)
        header = csv_output.split("\n")[0]

        # Original fields should be in original order at the start (without error rate)
        expected_start = "Date,Total Traces,Zenrows Errors"
        assert header.startswith(expected_start)

        # Category columns should be added after core columns, error rate at end
        original_columns = expected_start.split(",")
        header_parts = header.split(",")

        for i, expected_col in enumerate(original_columns):
            assert header_parts[i] == expected_col

    def test_empty_data_handling(self):
        """Test handling of empty analysis data."""
        csv_output = self.formatter.format_zenrows_report({})

        # Should return basic header even with no data
        assert "Date,Total Traces,Zenrows Errors" in csv_output
        assert csv_output.endswith("Error Rate\n")
        assert csv_output.count("\n") == 1  # Just header + newline

    def test_missing_categories_handling(self):
        """Test handling when category data is missing."""
        data_without_categories = {
            "2025-09-04": {
                "total_traces": 100,
                "zenrows_errors": 5,
                "error_rate": 0.05,
                # No 'categories' key
            }
        }

        csv_output = self.formatter.format_zenrows_report(data_without_categories)
        lines = csv_output.strip().split("\n")

        # Should still work and show zeros for all categories
        assert len(lines) == 2  # header + 1 data row
        data_row = lines[1]
        assert data_row.startswith("2025-09-04,100,5")

    def test_zero_errors_all_categories_zero(self):
        """Test that when no errors exist, all categories are zero."""
        data_no_errors = {
            "2025-09-04": {
                "total_traces": 100,
                "zenrows_errors": 0,
                "error_rate": 0.0,
                "categories": {
                    "http_404_not_found": 0,
                    "http_422_unprocessable": 0,
                    "read_timeout": 0,
                    "http_413_too_large": 0,
                    "http_400_bad_request": 0,
                    "http_503_service_unavailable": 0,
                    "unknown_errors": 0,
                },
            }
        }

        csv_output = self.formatter.format_zenrows_report(data_no_errors)
        lines = csv_output.strip().split("\n")

        data_row = lines[1]
        assert data_row.startswith("2025-09-04,100,0")

        # All category columns should show 0
        assert ",0," in data_row or data_row.endswith(",0")

    def test_unknown_errors_category_handling(self):
        """Test handling of unknown_errors category."""
        data_with_unknown = {
            "2025-09-04": {
                "total_traces": 50,
                "zenrows_errors": 3,
                "error_rate": 0.06,
                "categories": {
                    "http_404_not_found": 1,
                    "http_422_unprocessable": 0,
                    "read_timeout": 0,
                    "http_413_too_large": 0,
                    "http_400_bad_request": 0,
                    "http_503_service_unavailable": 0,
                    "unknown_errors": 2,  # Should be handled properly
                },
            }
        }

        csv_output = self.formatter.format_zenrows_report(data_with_unknown)
        lines = csv_output.strip().split("\n")

        header = lines[0]
        assert "unknown_errors" in header

        data_row = lines[1]
        assert data_row.startswith("2025-09-04,50,3")

    def test_date_sorting_maintained(self):
        """Test that date sorting is maintained in enhanced output."""
        unsorted_data = {
            "2025-09-06": {
                "total_traces": 30,
                "zenrows_errors": 2,
                "error_rate": 0.067,
                "categories": {"http_404_not_found": 2, "unknown_errors": 0},
            },
            "2025-09-04": {
                "total_traces": 40,
                "zenrows_errors": 1,
                "error_rate": 0.025,
                "categories": {"http_404_not_found": 1, "unknown_errors": 0},
            },
            "2025-09-05": {
                "total_traces": 35,
                "zenrows_errors": 3,
                "error_rate": 0.086,
                "categories": {"http_404_not_found": 3, "unknown_errors": 0},
            },
        }

        csv_output = self.formatter.format_zenrows_report(unsorted_data)
        lines = csv_output.strip().split("\n")

        # Dates should be sorted
        assert lines[1].startswith("2025-09-04")
        assert lines[2].startswith("2025-09-05")
        assert lines[3].startswith("2025-09-06")


class TestLegacyCSVCompatibility:
    """Test cases for backward compatibility with existing CSV format functions."""

    def test_format_csv_report_without_categories(self):
        """Test that legacy format_csv_report function still works."""
        legacy_data = {"2025-09-04": {"total_traces": 100, "zenrows_errors": 5, "error_rate": 0.05}}

        csv_output = format_csv_report(legacy_data, "Test Report")
        lines = csv_output.strip().split("\n")

        assert len(lines) == 2  # header + 1 data row
        assert lines[0] == "Date,Total Traces,Zenrows Errors,Error Rate"
        assert lines[1] == "2025-09-04,100,5,0.0500"

    def test_existing_tests_compatibility(self):
        """Test that existing formatter usage patterns still work."""
        formatter = ReportFormatter()

        # Test with old-style data (no categories)
        old_style_data = {
            "2025-09-04": {"total_traces": 50, "zenrows_errors": 2, "error_rate": 0.04}
        }

        # Should not throw errors
        csv_output = formatter.format_zenrows_report(old_style_data)
        assert isinstance(csv_output, str)
        assert "2025-09-04" in csv_output


class TestCategoryColumnGeneration:
    """Test cases for category column generation and ordering."""

    def test_get_category_breakdown_columns_order(self):
        """Test that category columns are returned in frequency order."""
        columns = get_category_breakdown_columns()

        # Should be ordered by frequency from ErrorCategoryManager
        assert isinstance(columns, list)
        assert len(columns) >= 7  # At least 7 categories with count columns

        # Most common categories should be first (count columns only)
        assert columns[0] == "http_404_not_found_count"  # 50.4%
        assert columns[1] == "http_422_unprocessable_count"  # 18.2%
        assert columns[2] == "read_timeout_count"  # 13.2%

        # Unknown errors should be last
        assert columns[-1] == "unknown_errors_count"

    def test_all_categories_included_in_csv(self):
        """Test that all defined categories are included in CSV output."""
        formatter = ReportFormatter()
        test_data = {
            "2025-09-04": {
                "total_traces": 100,
                "zenrows_errors": 0,
                "error_rate": 0.0,
                "categories": {
                    "http_404_not_found": 0,
                    "http_422_unprocessable": 0,
                    "read_timeout": 0,
                    "http_413_too_large": 0,
                    "http_400_bad_request": 0,
                    "http_503_service_unavailable": 0,
                    "unknown_errors": 0,
                },
            }
        }

        csv_output = formatter.format_zenrows_report(test_data)
        header = csv_output.split("\n")[0]

        # All categories should be in header
        for category in get_category_breakdown_columns():
            assert category in header


class TestProductionDataPatterns:
    """Test cases using realistic production data patterns."""

    def test_realistic_error_distribution(self):
        """Test CSV output with realistic error distribution based on production data."""
        # Based on actual production analysis: 50.4% 404s, 18.2% 422s, 13.2% timeouts, etc.
        realistic_data = {
            "2025-09-04": {
                "total_traces": 1000,
                "zenrows_errors": 121,  # Based on actual production data
                "error_rate": 0.121,
                "categories": {
                    "http_404_not_found": 61,  # 50.4% of errors
                    "http_422_unprocessable": 22,  # 18.2% of errors
                    "read_timeout": 16,  # 13.2% of errors
                    "http_413_too_large": 15,  # 12.4% of errors
                    "http_400_bad_request": 7,  # 5.8% of errors
                    "http_503_service_unavailable": 1,  # 0.8% of errors
                    "unknown_errors": 0,
                },
            }
        }

        formatter = ReportFormatter()
        csv_output = formatter.format_zenrows_report(realistic_data)
        lines = csv_output.strip().split("\n")

        # Verify structure
        assert len(lines) == 2  # header + 1 data row

        data_row = lines[1]
        assert data_row.startswith("2025-09-04,1000,121")

        # Verify that the most common error types are represented
        assert "61" in data_row  # http_404_not_found count
        assert "22" in data_row  # http_422_unprocessable count

    def test_multi_day_production_pattern(self):
        """Test multi-day CSV output with varying error patterns."""
        multi_day_data = {
            "2025-09-04": {
                "total_traces": 500,
                "zenrows_errors": 25,
                "error_rate": 0.05,
                "categories": {
                    "http_404_not_found": 15,
                    "http_422_unprocessable": 5,
                    "read_timeout": 3,
                    "http_413_too_large": 2,
                    "http_400_bad_request": 0,
                    "http_503_service_unavailable": 0,
                    "unknown_errors": 0,
                },
            },
            "2025-09-05": {
                "total_traces": 750,
                "zenrows_errors": 30,
                "error_rate": 0.04,
                "categories": {
                    "http_404_not_found": 18,
                    "http_422_unprocessable": 6,
                    "read_timeout": 4,
                    "http_413_too_large": 1,
                    "http_400_bad_request": 1,
                    "http_503_service_unavailable": 0,
                    "unknown_errors": 0,
                },
            },
        }

        formatter = ReportFormatter()
        csv_output = formatter.format_zenrows_report(multi_day_data)
        lines = csv_output.strip().split("\n")

        assert len(lines) == 3  # header + 2 data rows

        # Check both days are properly formatted
        assert lines[1].startswith("2025-09-04,500,25")
        assert lines[2].startswith("2025-09-05,750,30")

    def test_edge_case_all_unknown_errors(self):
        """Test handling when all errors are unknown/unclassified."""
        unknown_heavy_data = {
            "2025-09-04": {
                "total_traces": 100,
                "zenrows_errors": 10,
                "error_rate": 0.1,
                "categories": {
                    "http_404_not_found": 0,
                    "http_422_unprocessable": 0,
                    "read_timeout": 0,
                    "http_413_too_large": 0,
                    "http_400_bad_request": 0,
                    "http_503_service_unavailable": 0,
                    "unknown_errors": 10,  # All errors are unknown
                },
            }
        }

        formatter = ReportFormatter()
        csv_output = formatter.format_zenrows_report(unknown_heavy_data)

        # Should handle gracefully
        assert "2025-09-04,100,10" in csv_output
        assert "unknown_errors" in csv_output.split("\n")[0]  # In header
