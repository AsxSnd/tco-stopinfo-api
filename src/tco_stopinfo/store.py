from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .journey_context import merge_stop_list_payload, refresh_active_fs_context


# MQTT topic suffix -> state key on VehicleState
TOPIC_SUFFIXES = (
    "journey",
    "destination",
    "linkprogress",
    "stopinfo",
    "list/stops",
    "connections",
    "journeystate",
    "announcement",
    "list/announcements",
    "list/destinations",
    "sensors/stop_button",
    "sensors/door",
)


@dataclass
class VehicleState:
    vehicle_id: str
    topics: dict[str, Any] = field(default_factory=dict)
    stop_lists_by_ref: dict[str, dict[str, Any]] = field(default_factory=dict)
    stopinfo_by_ref: dict[str, dict[str, Any]] = field(default_factory=dict)
    stopinfo_updated_at: dict[str, float] = field(default_factory=dict)
    active_stop_list: dict[str, Any] = field(default_factory=dict)
    active_stopinfo: dict[str, Any] | None = None
    active_journey_ref: str | None = None
    updated_at: float = field(default_factory=time.time)
    version: int = 0

    def set_topic(self, suffix: str, payload: Any) -> bool:
        previous = self.topics.get(suffix)
        if previous == payload:
            return False
        self.topics[suffix] = payload
        self._record_journey_payload(suffix, payload)
        refresh_active_fs_context(self)
        self.updated_at = time.time()
        self.version += 1
        return True

    def _record_journey_payload(self, suffix: str, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        ref = payload.get("vehicleJourneyRef")
        if not ref:
            return
        ref_key = str(ref)
        if suffix == "list/stops" and payload.get("stops"):
            merged = merge_stop_list_payload(self.stop_lists_by_ref.get(ref_key), payload)
            self.stop_lists_by_ref[ref_key] = merged
            self.topics["list/stops"] = merged
        elif suffix == "stopinfo" and payload.get("callSequenceNumber") is not None:
            self.stopinfo_by_ref[ref_key] = payload
            self.stopinfo_updated_at[ref_key] = time.time()


@dataclass
class CachedResponse:
    body: bytes
    headers: dict[str, str]
    built_at: float
    state_version: int


class VehicleStore:
    """In-memory vehicle MQTT state and pre-built HTTP responses."""

    def __init__(self, vehicle_ttl_seconds: int = 7200) -> None:
        self._vehicles: dict[str, VehicleState] = {}
        self._responses: dict[tuple[str, str], CachedResponse] = {}
        self._fast_hits: dict[tuple[str, str], CachedResponse] = {}
        self._vehicle_ttl = vehicle_ttl_seconds

    def get_or_create(self, vehicle_id: str) -> VehicleState:
        state = self._vehicles.get(vehicle_id)
        if state is None:
            state = VehicleState(vehicle_id=vehicle_id)
            self._vehicles[vehicle_id] = state
        return state

    def update_topic(self, vehicle_id: str, suffix: str, payload: Any) -> bool:
        state = self.get_or_create(vehicle_id)
        return state.set_topic(suffix, payload)

    def get_state(self, vehicle_id: str) -> VehicleState | None:
        return self._vehicles.get(vehicle_id)

    def put_response(self, account: str, vehicle_id: str, cached: CachedResponse) -> None:
        key = (account.lower(), vehicle_id)
        self._responses[key] = cached
        self._fast_hits.pop(key, None)

    def get_response(
        self,
        account: str,
        vehicle_id: str,
        *,
        fast_response_seconds: int,
    ) -> CachedResponse | None:
        key = (account.lower(), vehicle_id)
        now = time.time()

        fast = self._fast_hits.get(key)
        if fast is not None and now - fast.built_at <= fast_response_seconds:
            return fast

        cached = self._responses.get(key)
        if cached is not None:
            self._fast_hits[key] = cached
        return cached

    def invalidate_vehicle(self, vehicle_id: str) -> None:
        keys = [key for key in self._responses if key[1] == vehicle_id]
        for key in keys:
            self._responses.pop(key, None)
            self._fast_hits.pop(key, None)

    def purge_stale(self) -> int:
        now = time.time()
        removed = 0
        stale_ids = [
            vid
            for vid, state in self._vehicles.items()
            if now - state.updated_at > self._vehicle_ttl
        ]
        for vid in stale_ids:
            self._vehicles.pop(vid, None)
            keys = [key for key in self._responses if key[1] == vid]
            for key in keys:
                self._responses.pop(key, None)
                self._fast_hits.pop(key, None)
            removed += 1
        return removed

    def stats(self) -> dict[str, object]:
        vehicle_ids = sorted(self._vehicles.keys())
        with_data = [
            vid for vid, state in self._vehicles.items() if state.topics
        ]
        cached_accounts = sorted({account for account, _vid in self._responses})
        return {
            "vehicles_in_memory": len(self._vehicles),
            "vehicles_with_mqtt_data": len(with_data),
            "cached_http_responses": len(self._responses),
            "vehicle_ids": vehicle_ids,
            "vehicles_with_data_ids": sorted(with_data),
            "cached_accounts": cached_accounts,
        }
