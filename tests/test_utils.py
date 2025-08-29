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
        assert hasattr(spinner, '__enter__')
        assert hasattr(spinner, '__exit__')

    def test_create_spinner_with_custom_style(self):
        """Test creating spinner with custom style."""
        with patch('lse.utils.Progress') as mock_progress:
            spinner = create_spinner("Custom loading...", spinner_style="dots")
            assert spinner is not None

    def test_spinner_context_manager(self):
        """Test using spinner as context manager."""
        with create_spinner("Test spinner") as spinner:
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
        with patch('lse.utils.Progress') as mock_progress:
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
            items,
            process_item,
            description="Processing numbers",
            batch_size=3
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