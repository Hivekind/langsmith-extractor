"""Tests for utility functions and progress indication."""

import time
from io import StringIO
from unittest.mock import patch

import pytest
from rich.console import Console

from lse.utils import (
    ProgressContext,
    create_spinner,
    create_progress_bar,
    with_progress,
    batch_progress,
    extract_domain_from_url,
    classify_file_type,
)


class TestProgressContext:
    """Test the ProgressContext class."""

    def test_progress_context_creation(self):
        """Test that ProgressContext can be created."""
        progress = ProgressContext(description="Test operation")
        assert progress.description == "Test operation"
        assert progress.console is not None
        assert not progress.show_colors  # Should default to no colors

    def test_progress_context_with_colors_disabled(self):
        """Test that colors are disabled by default."""
        progress = ProgressContext(description="Test", show_colors=False)
        assert not progress.show_colors
        assert progress.console._force_terminal is False

    def test_progress_context_as_context_manager(self):
        """Test using ProgressContext as context manager."""
        with ProgressContext(description="Test operation") as progress:
            assert progress.progress is not None
            task_id = progress.add_task("Subtask", total=10)
            assert isinstance(task_id, int)
            progress.update(task_id, advance=5)

    def test_progress_context_manual_start_stop(self):
        """Test manual start and stop of progress context."""
        progress = ProgressContext(description="Test operation")
        progress.start()
        assert progress.progress is not None

        task_id = progress.add_task("Test task", total=5)
        progress.update(task_id, advance=2)

        progress.stop()
        # After stop, progress should be None
        assert progress.progress is None

    def test_progress_context_console_output(self):
        """Test that progress context captures console output."""
        console = Console(file=StringIO(), force_terminal=False)
        progress = ProgressContext(description="Test", console=console)

        with progress:
            task_id = progress.add_task("Task", total=1)
            progress.update(task_id, advance=1, description="Updated task")

    def test_progress_context_multiple_tasks(self):
        """Test handling multiple tasks in progress context."""
        with ProgressContext(description="Multi-task test") as progress:
            task1 = progress.add_task("Task 1", total=10)
            task2 = progress.add_task("Task 2", total=20)

            progress.update(task1, advance=5)
            progress.update(task2, advance=10)

            # Should not raise errors
            assert isinstance(task1, int)
            assert isinstance(task2, int)


class TestSpinnerUtilities:
    """Test spinner utility functions."""

    def test_create_spinner_basic(self):
        """Test creating a basic spinner."""
        # Test that create_spinner returns a context manager
        spinner = create_spinner("Loading...")
        assert hasattr(spinner, "__enter__")
        assert hasattr(spinner, "__exit__")

    def test_create_spinner_with_custom_style(self):
        """Test creating spinner with custom style."""
        with patch("lse.utils.Progress"):
            spinner = create_spinner("Custom loading...", spinner_style="dots")
            assert spinner is not None

    def test_spinner_context_manager(self):
        """Test using spinner as context manager."""
        with create_spinner("Test spinner"):
            # Should not raise errors
            time.sleep(0.1)  # Brief delay to simulate work

    def test_spinner_no_colors(self):
        """Test that spinner respects no-color setting."""
        console = Console(file=StringIO(), force_terminal=False)

        with create_spinner("Test", console=console) as spinner:
            # Should work without colors
            assert spinner is not None


class TestProgressBarUtilities:
    """Test progress bar utility functions."""

    def test_create_progress_bar_basic(self):
        """Test creating a basic progress bar."""
        with patch("lse.utils.Progress"):
            progress_bar = create_progress_bar("Processing files")
            assert progress_bar is not None

    def test_create_progress_bar_with_total(self):
        """Test creating progress bar with known total."""
        with create_progress_bar("Processing", total=100) as progress:
            task_id = progress.add_task("Test", total=100)
            progress.update(task_id, advance=25)
            progress.update(task_id, advance=25)
            # Should complete 50% without errors

    def test_progress_bar_no_colors(self):
        """Test progress bar without colors."""
        console = Console(file=StringIO(), force_terminal=False, color_system=None)

        with create_progress_bar("Test", console=console) as progress:
            task_id = progress.add_task("Task", total=10)
            for i in range(10):
                progress.update(task_id, advance=1)
                time.sleep(0.01)  # Brief delay


