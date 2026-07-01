from __future__ import annotations

import time
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .store import VehicleState


def journey_refs_match(left: str | None, right: str | None) -> bool:
    """True when two vehicleJourneyRef values refer to the same journey."""
    if not left or not right:
        return True
    a = str(left)
    b = str(right)
    if a == b:
        return True
    return a in b or b in a


def merge_stop_list_payload(
    existing: dict[str, Any] | None,
    new: dict[str, Any],
) -> dict[str, Any]:
    """Merge stop list updates by call sequence number.

    Vehicles may publish a full list/stops once, then shorter partial updates.
    Keep the superset so FS can always show max_following_stops rows.
    """
    new_stops = new.get("stops") or []
    if not new_stops:
        return existing or new

    if not existing or not existing.get("stops"):
        return new

    old_ref = existing.get("vehicleJourneyRef")
    new_ref = new.get("vehicleJourneyRef")
    if old_ref and new_ref and not journey_refs_match(old_ref, new_ref):
        return new

    by_number: dict[int, dict[str, Any]] = {}
    for stop in existing.get("stops") or []:
        number = stop.get("number")
        if number is not None:
            by_number[int(number)] = stop
    for stop in new_stops:
        number = stop.get("number")
        if number is not None:
            by_number[int(number)] = stop

    return {
        "vehicleJourneyRef": new_ref or old_ref,
        "stops": [by_number[n] for n in sorted(by_number)],
    }


def refresh_active_fs_context(state: VehicleState) -> None:
    stop_list, stopinfo, active_ref = resolve_journey_stop_context(state)
    state.active_stop_list = stop_list
    state.active_stopinfo = stopinfo
    state.active_journey_ref = active_ref


def resolve_journey_stop_context(
    state: VehicleState,
    *,
    stopinfo_ttl_seconds: float = 30,
) -> tuple[dict[str, Any], dict[str, Any] | None, str | None]:
    """Return (stop_list, stopinfo, active_journey_ref) for FS building."""
    journey = state.topics.get("journey") or {}
    active_ref = journey.get("vehicleJourneyRef")

    stop_list = _pick_stop_list(state, active_ref)
    if stop_list:
        list_ref = stop_list.get("vehicleJourneyRef")
        if active_ref is None:
            active_ref = list_ref
        elif list_ref and not journey_refs_match(active_ref, list_ref):
            stop_list = _pick_stop_list(state, list_ref)
            active_ref = list_ref

    stopinfo = _pick_stopinfo(
        state,
        match_ref=(stop_list or {}).get("vehicleJourneyRef") or active_ref,
        stopinfo_ttl_seconds=stopinfo_ttl_seconds,
        has_stop_list=bool((stop_list or {}).get("stops")),
    )

    if active_ref is None:
        active_ref = (stop_list or {}).get("vehicleJourneyRef") or (stopinfo or {}).get(
            "vehicleJourneyRef"
        )

    return stop_list or {}, stopinfo, active_ref


def _pick_stop_list(state: VehicleState, active_ref: str | None) -> dict[str, Any] | None:
    current = state.topics.get("list/stops") or {}
    if current.get("stops"):
        list_ref = current.get("vehicleJourneyRef")
        if active_ref is None or list_ref is None or journey_refs_match(active_ref, list_ref):
            return current

    if active_ref:
        for ref, cached in state.stop_lists_by_ref.items():
            if cached.get("stops") and journey_refs_match(ref, active_ref):
                return cached

    if current.get("stops"):
        return current

    for cached in state.stop_lists_by_ref.values():
        if cached.get("stops"):
            return cached
    return None


def _pick_stopinfo(
    state: VehicleState,
    *,
    match_ref: str | None,
    stopinfo_ttl_seconds: float,
    has_stop_list: bool,
) -> dict[str, Any] | None:
    current = state.topics.get("stopinfo") or {}
    if current.get("callSequenceNumber") is not None:
        si_ref = current.get("vehicleJourneyRef")
        if match_ref is None or si_ref is None or journey_refs_match(si_ref, match_ref):
            return current

    if not match_ref:
        return None

    now = time.time()
    best: dict[str, Any] | None = None
    best_at = 0.0
    for ref, cached in state.stopinfo_by_ref.items():
        if cached.get("callSequenceNumber") is None:
            continue
        if not journey_refs_match(ref, match_ref):
            continue
        updated_at = state.stopinfo_updated_at.get(ref, 0.0)
        if not has_stop_list and now - updated_at > stopinfo_ttl_seconds:
            continue
        if updated_at >= best_at:
            best = cached
            best_at = updated_at
    return best
