"""Tests for output formatting functionality."""

from lse.formatters import ReportFormatter, format_csv_report, format_summary_stats


class TestCSVFormatting:
    """Test CSV output formatting functionality."""

    def test_format_csv_report_basic(self):
        """Test basic CSV report formatting."""
        analysis_data = {
            "2025-08-29": {"total_traces": 10, "zenrows_errors": 2, "error_rate": 0.2},
            "2025-08-30": {"total_traces": 5, "zenrows_errors": 0, "error_rate": 0.0},
        }

        result = format_csv_report(analysis_data)

        lines = result.strip().split("\n")
        assert lines[0] == "Date,Total Traces,Zenrows Errors,Error Rate"
        assert lines[1] == "2025-08-29,10,2,0.2000"
        assert lines[2] == "2025-08-30,5,0,0.0000"

    def test_format_csv_report_sorted_dates(self):
        """Test that CSV output is sorted by date."""
        analysis_data = {
            "2025-08-30": {"total_traces": 5, "zenrows_errors": 0, "error_rate": 0.0},
            "2025-08-28": {"total_traces": 8, "zenrows_errors": 1, "error_rate": 0.125},
            "2025-08-29": {"total_traces": 10, "zenrows_errors": 2, "error_rate": 0.2},
        }

        result = format_csv_report(analysis_data)

        lines = result.strip().split("\n")
        assert "2025-08-28" in lines[1]
        assert "2025-08-29" in lines[2]
        assert "2025-08-30" in lines[3]

    def test_format_csv_report_empty_data(self):
        """Test CSV formatting with empty analysis data."""
        result = format_csv_report({})

        assert result == "Date,Total Traces,Zenrows Errors,Error Rate\n"

    def test_format_csv_report_precision(self):
        """Test CSV formatting with decimal precision."""
        analysis_data = {
            "2025-08-29": {
                "total_traces": 3,
                "zenrows_errors": 1,
                "error_rate": 0.333333,  # Should be formatted to 33.3%
            }
        }

        result = format_csv_report(analysis_data)

        assert "0.3333" in result


class TestSummaryStatistics:
    """Test summary statistics calculation."""

    def test_format_summary_stats_basic(self):
        """Test basic summary statistics calculation."""
        analysis_data = {
            "2025-08-28": {"total_traces": 10, "zenrows_errors": 1, "error_rate": 0.1},
            "2025-08-29": {"total_traces": 20, "zenrows_errors": 4, "error_rate": 0.2},
            "2025-08-30": {"total_traces": 5, "zenrows_errors": 0, "error_rate": 0.0},
        }

        stats = format_summary_stats(analysis_data)

        assert stats["total_days"] == 3
        assert stats["total_traces"] == 35
        assert stats["total_zenrows_errors"] == 5
        assert abs(stats["overall_error_rate"] - 0.142857) < 0.000001  # 5/35 = 0.142857...
        assert stats["worst_day"] == "2025-08-29"
        assert stats["best_day"] == "2025-08-30"

    def test_format_summary_stats_empty_data(self):
        """Test summary statistics with empty data."""
        stats = format_summary_stats({})

        assert stats["total_days"] == 0
        assert stats["total_traces"] == 0
        assert stats["total_zenrows_errors"] == 0
        assert stats["overall_error_rate"] == 0.0
        assert stats["worst_day"] is None
        assert stats["best_day"] is None

    def test_format_summary_stats_single_day(self):
        """Test summary statistics with single day data."""
        analysis_data = {"2025-08-29": {"total_traces": 10, "zenrows_errors": 2, "error_rate": 0.2}}

        stats = format_summary_stats(analysis_data)

        assert stats["total_days"] == 1
        assert stats["worst_day"] == "2025-08-29"
        assert stats["best_day"] == "2025-08-29"


