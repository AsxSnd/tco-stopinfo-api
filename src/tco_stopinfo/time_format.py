from __future__ import annotations

from datetime import datetime, timezone
from typing import Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

TzInfo = Union[ZoneInfo, timezone]


def get_timezone(name: str) -> TzInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name.upper() in ("UTC", "ETC/UTC", "GMT"):
            return ZoneInfo("UTC")
        try:
            return ZoneInfo("UTC")
        except ZoneInfoNotFoundError:
            # Windows without tzdata: fixed offset fallback (no DST).
            return timezone.utc  # type: ignore[return-value]


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def format_hhmm_local(iso_time: str | None, tz: TzInfo) -> str | None:
    """Format an ISO-8601 UTC timestamp as local HH:MM."""
    target = parse_iso_datetime(iso_time)
    if target is None:
        return None
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    return target.astimezone(tz).strftime("%H:%M")
