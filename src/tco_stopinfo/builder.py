from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .config import AccountConfig

STATUS_OK = 200
STATUS_NO_CONTENT = 204

TRANSPORT_MODE_CODES = {
    "BUS": 700,
    "TRAM": 900,
    "RAIL": 100,
    "TRAIN": 100,
    "METRO": 400,
    "TUBE": 400,
    "FERRY": 1200,
    "URBAN": 400,
}


def _empty_area(heading: str = "") -> dict[str, Any]:
    return {
        "Count": 0,
        "Content": [],
        "StatusCode": STATUS_NO_CONTENT,
        "Heading": heading,
        "Display": -1,
        "Message": "",
    }


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _minutes_until(iso_time: str | None, now: datetime | None = None) -> int | None:
    target = _parse_iso_datetime(iso_time)
    if target is None:
        return None
    if now is None:
        now = datetime.now(timezone.utc)
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return max(0, int((target - now).total_seconds() // 60))


def _format_relative_minutes(minutes: int | None, *, show_now: bool) -> str | None:
    if minutes is None:
        return None
    if minutes < 1:
        return "Now" if show_now else "1 min"
    return f"{minutes} min"


def _format_hhmm(iso_time: str | None) -> str | None:
    target = _parse_iso_datetime(iso_time)
    if target is None:
        return None
    return target.strftime("%H:%M")


def _tariff_zone(stop: dict[str, Any]) -> str:
    zone_code = stop.get("zoneCode")
    if zone_code is not None:
        return str(zone_code)
    zone = stop.get("zone")
    return str(zone) if zone is not None else ""


def _stop_by_sequence(stops: list[dict[str, Any]], sequence: int) -> dict[str, Any] | None:
    for stop in stops:
        if stop.get("number") == sequence:
            return stop
    return None


def _visible_stops(stops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [s for s in stops if not s.get("blind")]


def _build_destinations(
    destination: dict[str, Any] | None,
    dest_list: dict[str, Any] | None,
    linkprogress: dict[str, Any] | None,
    stops: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(name: str, stop_idx: int, eta_iso: str | None) -> None:
        if not name or name in seen:
            return
        seen.add(name)
        stop_name = ""
        if stop_idx > 0:
            stop = _stop_by_sequence(stops, stop_idx)
            stop_name = (stop or {}).get("name", "")
        minutes = _minutes_until(eta_iso)
        results.append(
            {
                "DestinationName": name,
                "DestinationStopName": stop_name,
                "DestinationStopIdx": stop_idx,
                "ETA": _format_hhmm(eta_iso) or "",
                "ETAMinutes": minutes if minutes is not None else 0,
            }
        )

    if destination:
        ext = destination.get("externalDisplay") or {}
        dest_name = ext.get("destinationName") or destination.get("finalDestinationName") or destination.get("name") or ""
        via = ext.get("viaDestinationName")
        if via and dest_name:
            display = f"{dest_name} via {via}" if "via" not in dest_name.lower() else dest_name
        else:
            display = dest_name
        eta_iso = (linkprogress or {}).get("expectedArrivalTimeDestination")
        last_stop = _visible_stops(stops)[-1] if stops else None
        stop_idx = last_stop.get("number", -1) if last_stop else -1
        add(display, stop_idx, eta_iso)

    if dest_list:
        for item in dest_list.get("destinations") or []:
            name = item.get("name") or ""
            add(name, -1, (linkprogress or {}).get("expectedArrivalTimeDestination"))

    return results


def _build_fs_connections(
    connections_payload: dict[str, Any] | None,
    *,
    mode: str,
    max_connections: int,
) -> list[dict[str, Any]]:
    if not connections_payload or mode == "none":
        return []

    grouped: dict[int, list[dict[str, Any]]] = {}
    for conn in connections_payload.get("connections") or []:
        if conn.get("cancelled"):
            continue
        mode_code = TRANSPORT_MODE_CODES.get(
            (conn.get("transportModeCode") or "BUS").upper(), 700
        )
        line = conn.get("lineDesignation") or ""
        if not line:
            continue
        grouped.setdefault(mode_code, [])
        if mode == "compact":
            if any(item.get("Line") == line for item in grouped[mode_code]):
                continue
            grouped[mode_code].append({"Line": line})
        if len(grouped[mode_code]) >= max_connections:
            continue

    return [
        {"TransportType": transport_type, "Content": content}
        for transport_type, content in grouped.items()
    ]


def _build_following_stop_row(
    stop: dict[str, Any],
    *,
    stop_idx: int,
    eta_iso: str | None,
    show_now: bool,
    at_stop: bool,
    connections: list[dict[str, Any]],
    stop_pressed: bool,
) -> dict[str, Any]:
    minutes = _minutes_until(eta_iso)
    row: dict[str, Any] = {
        "Name": stop.get("name", ""),
        "Requested": bool(stop_pressed or stop.get("alightingAllowed", True)),
        "Note": "cancelled" if stop.get("cancelled") else "",
        "StopIdx": stop_idx,
        "TariffZone": _tariff_zone(stop),
        "AtStop": at_stop,
        "ConnectionPoint": False,
        "Connections": connections,
    }
    relative = _format_relative_minutes(minutes, show_now=show_now)
    if relative:
        row["Time"] = relative
    arrival = _format_hhmm(eta_iso)
    if arrival:
        row["TimeArrival"] = arrival
    return row


def build_stopinfo_response(
    state_topics: dict[str, Any],
    account: AccountConfig,
) -> dict[str, Any]:
    journey = state_topics.get("journey") or {}
    linkprogress = state_topics.get("linkprogress") or {}
    stop_list = state_topics.get("list/stops") or {}
    destination = state_topics.get("destination") or {}
    connections = state_topics.get("connections")
    dest_list = state_topics.get("list/destinations")
    stop_button = state_topics.get("sensors/stop_button") or {}
    door = state_topics.get("sensors/door") or {}

    stops = _visible_stops(stop_list.get("stops") or [])
    if not journey.get("lineNumber") and not stops:
        return {
            "FS": _empty_area("Following stops"),
            "LD": _empty_area(),
            "TD": _empty_area(),
            "MD": _empty_area(),
            "OM": _empty_area(),
        }

    next_sequence = linkprogress.get("callSequenceNumber")
    if not next_sequence and stops:
        next_sequence = stops[0].get("number", 1)

    distance = linkprogress.get("distance")
    at_stop = distance == 0 or (door.get("doorOpen") is True)

    following_rows: list[dict[str, Any]] = []
    fs_connections = _build_fs_connections(
        connections,
        mode=account.fs_connection_mode,
        max_connections=account.max_connections_per_stop,
    )

    following_meta = {item.get("callSequenceNumber"): item for item in linkprogress.get("followingStops") or []}
    start_idx = 0
    for idx, stop in enumerate(stops):
        if stop.get("number") == next_sequence:
            start_idx = idx
            break

    for offset, stop in enumerate(stops[start_idx : start_idx + account.max_following_stops]):
        seq = stop.get("number", start_idx + offset + 1)
        meta = following_meta.get(seq, {})
        eta_iso = meta.get("expectedArrivalTime") or stop.get("estimatedArrivalFull")
        if offset == 0 and linkprogress.get("expectedArrivalTime"):
            eta_iso = linkprogress.get("expectedArrivalTime")
        following_rows.append(
            _build_following_stop_row(
                stop,
                stop_idx=seq if isinstance(seq, int) else offset + 1,
                eta_iso=eta_iso,
                show_now=offset == 0,
                at_stop=at_stop and offset == 0,
                connections=fs_connections if offset == 0 else [],
                stop_pressed=bool(stop_button.get("stopPressed")),
            )
        )

    destinations = _build_destinations(destination, dest_list, linkprogress, stops)
    primary = destinations[0] if destinations else None

    delay_seconds = linkprogress.get("delaySeconds") or 0
    delay_min = int(delay_seconds // 60) if delay_seconds else 0

    line = ""
    ext = destination.get("externalDisplay") or {} if destination else {}
    line = ext.get("lineNumber") or journey.get("lineNumber") or ""

    fs: dict[str, Any] = {
        "Count": len(following_rows),
        "Content": following_rows,
        "StatusCode": STATUS_OK if following_rows else STATUS_NO_CONTENT,
        "Heading": "Following stops",
        "Display": -1,
        "Message": "",
        "Line": str(line),
        "JourneyIdent": journey.get("vehicleJourneyRef") or stop_list.get("vehicleJourneyRef") or "",
        "DelayMin": delay_min,
        "DistanceFromPrev": -1,
        "DistanceToNext": linkprogress.get("distance", -1) if linkprogress.get("distance") is not None else -1,
        "DestinationCount": len(destinations),
        "DestinationExtended": destinations,
        "Via": [],
    }
    if primary:
        fs["DestinationName"] = primary["DestinationName"]
        fs["ETA"] = primary["ETA"]
        fs["ETAMinutes"] = primary["ETAMinutes"]

    ld = _build_ld_area(connections, stops, next_sequence)
    om = _build_om_area(connections, state_topics.get("announcement"), account.base_language)

    return {
        "FS": fs,
        "LD": ld,
        "TD": _empty_area(),
        "MD": _empty_area(),
        "OM": om,
    }


def _build_ld_area(
    connections_payload: dict[str, Any] | None,
    stops: list[dict[str, Any]],
    call_sequence: int | None,
) -> dict[str, Any]:
    if not connections_payload:
        return _empty_area()

    if connections_payload.get("callSequenceNumber") not in (None, call_sequence):
        return _empty_area()

    expiry = _parse_iso_datetime(connections_payload.get("expiryDateTime"))
    if expiry and expiry < datetime.now(timezone.utc):
        return _empty_area("Departures")

    content: list[dict[str, Any]] = []
    for conn in connections_payload.get("connections") or []:
        if conn.get("cancelled"):
            continue
        departures = conn.get("departures") or []
        times: list[str] = []
        times_extended: list[dict[str, Any]] = []
        for dep in departures[:5]:
            rel_min = _minutes_until(dep.get("expectedDepartureTime"))
            rel = _format_relative_minutes(rel_min, show_now=False) or ""
            times.append(rel)
            times_extended.append(
                {
                    "PlannedTime": _format_hhmm(dep.get("plannedDepartureTime")) or "",
                    "Absolute": _format_hhmm(dep.get("expectedDepartureTime")) or "",
                    "Relative": rel,
                    "Live": True,
                    "DelayMin": int((dep.get("departureDelaySeconds") or 0) // 60),
                    "Cancelled": False,
                    "StatusText": "",
                }
            )
        if not times and not conn.get("lineDesignation"):
            continue
        content.append(
            {
                "Mode": (conn.get("transportModeCode") or "BUS").upper(),
                "Line": conn.get("lineDesignation") or "",
                "Dest": conn.get("directionName") or "",
                "Dir": "",
                "Stop": conn.get("stopPointDesignation") or "",
                "Times": times,
                "TimesExtended": times_extended,
            }
        )

    stop_name = ""
    if call_sequence:
        stop = _stop_by_sequence(stops, call_sequence)
        stop_name = (stop or {}).get("name", "")

    heading = connections_payload.get("heading") or (
        f"Departures at {stop_name}" if stop_name else "Departures"
    )
    return {
        "Count": len(content),
        "Content": content,
        "StatusCode": STATUS_OK if content else STATUS_NO_CONTENT,
        "Heading": heading,
        "Display": connections_payload.get("displayDurationSeconds", -1),
        "Message": connections_payload.get("message") or "",
    }


def _build_om_area(
    connections_payload: dict[str, Any] | None,
    announcement: dict[str, Any] | None,
    base_language: str,
) -> dict[str, Any]:
    content: list[dict[str, Any]] = []

    if connections_payload:
        for msg in connections_payload.get("situationMessages") or []:
            content.append(
                {
                    "MessageType": 0,
                    "MessageData": {
                        "Heading": msg.get("heading", ""),
                        "Detail": msg.get("body", ""),
                        "ValidFrom": "",
                        "ValidTo": "",
                    },
                }
            )

    if announcement:
        messages = announcement.get("message") or []
        chosen = next((m for m in messages if m.get("language") == base_language), None)
        if chosen is None and messages:
            chosen = messages[0]
        if chosen:
            content.append(
                {
                    "MessageType": 0,
                    "MessageData": {
                        "Heading": chosen.get("heading", ""),
                        "Detail": chosen.get("body", ""),
                        "ValidFrom": "",
                        "ValidTo": "",
                    },
                }
            )

    return {
        "Count": len(content),
        "Content": content,
        "StatusCode": STATUS_OK if content else STATUS_NO_CONTENT,
        "Heading": "Traffic info" if content else "",
        "Display": -1,
        "Message": "",
    }


def build_response_headers(payload: dict[str, Any], *, cache_max_age: int) -> dict[str, str]:
    def tc_header(area: str) -> str:
        code = int(payload[area]["StatusCode"])
        suffix = "0" if code == STATUS_NO_CONTENT else "-1"
        return f"{code},{suffix}"

    return {
        "Content-Type": "application/json",
        "Cache-Control": f"max-age={cache_max_age}",
        "X.TC-FS": tc_header("FS"),
        "X.TC-LD": tc_header("LD"),
        "X.TC-TD": tc_header("TD"),
        "X.TC-MD": tc_header("MD"),
        "X.TC-OM": tc_header("OM"),
    }
