"""Date and time utilities."""

import datetime
from zoneinfo import ZoneInfo


def get_current_date_time() -> str:
    """Get the current date and time in UTC as an ISO string."""
    return datetime.utcnow().isoformat() + "Z"
