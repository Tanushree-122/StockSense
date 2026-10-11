"""Time helpers. The database stores UTC; people see India Standard Time (IST)."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def now_utc():
    return datetime.now(timezone.utc)


def to_ist(value):
    """Convert a datetime to IST. Naive values (SQLite) are treated as UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(IST)


def ist_date(value):
    """The calendar date in IST for a datetime."""
    converted = to_ist(value)
    return converted.date() if converted else None


def ist_today():
    return ist_date(now_utc())
