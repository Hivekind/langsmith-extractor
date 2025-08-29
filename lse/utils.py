"""Utility functions for progress indication and common operations."""

import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, List, Optional, TypeVar, Iterator

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

logger = logging.getLogger("lse.utils")

T = TypeVar('T')


class ProgressContext:
    """Context manager for progress indication with Rich."""
    
    def __init__(
        self, 
        description: str, 
        console: Optional[Console] = None,
        show_colors: bool = False
    ):
        """
        Initialize progress context.
        
        Args:
            description: Description of the operation
            console: Rich console instance (creates new if None)
            show_colors: Whether to show colors (disabled by default)
        """
        self.description = description
        self.show_colors = show_colors
        self.console = console or Console(
            force_terminal=False,
            color_system=None if not show_colors else "auto"
        )
        self.progress: Optional[Progress] = None

    def __enter__(self) -> 'ProgressContext':
        """Enter the progress context."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the progress context."""
        self.stop()

    def start(self) -> None:
        """Start the progress display."""
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="white", finished_style="white") if not self.show_colors else BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=False
        )
        self.progress.__enter__()

    def stop(self) -> None:
        """Stop the progress display."""
        if self.progress:
            self.progress.__exit__(None, None, None)
            self.progress = None

    def add_task(self, description: str, total: Optional[int] = None) -> int:
        """Add a task to the progress display."""
        if not self.progress:
            raise RuntimeError("Progress context not started")
        return self.progress.add_task(description, total=total)

    def update(
        self, 
        task_id: int, 
        advance: Optional[int] = None, 
        description: Optional[str] = None,
        **kwargs
    ) -> None:
        """Update a task in the progress display."""
        if not self.progress:
            raise RuntimeError("Progress context not started")
        self.progress.update(task_id, advance=advance, description=description, **kwargs)


@contextmanager
def create_spinner(
    description: str,
    spinner_style: str = "dots",
    console: Optional[Console] = None
) -> Iterator[Progress]:
    """
    Create a spinner for indeterminate operations.
    
    Args:
        description: Description of the operation
        spinner_style: Style of spinner (dots, arc, etc.)
        console: Rich console instance
        
    Yields:
        Progress instance configured as spinner
    """
    console = console or Console(force_terminal=False, color_system=None)
    
    with Progress(
        SpinnerColumn(spinner_style),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        progress.add_task(description, total=None)
        yield progress


@contextmanager
def create_progress_bar(
    description: str,
    total: Optional[int] = None,
    console: Optional[Console] = None
) -> Iterator[Progress]:
    """
    Create a progress bar for determinate operations.
    
    Args:
        description: Description of the operation
        total: Total number of items (if known)
        console: Rich console instance
        
    Yields:
        Progress instance configured as progress bar
    """
    console = console or Console(force_terminal=False, color_system=None)
    
    columns = [
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="white", finished_style="white"),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ]
    
    if total:
        columns.append(TimeRemainingColumn())
    
    with Progress(*columns, console=console, transient=False) as progress:
        yield progress


def with_progress(description: str, show_colors: bool = False):
    """
    Decorator to add progress indication to functions.
    
    Args:
        description: Description of the operation
        show_colors: Whether to show colors
        
    The decorated function can accept a progress_callback parameter
    which will be called with (current, total, description) arguments.
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Check if function wants progress callback
            import inspect
            sig = inspect.signature(func)
            wants_progress = 'progress_callback' in sig.parameters
            
            if wants_progress:
                progress_data = {'current': 0, 'total': 0, 'task_id': None}
                
                def progress_callback(current: int, total: int, desc: Optional[str] = None):
                    progress_data['current'] = current
                    progress_data['total'] = total
                    if progress_data['task_id'] is not None and progress_context.progress:
                        progress_context.progress.update(
                            progress_data['task_id'],
                            completed=current,
                            total=total,
                            description=desc or description
                        )
                
                with ProgressContext(description, show_colors=show_colors) as progress_context:
                    progress_data['task_id'] = progress_context.add_task(description, total=None)
                    kwargs['progress_callback'] = progress_callback
                    return func(*args, **kwargs)
            else:
                # No progress callback needed, just run with spinner
                with create_spinner(description) as spinner:
                    return func(*args, **kwargs)
        
        return wrapper
    return decorator


def batch_progress(
    items: List[T],
    processor: Callable[[T], Any],
    description: str = "Processing items",
    batch_size: int = 1,
    show_colors: bool = False
) -> List[Any]:
    """
    Process items in batches with progress indication.
    
    Args:
        items: List of items to process
        processor: Function to process each item
        description: Description for progress bar
        batch_size: Number of items to process in each batch
        show_colors: Whether to show colors
        
    Returns:
        List of processed results
        
    Raises:
        Exception: If processing fails on any item
    """
    results = []
    total_items = len(items)
    
    with ProgressContext(description, show_colors=show_colors) as progress:
        task_id = progress.add_task(f"{description} (0/{total_items})", total=total_items)
        
        for i in range(0, total_items, batch_size):
            batch = items[i:i + batch_size]
            batch_results = []
            
            for item in batch:
                try:
                    result = processor(item)
                    batch_results.append(result)
                except Exception as e:
                    logger.error(f"Error processing item {i + len(batch_results)}: {e}")
                    raise
                
                # Update progress
                completed = i + len(batch_results)
                progress.update(
                    task_id, 
                    completed=completed,
                    description=f"{description} ({completed}/{total_items})"
                )
            
            results.extend(batch_results)
            
            # Small delay to make progress visible for fast operations
            if batch_size > 1:
                time.sleep(0.01)
    
    return results


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_bytes(bytes_count: int) -> str:
    """
    Format byte count to human-readable string.
    
    Args:
        bytes_count: Number of bytes
        
    Returns:
        Formatted byte count string
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(bytes_count)
    
    for unit in units:
        if size < 1024.0:
            if unit == 'B':
                return f"{int(size)} {unit}"
            else:
                return f"{size:.1f} {unit}"
        size /= 1024.0
    
    return f"{size:.1f} PB"


def simple_progress_bar(
    current: int, 
    total: int, 
    width: int = 40, 
    show_percentage: bool = True
) -> str:
    """
    Create a simple text-based progress bar.
    
    Args:
        current: Current progress value
        total: Total progress value
        width: Width of the progress bar in characters
        show_percentage: Whether to show percentage
        
    Returns:
        Formatted progress bar string
    """
    if total <= 0:
        return "Progress: unknown"
    
    percentage = min(100, (current / total) * 100)
    filled_width = int((current / total) * width)
    
    bar = '█' * filled_width + '░' * (width - filled_width)
    
    if show_percentage:
        return f"[{bar}] {percentage:.1f}%"
    else:
        return f"[{bar}] {current}/{total}"


class OperationTimer:
    """Context manager for timing operations."""
    
    def __init__(self, description: str = "Operation"):
        """Initialize timer with description."""
        self.description = description
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def __enter__(self) -> 'OperationTimer':
        """Start timing."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log duration."""
        self.end_time = time.time()
        if self.start_time:
            duration = self.end_time - self.start_time
            logger.debug(f"{self.description} completed in {format_duration(duration)}")
    
    @property
    def elapsed(self) -> Optional[float]:
        """Get elapsed time in seconds."""
        if self.start_time:
            end = self.end_time or time.time()
            return end - self.start_time
        return None