class TestProgressDecorators:
    """Test progress indication decorators and wrappers."""

    def test_with_progress_decorator(self):
        """Test the with_progress decorator."""

        @with_progress("Processing items")
        def sample_function(items, progress_callback=None):
            results = []
            for i, item in enumerate(items):
                if progress_callback:
                    progress_callback(i + 1, len(items), f"Processing {item}")
                results.append(f"processed_{item}")
                time.sleep(0.01)  # Simulate work
            return results

        items = ["a", "b", "c"]
        result = sample_function(items)
        assert result == ["processed_a", "processed_b", "processed_c"]

    def test_with_progress_no_callback(self):
        """Test with_progress decorator when no progress callback used."""

        @with_progress("Simple operation")
        def simple_function():
            return "done"

        result = simple_function()
        assert result == "done"

    def test_batch_progress_function(self):
        """Test batch_progress utility function."""
        items = list(range(10))

        def process_item(item):
            time.sleep(0.01)  # Simulate work
            return item * 2

        results = batch_progress(
            items, process_item, description="Processing numbers", batch_size=3
        )

        expected = [i * 2 for i in range(10)]
        assert results == expected

    def test_batch_progress_with_error_handling(self):
        """Test batch_progress with error in processing."""
        items = [1, 2, "invalid", 4]

        def process_item(item):
            if isinstance(item, str):
                raise ValueError(f"Cannot process {item}")
            return item * 2

        # Should handle errors gracefully and continue
        with pytest.raises(ValueError):
            batch_progress(items, process_item, "Processing with errors")


class TestProgressIntegration:
    """Test integration of progress utilities."""

    def test_nested_progress_contexts(self):
        """Test nested progress contexts don't interfere."""
        with ProgressContext("Outer operation") as outer:
            outer_task = outer.add_task("Outer task", total=2)

            with ProgressContext("Inner operation") as inner:
                inner_task = inner.add_task("Inner task", total=3)
                inner.update(inner_task, advance=3)

            outer.update(outer_task, advance=2)

    def test_progress_with_logging(self):
        """Test that progress works alongside logging."""
        import logging

        # Set up a logger
        logger = logging.getLogger("test_progress")

        with ProgressContext("Logged operation") as progress:
            task_id = progress.add_task("Task with logging", total=2)
            logger.info("Starting operation")
            progress.update(task_id, advance=1)
            logger.info("Halfway done")
            progress.update(task_id, advance=1)
            logger.info("Operation complete")

    def test_progress_error_handling(self):
        """Test progress indication with error scenarios."""
        with ProgressContext("Error test") as progress:
            task_id = progress.add_task("Failing task", total=5)

            try:
                progress.update(task_id, advance=2)
                raise Exception("Simulated error")
            except Exception:
                # Progress should still be usable after errors
                progress.update(task_id, description="Task failed")

    def test_progress_performance(self):
        """Test that progress indication doesn't significantly slow operations."""
        import time

        # Test without progress
        start_time = time.time()
        for i in range(100):
            time.sleep(0.001)  # Simulate small work unit
        no_progress_time = time.time() - start_time

        # Test with progress
        start_time = time.time()
        with ProgressContext("Performance test") as progress:
            task_id = progress.add_task("Performance task", total=100)
            for i in range(100):
                progress.update(task_id, advance=1)
                time.sleep(0.001)  # Simulate small work unit
        with_progress_time = time.time() - start_time

        # Progress overhead should be reasonable (less than 50% slower)
        assert with_progress_time < no_progress_time * 1.5


