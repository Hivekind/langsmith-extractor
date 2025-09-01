"""Timezone utilities for UTC-based operations."""

from datetime import datetime, timezone, timedelta
from typing import Union

# Default timezone for all operations: UTC
DEFAULT_TIMEZONE = timezone.utc

# Legacy timezone (kept for backward compatibility)
LANGSMITH_TIMEZONE = timezone(timedelta(hours=8))


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime.

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        Datetime object at midnight
    """
    return datetime.strptime(date_str, "%Y-%m-%d")


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC.

    Args:
        dt: Datetime to convert

    Returns:
        Datetime in UTC timezone
    """
    if dt.tzinfo is None:
        # Assume naive datetime is already in UTC
        return dt.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC
        return dt.astimezone(timezone.utc)


def to_langsmith_timezone(dt: datetime) -> datetime:
    """Convert datetime to LangSmith timezone (UTC+08:00).

    DEPRECATED: Use to_utc() instead. Kept for backward compatibility.

    Args:
        dt: Datetime to convert

    Returns:
        Datetime in LangSmith timezone
    """
    if dt.tzinfo is None:
        # Assume naive datetime is already in LangSmith timezone
        return dt.replace(tzinfo=LANGSMITH_TIMEZONE)
    else:
        # Convert to LangSmith timezone
        return dt.astimezone(LANGSMITH_TIMEZONE)


def parse_datetime_for_api(dt_str: str) -> datetime:
    """Parse datetime string and convert to UTC for API calls.

    Args:
        dt_str: Datetime string in ISO format

    Returns:
        Datetime in UTC timezone for API operations
    """
    # Parse the datetime string
    if "Z" in dt_str:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    elif "+" in dt_str or dt_str.count("-") > 2:  # Has timezone info
        dt = datetime.fromisoformat(dt_str)
    else:
        # No timezone info - assume UTC
        dt = datetime.fromisoformat(dt_str)
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert to UTC for API
    return to_utc(dt)


def make_date_range_inclusive(
    start_date: Union[str, datetime], end_date: Union[str, datetime]
) -> tuple[datetime, datetime]:
    """Create inclusive date range in UTC timezone.

    Args:
        start_date: Start date (YYYY-MM-DD format or datetime)
        end_date: End date (YYYY-MM-DD format or datetime)

    Returns:
        Tuple of (start_datetime, end_datetime) in UTC for API calls
    """
    # Parse start date
    if isinstance(start_date, str):
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    else:
        start_dt = to_utc(start_date)

    # Parse end date and make it inclusive (end of day)
    if isinstance(end_date, str):
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        end_dt = end_dt.replace(tzinfo=timezone.utc)
    else:
        end_dt = to_utc(end_date)
        if end_dt.hour == 0 and end_dt.minute == 0 and end_dt.second == 0:
            # Assume this is a date-only datetime, make it end of day
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Return UTC datetimes for API calls
    return start_dt, end_dt


def format_for_display(dt: datetime) -> str:
    """Format datetime for user display in UTC timezone.

    Args:
        dt: Datetime to format

    Returns:
        Formatted datetime string in UTC
    """
    display_dt = to_utc(dt)
    return display_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
