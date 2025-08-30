"""Timezone utilities for LangSmith operations."""

from datetime import datetime, timezone, timedelta
from typing import Union

# LangSmith account timezone: UTC+08:00
LANGSMITH_TIMEZONE = timezone(timedelta(hours=8))


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime.

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        Datetime object at midnight
    """
    return datetime.strptime(date_str, "%Y-%m-%d")


def to_langsmith_timezone(dt: datetime) -> datetime:
    """Convert datetime to LangSmith timezone (UTC+08:00).

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


def to_utc(dt: datetime) -> datetime:
    """Convert datetime from LangSmith timezone to UTC.

    Args:
        dt: Datetime in LangSmith timezone

    Returns:
        Datetime in UTC
    """
    if dt.tzinfo is None:
        # Assume naive datetime is in LangSmith timezone
        dt = dt.replace(tzinfo=LANGSMITH_TIMEZONE)

    return dt.astimezone(timezone.utc)


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
        # No timezone info - assume LangSmith timezone
        dt = datetime.fromisoformat(dt_str)
        dt = dt.replace(tzinfo=LANGSMITH_TIMEZONE)

    # Convert to UTC for API
    return to_utc(dt)


def make_date_range_inclusive(
    start_date: Union[str, datetime], end_date: Union[str, datetime]
) -> tuple[datetime, datetime]:
    """Create inclusive date range in LangSmith timezone.

    Args:
        start_date: Start date (YYYY-MM-DD format or datetime)
        end_date: End date (YYYY-MM-DD format or datetime)

    Returns:
        Tuple of (start_datetime, end_datetime) in UTC for API calls
    """
    # Parse start date
    if isinstance(start_date, str):
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        start_dt = start_dt.replace(tzinfo=LANGSMITH_TIMEZONE)
    else:
        start_dt = to_langsmith_timezone(start_date)

    # Parse end date and make it inclusive (end of day)
    if isinstance(end_date, str):
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        end_dt = end_dt.replace(tzinfo=LANGSMITH_TIMEZONE)
    else:
        end_dt = to_langsmith_timezone(end_date)
        if end_dt.hour == 0 and end_dt.minute == 0 and end_dt.second == 0:
            # Assume this is a date-only datetime, make it end of day
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Convert to UTC for API calls
    return to_utc(start_dt), to_utc(end_dt)


def format_for_display(dt: datetime) -> str:
    """Format datetime for user display in LangSmith timezone.

    Args:
        dt: Datetime to format

    Returns:
        Formatted datetime string
    """
    display_dt = to_langsmith_timezone(dt)
    return display_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