class TestURLDomainExtraction:
    """Test URL domain extraction utilities."""

    def test_extract_domain_from_valid_url(self):
        """Test domain extraction from valid URLs."""
        assert extract_domain_from_url("https://example.com/path") == "example.com"
        assert extract_domain_from_url("http://subdomain.example.org") == "subdomain.example.org"
        assert extract_domain_from_url("https://www.google.com/search?q=test") == "www.google.com"

    def test_extract_domain_with_port(self):
        """Test domain extraction from URLs with ports."""
        assert extract_domain_from_url("https://localhost:8080/api") == "localhost:8080"
        assert extract_domain_from_url("http://example.com:3000/path") == "example.com:3000"

    def test_extract_domain_without_protocol(self):
        """Test domain extraction from URLs without protocol."""
        assert extract_domain_from_url("//example.com/path") == "example.com"
        assert extract_domain_from_url("example.com/path") == "example.com"

    def test_extract_domain_from_malformed_urls(self):
        """Test domain extraction from malformed URLs returns None."""
        assert extract_domain_from_url("") is None
        assert extract_domain_from_url("not-a-url") is None
        assert extract_domain_from_url("://missing-scheme") is None
        assert extract_domain_from_url("http://") is None

    def test_extract_domain_from_none_input(self):
        """Test domain extraction handles None input gracefully."""
        assert extract_domain_from_url(None) is None

    def test_extract_domain_with_query_parameters(self):
        """Test domain extraction ignores query parameters."""
        url = "https://example.com/path?param1=value1&param2=value2"
        assert extract_domain_from_url(url) == "example.com"

    def test_extract_domain_with_fragments(self):
        """Test domain extraction ignores URL fragments."""
        url = "https://example.com/path#section1"
        assert extract_domain_from_url(url) == "example.com"

    def test_extract_domain_from_ip_addresses(self):
        """Test domain extraction from IP addresses."""
        assert extract_domain_from_url("https://192.168.1.1/path") == "192.168.1.1"
        assert extract_domain_from_url("http://127.0.0.1:8000") == "127.0.0.1:8000"

    def test_extract_domain_case_sensitivity(self):
        """Test domain extraction preserves case."""
        assert extract_domain_from_url("https://Example.COM/path") == "Example.COM"


class TestFileTypeClassification:
    """Test file type classification utilities."""

    def test_classify_pdf_files(self):
        """Test classification of PDF files."""
        assert classify_file_type("document.pdf") == "pdf"
        assert classify_file_type("https://example.com/report.pdf") == "pdf"
        assert classify_file_type("DOCUMENT.PDF") == "pdf"  # Case insensitive

    def test_classify_image_files(self):
        """Test classification of image files."""
        assert classify_file_type("photo.jpg") == "image"
        assert classify_file_type("image.png") == "image"
        assert classify_file_type("graphic.gif") == "image"
        assert classify_file_type("picture.jpeg") == "image"
        assert classify_file_type("icon.svg") == "image"

    def test_classify_api_endpoints(self):
        """Test classification of API endpoints."""
        assert classify_file_type("https://api.example.com/data") == "api"
        assert classify_file_type("https://example.com/api/users") == "api"
        assert classify_file_type("data.json") == "api"
        assert classify_file_type("config.xml") == "api"

    def test_classify_html_pages(self):
        """Test classification of HTML pages."""
        assert classify_file_type("page.html") == "html"
        assert classify_file_type("index.htm") == "html"
        assert classify_file_type("https://example.com/") == "html"  # No extension
        assert classify_file_type("https://example.com/page") == "html"  # No extension

    def test_classify_other_file_types(self):
        """Test classification of other file types."""
        assert classify_file_type("document.txt") == "other"
        assert classify_file_type("archive.zip") == "other"
        assert classify_file_type("video.mp4") == "other"
        assert classify_file_type("data.csv") == "other"

    def test_classify_file_type_with_query_parameters(self):
        """Test file type classification ignores query parameters."""
        url = "https://example.com/document.pdf?download=true"
        assert classify_file_type(url) == "pdf"

    def test_classify_file_type_with_fragments(self):
        """Test file type classification ignores URL fragments."""
        url = "https://example.com/image.png#section"
        assert classify_file_type(url) == "image"

    def test_classify_file_type_from_none_input(self):
        """Test file type classification handles None input."""
        assert classify_file_type(None) == "other"

    def test_classify_file_type_from_empty_input(self):
        """Test file type classification handles empty input."""
        assert classify_file_type("") == "other"

    def test_classify_file_type_case_insensitive(self):
        """Test file type classification is case insensitive."""
        assert classify_file_type("DOCUMENT.PDF") == "pdf"
        assert classify_file_type("Image.PNG") == "image"
        assert classify_file_type("Data.JSON") == "api"

    def test_classify_file_type_multiple_extensions(self):
        """Test file type classification with multiple extensions."""
        assert classify_file_type("archive.tar.gz") == "other"
        assert classify_file_type("backup.pdf.bak") == "other"  # Takes last extension

    def test_classify_api_endpoints_comprehensive(self):
        """Test comprehensive API endpoint detection."""
        api_urls = [
            "https://example.com/api/v1/users",
            "https://api.github.com/repos",
            "https://example.com/rest/data",
            "https://example.com/graphql",
            "https://example.com/data.json",
            "https://example.com/config.xml",
            "https://example.com/feed.rss",
        ]
        for url in api_urls:
            assert classify_file_type(url) == "api", f"Failed for URL: {url}"


