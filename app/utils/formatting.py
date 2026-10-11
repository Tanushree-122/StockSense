"""Template filters: rupees with Indian digit grouping, and IST date display."""
from decimal import ROUND_HALF_UP, Decimal

from app.utils.dates import to_ist


def _indian_group(digits):
    if len(digits) <= 3:
        return digits
    head, tail = digits[:-3], digits[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


def rupees(value, decimals=2):
    """Format a number as rupees, for example 125000 -> ₹1,25,000.00"""
    if value is None:
        value = 0
    amount = Decimal(str(value))
    places = Decimal(1).scaleb(-decimals)
    amount = amount.quantize(places, rounding=ROUND_HALF_UP)
    sign = "-" if amount < 0 else ""
    whole, _, fraction = "{:f}".format(abs(amount)).partition(".")
    text = sign + "₹" + _indian_group(whole)
    if decimals > 0:
        text += "." + fraction.ljust(decimals, "0")
    return text


def ist(value, fmt="%d %b %Y, %I:%M %p"):
    """Show a datetime in IST."""
    converted = to_ist(value)
    return converted.strftime(fmt) if converted else ""
