from __future__ import annotations

import time
from unittest.mock import patch

from tco_stopinfo.app import ApplicationState
from tco_stopinfo.config import AppConfig, CacheConfig, load_config


def _app_with_cooldown(cooldown: int = 60) -> ApplicationState:
    cfg = load_config("config.example.yaml")
    cfg.cache = CacheConfig(
        fast_response_seconds=10,
        mqtt_fetch_cooldown_seconds=cooldown,
        mqtt_fetch_connect_seconds=0.01,
        mqtt_fetch_wait_seconds=0.01,
    )
    return ApplicationState(cfg)


def test_no_fetch_when_vehicle_already_has_mqtt_topics() -> None:
    app = _app_with_cooldown()
    state = app.store.get_or_create("9999")
    state.set_topic("journey", {"lineNumber": "10"})

    with patch("tco_stopinfo.app.fetch_vehicle_topics") as fetch:
        app.ensure_vehicle_stop_context("9999")
        fetch.assert_not_called()


def test_fetch_cooldown_after_empty_read() -> None:
    app = _app_with_cooldown(cooldown=60)
    with patch("tco_stopinfo.app.fetch_vehicle_topics", return_value={}) as fetch:
        app.ensure_vehicle_stop_context("8888")
        assert fetch.call_count == 1

        app.ensure_vehicle_stop_context("8888")
        fetch.assert_called_once()


def test_get_stopinfo_response_cached_empty_is_fast() -> None:
    app = _app_with_cooldown()
    with patch("tco_stopinfo.app.fetch_vehicle_topics", return_value={}) as fetch:
        first = app.get_stopinfo_response("vilnius", "7777")
        second = app.get_stopinfo_response("vilnius", "7777")

    assert first.body == second.body
    assert fetch.call_count == 1
    assert app.store.get_response("vilnius", "7777", fast_response_seconds=0) is not None


def test_get_stopinfo_response_skips_rebuild_when_version_unchanged() -> None:
    app = _app_with_cooldown()
    state = app.store.get_or_create("6666")
    state.set_topic("journey", {"lineNumber": "10"})
    state.set_topic(
        "list/stops",
        {"stops": [{"number": 1, "name": "Stop A"}], "vehicleJourneyRef": "T1"},
    )
    state.set_topic("stopinfo", {"callSequenceNumber": 1, "type": "ARRIVAL"})

    with patch.object(app, "rebuild_vehicle") as rebuild:
        first = app.get_stopinfo_response("vilnius", "6666")
        second = app.get_stopinfo_response("vilnius", "6666")

    assert first.body == second.body
    assert rebuild.call_count == 1