class TestReportFormatter:
    """Test the main ReportFormatter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ReportFormatter()

    def test_format_zenrows_report(self):
        """Test zenrows-specific report formatting."""
        analysis_data = {"2025-08-29": {"total_traces": 10, "zenrows_errors": 2, "error_rate": 0.2}}

        result = self.formatter.format_zenrows_report(analysis_data)

        assert "Date,Total Traces,Zenrows Errors,Error Rate" in result
        assert "2025-08-29,10,2,0.2000" in result

    def test_format_zenrows_report_empty(self):
        """Test zenrows report formatting with empty data."""
        result = self.formatter.format_zenrows_report({})

        assert result == "Date,Total Traces,Zenrows Errors,Error Rate\n"

    def test_format_summary(self):
        """Test human-readable summary formatting."""
        analysis_data = {
            "2025-08-28": {"total_traces": 10, "zenrows_errors": 1, "error_rate": 0.1},
            "2025-08-29": {"total_traces": 20, "zenrows_errors": 4, "error_rate": 0.2},
        }

        result = self.formatter.format_summary(analysis_data)

        assert "=== Zenrows Error Rate Summary ===" in result
        assert "2 day(s)" in result
        assert "Total traces analyzed: 30" in result
        assert "Total zenrows errors: 5" in result
        assert "Overall error rate: 16.7%" in result  # 5/30 = 0.1666... -> 16.7%
        assert "Worst day: 2025-08-29 (20.0%)" in result
        assert "Best day: 2025-08-28 (10.0%)" in result

    def test_format_summary_empty(self):
        """Test summary formatting with empty data."""
        result = self.formatter.format_summary({})

        assert "No data available" in result


class TestOutputIntegration:
    """Test integration of formatting with analysis results."""

    def test_end_to_end_csv_formatting(self):
        """Test complete CSV formatting workflow."""
        # Simulate realistic analysis results
        analysis_data = {
            "2025-08-25": {"total_traces": 15, "zenrows_errors": 0, "error_rate": 0.0},
            "2025-08-26": {"total_traces": 32, "zenrows_errors": 3, "error_rate": 0.094},
            "2025-08-27": {"total_traces": 28, "zenrows_errors": 7, "error_rate": 0.25},
            "2025-08-28": {"total_traces": 41, "zenrows_errors": 2, "error_rate": 0.049},
            "2025-08-29": {"total_traces": 19, "zenrows_errors": 1, "error_rate": 0.053},
        }

        formatter = ReportFormatter()
        csv_output = formatter.format_zenrows_report(analysis_data)

        # Verify structure
        lines = csv_output.strip().split("\n")
        assert len(lines) == 6  # Header + 5 data rows
        assert lines[0] == "Date,Total Traces,Zenrows Errors,Error Rate"

        # Verify date ordering
        dates_in_output = [line.split(",")[0] for line in lines[1:]]
        assert dates_in_output == sorted(dates_in_output)

        # Verify specific data points
        assert "2025-08-27,28,7,0.2500" in csv_output
        assert "2025-08-25,15,0,0.0000" in csv_output

    def test_stdout_compatibility(self):
        """Test that output is compatible with stdout piping."""
        analysis_data = {
            "2025-08-29": {"total_traces": 100, "zenrows_errors": 5, "error_rate": 5.0}
        }

        formatter = ReportFormatter()
        output = formatter.format_zenrows_report(analysis_data)

        # Should end with single newline for clean piping
        assert output.endswith("\n")
        assert not output.endswith("\n\n")

        # Should not contain any console formatting or colors
        assert "\x1b[" not in output  # ANSI escape codes
        assert "[green]" not in output  # Rich markup


class TestURLPatternFormatter:
    """Test URL pattern analysis formatting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ReportFormatter()

    def test_format_zenrows_url_patterns_basic(self):
        """Test basic URL pattern formatting."""
        url_results = {
            "domains": {
                "example.com": {
                    "count": 5,
                    "error_categories": {
                        "http_404_not_found": 3,
                        "http_422_unprocessable": 2,
                    },
                },
                "test.org": {
                    "count": 2,
                    "error_categories": {
                        "read_timeout": 2,
                    },
                },
            },
            "file_types": {
                "pdf": {
                    "count": 4,
                    "error_categories": {
                        "http_413_too_large": 3,
                        "http_404_not_found": 1,
                    },
                },
                "html": {
                    "count": 3,
                    "error_categories": {
                        "http_404_not_found": 2,
                        "http_422_unprocessable": 1,
                    },
                },
            },
            "total_analyzed": 7,
            "traces_without_urls": 0,
            "total_zenrows_traces": 10,
        }

        result = self.formatter.format_zenrows_url_patterns_report(url_results)
        lines = result.strip().split("\n")

        # Check header
        assert lines[0] == "Type,Name,Count,Top Error Categories"

        # Check domain entries (should be sorted by count descending)
        assert 'domain,example.com,5,"http_404_not_found(3);http_422_unprocessable(2)"' in result
        assert 'domain,test.org,2,"read_timeout(2)"' in result

        # Check file type entries (should be sorted by count descending)
        assert 'file_type,pdf,4,"http_413_too_large(3);http_404_not_found(1)"' in result
        assert 'file_type,html,3,"http_404_not_found(2);http_422_unprocessable(1)"' in result

        # Check summary
        assert "# Summary: 7 errors analyzed from 10 total ZenRows traces, 0 without URLs" in result

    def test_format_zenrows_url_patterns_empty_data(self):
        """Test URL pattern formatting with empty data."""
        result = self.formatter.format_zenrows_url_patterns_report({})
        assert result == "Type,Name,Count,Top Error Categories\n"

    def test_format_zenrows_url_patterns_top_limit(self):
        """Test URL pattern formatting with top limit."""
        url_results = {
            "domains": {
                "first.com": {"count": 5, "error_categories": {"error1": 5}},
                "second.com": {"count": 4, "error_categories": {"error2": 4}},
                "third.com": {"count": 3, "error_categories": {"error3": 3}},
                "fourth.com": {"count": 2, "error_categories": {"error4": 2}},
            },
            "file_types": {
                "pdf": {"count": 6, "error_categories": {"error_pdf": 6}},
                "html": {"count": 5, "error_categories": {"error_html": 5}},
                "image": {"count": 4, "error_categories": {"error_img": 4}},
            },
            "total_analyzed": 10,
            "traces_without_urls": 0,
            "total_zenrows_traces": 15,
        }

        # Test with top=2 limit
        result = self.formatter.format_zenrows_url_patterns_report(url_results, top=2)

        # Should only show top 2 domains and top 2 file types
        assert result.count("domain,") == 2  # Only 2 domain entries
        assert result.count("file_type,") == 2  # Only 2 file type entries
        assert "first.com" in result  # Top domain
        assert "second.com" in result  # Second domain
        assert "third.com" not in result  # Should be excluded
        assert "pdf" in result  # Top file type
        assert "html" in result  # Second file type

    def test_format_zenrows_url_patterns_sorted_by_frequency(self):
        """Test that formatter handles pre-sorted data correctly (analysis function sorts by frequency)."""
        # Data comes pre-sorted from analysis function - simulate that here
        url_results = {
            "domains": {
                "high.com": {"count": 10, "error_categories": {"error2": 10}},  # Highest first
                "medium.com": {"count": 5, "error_categories": {"error3": 5}},  # Medium second
                "low.com": {"count": 1, "error_categories": {"error1": 1}},  # Lowest last
            },
            "file_types": {
                "common": {"count": 8, "error_categories": {"error2": 8}},  # Higher first
                "rare": {"count": 2, "error_categories": {"error1": 2}},  # Lower second
            },
            "total_analyzed": 15,
            "traces_without_urls": 0,
            "total_zenrows_traces": 20,
        }

        result = self.formatter.format_zenrows_url_patterns_report(url_results)
        lines = result.strip().split("\n")

        # Find domain lines and file type lines
        domain_lines = [line for line in lines if line.startswith("domain,")]
        file_type_lines = [line for line in lines if line.startswith("file_type,")]

        # Domains should be in descending order by count
        assert "high.com,10" in domain_lines[0]  # Highest count first
        assert "medium.com,5" in domain_lines[1]  # Medium count second
        assert "low.com,1" in domain_lines[2]  # Lowest count last

        # File types should be in descending order by count
        assert "common,8" in file_type_lines[0]  # Higher count first
        assert "rare,2" in file_type_lines[1]  # Lower count second

    def test_format_zenrows_url_patterns_error_categories_sorted(self):
        """Test that error categories are sorted by frequency within each entry."""
        url_results = {
            "domains": {
                "example.com": {
                    "count": 10,
                    "error_categories": {
                        "rare_error": 1,
                        "common_error": 7,
                        "medium_error": 2,
                    },
                },
            },
            "file_types": {},
            "total_analyzed": 10,
            "traces_without_urls": 0,
        }

        result = self.formatter.format_zenrows_url_patterns_report(url_results)

        # Error categories should be sorted by count (descending) within the entry
        domain_line = [line for line in result.split("\n") if line.startswith("domain,")][0]
        categories_part = domain_line.split('"')[1]  # Extract the quoted categories part

        # Should be sorted: common_error(7), medium_error(2), rare_error(1)
        expected_order = "common_error(7);medium_error(2);rare_error(1)"
        assert categories_part == expected_order