class TestURLUtilitiesIntegration:
    """Test integration of URL parsing utilities."""

    def test_domain_and_file_type_extraction_together(self):
        """Test extracting both domain and file type from same URL."""
        url = "https://example.com/document.pdf"
        domain = extract_domain_from_url(url)
        file_type = classify_file_type(url)

        assert domain == "example.com"
        assert file_type == "pdf"

    def test_batch_url_processing(self):
        """Test processing multiple URLs efficiently."""
        urls = [
            "https://example.com/report.pdf",
            "https://api.example.com/data",
            "https://example.com/image.png",
            "https://example.com/page.html",
            "https://other.com/unknown.xyz",
        ]

        results = []
        for url in urls:
            results.append(
                {
                    "url": url,
                    "domain": extract_domain_from_url(url),
                    "file_type": classify_file_type(url),
                }
            )

        assert len(results) == 5
        assert results[0]["domain"] == "example.com"
        assert results[0]["file_type"] == "pdf"
        assert results[1]["file_type"] == "api"

    def test_error_handling_resilience(self):
        """Test that utilities handle errors gracefully in batch processing."""
        problematic_urls = [
            None,
            "",
            "invalid-url",
            "https://example.com/valid.pdf",
            "://malformed",
        ]

        # Should not raise exceptions
        for url in problematic_urls:
            domain = extract_domain_from_url(url)
            file_type = classify_file_type(url)

            # Valid URL should work
            if url == "https://example.com/valid.pdf":
                assert domain == "example.com"
                assert file_type == "pdf"
            # Invalid URLs should return None or fallback values
            elif url in [None, "", "invalid-url", "://malformed"]:
                assert domain is None
                assert file_type == "other"

    def test_real_world_url_samples(self):
        """Test with realistic URL patterns from web scraping."""
        real_world_urls = [
            "https://www.sec.gov/Archives/edgar/data/1234567/000119312521123456/d123456d10k.pdf",
            "https://api.github.com/repos/owner/repo/releases/latest",
            "https://images.unsplash.com/photo-1234567890?ixlib=rb-4.0.3",
            "https://example.com/",
            "https://cdn.example.com/assets/logo.svg",
            "https://docs.google.com/spreadsheets/d/abc123/export?format=pdf",
        ]

        expected_results = [
            ("www.sec.gov", "pdf"),
            ("api.github.com", "api"),
            ("images.unsplash.com", "image"),
            ("example.com", "html"),
            ("cdn.example.com", "image"),
            ("docs.google.com", "pdf"),  # Query param should be detected
        ]

        for url, (expected_domain, expected_file_type) in zip(real_world_urls, expected_results):
            domain = extract_domain_from_url(url)
            file_type = classify_file_type(url)

            assert domain == expected_domain, (
                f"Domain mismatch for {url}: got {domain}, expected {expected_domain}"
            )
            assert file_type == expected_file_type, (
                f"File type mismatch for {url}: got {file_type}, expected {expected_file_type}"
            )
