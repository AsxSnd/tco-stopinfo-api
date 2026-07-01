from zoneinfo import ZoneInfo

from tco_stopinfo.time_format import format_hhmm_local, get_timezone


def test_format_hhmm_local_vilnius_summer() -> None:
    tz = get_timezone("Europe/Vilnius")
    # 2026-07-01 11:18 UTC = 14:18 EEST (UTC+3)
    assert format_hhmm_local("2026-07-01T11:18:00Z", tz) == "14:18"


def test_format_hhmm_local_invalid_returns_none() -> None:
    tz = ZoneInfo("UTC")
    assert format_hhmm_local(None, tz) is None
    assert format_hhmm_local("not-a-date", tz) is None
