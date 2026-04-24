from datetime import datetime


def format_utc_offset(ts: datetime) -> str:
    """
    Returns timezone as 'UTC+02:00', 'UTC-05:00', or 'naive'.
    """
    if ts.tzinfo is None:
        return "naive"
    offset = ts.utcoffset()
    if offset is None:
        return "naive"
    total_min = int(offset.total_seconds() // 60)
    sign = "+" if total_min >= 0 else "-"
    hours, minutes = divmod(abs(total_min), 60)
    return f"UTC{sign}{hours:02d}:{minutes:02d}"