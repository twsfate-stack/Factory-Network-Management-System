from datetime import datetime, timezone
from zoneinfo import ZoneInfo

THAILAND_TZ = ZoneInfo("Asia/Bangkok")


def utcnow():
    return datetime.now(timezone.utc)


def iso_thailand(value):
    if value is None:
        return None
    # SQLite returns naive datetimes; persisted values represent UTC.
    aware = value.replace(tzinfo=value.tzinfo or timezone.utc)
    return aware.astimezone(THAILAND_TZ).isoformat()
