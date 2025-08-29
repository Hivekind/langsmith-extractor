"""Tests for output formatting functionality."""

from lse.formatters import ReportFormatter, format_csv_report, format_summary_stats


class TestCSVFormatting:
    """Test CSV output formatting functionality."""

    def test_format_csv_report_basic(self):
        """Test basic CSV report formatting."""
        analysis_data = {
            "2025-08-29": {"total_traces": 10, "zenrows_errors": 2, "error_rate": 20.0},
            "2025-08-30": {"total_traces": 5, "zenrows_errors": 0, "error_rate": 0.0},
        }

        result = format_csv_report(analysis_data)

        lines = result.strip().split("\n")
        assert lines[0] == "Date,Total Traces,Zenrows Errors,Error Rate"
        assert lines[1] == "2025-08-29,10,2,20.0%"
        assert lines[2] == "2025-08-30,5,0,0.0%"

    def test_format_csv_report_sorted_dates(self):
        """Test that CSV output is sorted by date."""
        analysis_data = {
            "2025-08-30": {"total_traces": 5, "zenrows_errors": 0, "error_rate": 0.0},
            "2025-08-28": {"total_traces": 8, "zenrows_errors": 1, "error_rate": 12.5},
            "2025-08-29": {"total_traces": 10, "zenrows_errors": 2, "error_rate": 20.0},
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
                "error_rate": 33.333333,  # Should be formatted to 33.3%
            }
        }

        result = format_csv_report(analysis_data)

        assert "33.3%" in result


class TestSummaryStatistics:
    """Test summary statistics calculation."""

    def test_format_summary_stats_basic(self):
        """Test basic summary statistics calculation."""
        analysis_data = {
            "2025-08-28": {"total_traces": 10, "zenrows_errors": 1, "error_rate": 10.0},
            "2025-08-29": {"total_traces": 20, "zenrows_errors": 4, "error_rate": 20.0},
            "2025-08-30": {"total_traces": 5, "zenrows_errors": 0, "error_rate": 0.0},
        }

        stats = format_summary_stats(analysis_data)

        assert stats["total_days"] == 3
        assert stats["total_traces"] == 35
        assert stats["total_zenrows_errors"] == 5
        assert stats["overall_error_rate"] == 14.3  # 5/35 * 100 = 14.285...
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
        analysis_data = {
            "2025-08-29": {"total_traces": 10, "zenrows_errors": 2, "error_rate": 20.0}
        }

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
        analysis_data = {
            "2025-08-29": {"total_traces": 10, "zenrows_errors": 2, "error_rate": 20.0}
        }

        result = self.formatter.format_zenrows_report(analysis_data)

        assert "Date,Total Traces,Zenrows Errors,Error Rate" in result
        assert "2025-08-29,10,2,20.0%" in result

    def test_format_zenrows_report_empty(self):
        """Test zenrows report formatting with empty data."""
        result = self.formatter.format_zenrows_report({})

        assert result == "Date,Total Traces,Zenrows Errors,Error Rate\n"

    def test_format_summary(self):
        """Test human-readable summary formatting."""
        analysis_data = {
            "2025-08-28": {"total_traces": 10, "zenrows_errors": 1, "error_rate": 10.0},
            "2025-08-29": {"total_traces": 20, "zenrows_errors": 4, "error_rate": 20.0},
        }

        result = self.formatter.format_summary(analysis_data)

        assert "=== Zenrows Error Rate Summary ===" in result
        assert "2 day(s)" in result
        assert "Total traces analyzed: 30" in result
        assert "Total zenrows errors: 5" in result
        assert "Overall error rate: 16.7%" in result
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
            "2025-08-26": {"total_traces": 32, "zenrows_errors": 3, "error_rate": 9.4},
            "2025-08-27": {"total_traces": 28, "zenrows_errors": 7, "error_rate": 25.0},
            "2025-08-28": {"total_traces": 41, "zenrows_errors": 2, "error_rate": 4.9},
            "2025-08-29": {"total_traces": 19, "zenrows_errors": 1, "error_rate": 5.3},
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
        assert "2025-08-27,28,7,25.0%" in csv_output
        assert "2025-08-25,15,0,0.0%" in csv_output

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
