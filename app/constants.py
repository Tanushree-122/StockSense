"""Shared constants. Recommendation settings are used from Day 8."""

MOVEMENT_TYPES = ("OPENING", "STOCK_IN", "SALE", "ADJUSTMENT", "SALE_VOID")
ADJUSTMENT_REASONS = (
    "DAMAGED",
    "LOST_THEFT",
    "COUNT_CORRECTION",
    "RETURNED_TO_SUPPLIER",
    "OTHER",
)
SALE_STATUSES = ("COMPLETED", "VOIDED")
ALERT_TYPES = ("LOW_STOCK", "OUT_OF_STOCK")
ALERT_STATUSES = ("OPEN", "RESOLVED")
EMAIL_STATUSES = ("NOT_SENT", "SENT", "FAILED", "SKIPPED")

PAGE_SIZE = 15

# Recommendation rules (Day 8)
DEMAND_WINDOW_DAYS = 28
SAFETY_DAYS = 2
TARGET_COVER_DAYS = 14
DEFAULT_LEAD_TIME_DAYS = 3
OVERSTOCK_COVER_DAYS = 60


def sql_in(column, values):
    """Build a SQL text like: status IN ('A','B') for CHECK constraints."""
    quoted = ",".join("'{}'".format(v) for v in values)
    return "{} IN ({})".format(column, quoted)
