from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from .config import AccountConfig
from .time_format import format_hhmm_local, get_timezone

STATUS_OK = 200
STATUS_NO_CONTENT = 204
STATUS_NOT_MODIFIED = 304

# Legacy PaCIM-RT / Hogia: X.TC-* second field is 0 when area has no data (204).
TC_HEADER_SUFFIX_NO_DATA = "0"
TC_HEADER_SUFFIX_HAS_DATA = "-1"

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


def _format_hhmm(iso_time: str | None, tz: ZoneInfo) -> str | None:
    return format_hhmm_local(iso_time, tz)


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


def _resolve_fs_target(stopinfo: dict[str, Any] | None) -> tuple[int | None, bool]:
    """Return target call sequence and AtStop from pis/0/stopinfo only."""
    if not stopinfo or stopinfo.get("callSequenceNumber") is None:
        return None, False
    seq = int(stopinfo["callSequenceNumber"])
    stop_type = (stopinfo.get("type") or "ARRIVAL").upper()
    if stop_type == "ARRIVAL":
        return seq, True
    if stop_type in ("DEPARTURE", "PASSAGE"):
        return seq + 1, False
    return seq, True


def _eta_for_sequence(linkprogress: dict[str, Any], seq: int) -> str | None:
    if linkprogress.get("callSequenceNumber") == seq:
        return linkprogress.get("expectedArrivalTime")
    for item in linkprogress.get("followingStops") or []:
        if item.get("callSequenceNumber") == seq:
            return item.get("expectedArrivalTime")
    return None


def _build_following_rows(
    *,
    stops: list[dict[str, Any]],
    linkprogress: dict[str, Any],
    target_seq: int | None,
    at_stop: bool,
    max_stops: int,
    fs_connections: list[dict[str, Any]],
    stop_pressed: bool,
    tz: ZoneInfo,
) -> list[dict[str, Any]]:
    if not stops or target_seq is None:
        return []

    start_idx = _find_start_index(stops, target_seq)
    if start_idx is None:
        return []

    rows: list[dict[str, Any]] = []
    for offset, stop in enumerate(stops[start_idx : start_idx + max_stops]):
        seq = int(stop.get("number", start_idx + offset + 1))
        eta_iso = _eta_for_sequence(linkprogress, seq) or stop.get("estimatedArrivalFull")
        rows.append(
            _build_following_stop_row(
                stop,
                stop_idx=seq,
                eta_iso=eta_iso,
                show_now=offset == 0,
                at_stop=at_stop and offset == 0,
                connections=fs_connections if offset == 0 else [],
                stop_pressed=stop_pressed,
                tz=tz,
            )
        )
    return rows


def _stop_list_index(stops: list[dict[str, Any]], sequence: int | None) -> int | None:
    if sequence is None:
        return None
    for idx, stop in enumerate(stops):
        if stop.get("number") == sequence:
            return idx
    return None


def _find_start_index(stops: list[dict[str, Any]], target_seq: int) -> int | None:
    exact = _stop_list_index(stops, target_seq)
    if exact is not None:
        return exact
    for idx, stop in enumerate(stops):
        if stop.get("number", 0) >= target_seq:
            return idx
    return None


def _delay_minutes(linkprogress: dict[str, Any], stopinfo: dict[str, Any] | None = None) -> int:
    delay_seconds = linkprogress.get("delaySeconds")
    if delay_seconds is None:
        delay_seconds = linkprogress.get("departureDelaySeconds")
    if delay_seconds is None and stopinfo:
        estimate = stopinfo.get("estimate") or {}
        delay_seconds = estimate.get("delay")
    if delay_seconds is None:
        return 0
    return int(delay_seconds // 60)


def _multilanguage_fields(
    heading: str,
    detail: str,
    heading_ml: dict[str, Any] | None,
    detail_ml: dict[str, Any] | None,
    base_language: str,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "Heading": heading,
        "Detail": detail,
    }
    if heading_ml and len(heading_ml) > 1:
        data["Heading_Multilanguage"] = {str(k): str(v) for k, v in heading_ml.items()}
        if base_language in heading_ml:
            data["Heading"] = str(heading_ml[base_language])
    if detail_ml and len(detail_ml) > 1:
        data["Detail_Multilanguage"] = {str(k): str(v) for k, v in detail_ml.items()}
        if base_language in detail_ml:
            data["Detail"] = str(detail_ml[base_language])
    return data


def _iso_or_empty(value: str | None) -> str:
    if not value:
        return ""
    parsed = _parse_iso_datetime(value)
    if parsed is None:
        return value
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_destinations(
    destination: dict[str, Any] | None,
    dest_list: dict[str, Any] | None,
    linkprogress: dict[str, Any] | None,
    stops: list[dict[str, Any]],
    tz: ZoneInfo,
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
                "ETA": _format_hhmm(eta_iso, tz) or "",
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
        if stop_idx < 0 and linkprogress:
            following = linkprogress.get("followingStops") or []
            if following:
                stop_idx = following[-1].get("callSequenceNumber", -1)
            elif linkprogress.get("callSequenceNumber") is not None:
                stop_idx = int(linkprogress["callSequenceNumber"])
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


def _message_active(start: str | None, end: str | None, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    start_dt = _parse_iso_datetime(start)
    end_dt = _parse_iso_datetime(end)
    if start_dt and start_dt > now:
        return False
    if end_dt and end_dt < now:
        return False
    return True


def _om_from_language_array(
    messages: list[dict[str, Any]],
    base_language: str,
) -> tuple[str, str, dict[str, str] | None, dict[str, str] | None]:
    heading_ml: dict[str, str] = {}
    detail_ml: dict[str, str] = {}
    for item in messages:
        lang = str(item.get("language") or "")
        if item.get("heading"):
            heading_ml[lang] = str(item["heading"])
        if item.get("body"):
            detail_ml[lang] = str(item["body"])
    heading = heading_ml.get(base_language) or (next(iter(heading_ml.values()), "") if heading_ml else "")
    detail = detail_ml.get(base_language) or (next(iter(detail_ml.values()), "") if detail_ml else "")
    return heading, detail, heading_ml or None, detail_ml or None


def _build_om_entry(
    message_type: int,
    heading: str,
    detail: str,
    *,
    heading_ml: dict[str, Any] | None = None,
    detail_ml: dict[str, Any] | None = None,
    valid_from: str = "",
    valid_to: str = "",
    base_language: str,
) -> dict[str, Any]:
    data = _multilanguage_fields(heading, detail, heading_ml, detail_ml, base_language)
    data["ValidFrom"] = valid_from
    data["ValidTo"] = valid_to
    return {"MessageType": message_type, "MessageData": data}


def _build_following_stop_row(
    stop: dict[str, Any],
    *,
    stop_idx: int,
    eta_iso: str | None,
    show_now: bool,
    at_stop: bool,
    connections: list[dict[str, Any]],
    stop_pressed: bool,
    tz: ZoneInfo,
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
    arrival = _format_hhmm(eta_iso, tz)
    if arrival:
        row["TimeArrival"] = arrival
    return row


def build_stopinfo_response(
    state_topics: dict[str, Any],
    account: AccountConfig,
) -> dict[str, Any]:
    journey = state_topics.get("journey") or {}
    linkprogress = state_topics.get("linkprogress") or {}
    stopinfo = state_topics.get("stopinfo") or {}
    stop_list = state_topics.get("list/stops") or {}
    destination = state_topics.get("destination") or {}
    connections = state_topics.get("connections")
    dest_list = state_topics.get("list/destinations")
    stop_button = state_topics.get("sensors/stop_button") or {}

    tz = get_timezone(account.timezone)
    stops = _visible_stops(stop_list.get("stops") or [])
    if not journey.get("lineNumber") and not stops and not stopinfo.get("callSequenceNumber"):
        om = _build_om_area(
            connections,
            state_topics.get("announcement"),
            state_topics.get("list/announcements"),
            account,
            "",
        )
        return {
            "FS": _empty_area("Following stops"),
            "LD": _empty_area(),
            "TD": _empty_area(),
            "MD": _empty_area(),
            "OM": om,
        }

    target_seq, at_stop = _resolve_fs_target(stopinfo or None)
    next_sequence = target_seq
    if not next_sequence and stops:
        next_sequence = stops[0].get("number", 1)

    fs_connections = _build_fs_connections(
        connections,
        mode=account.fs_connection_mode,
        max_connections=account.max_connections_per_stop,
    )

    following_rows = _build_following_rows(
        stops=stops,
        linkprogress=linkprogress,
        target_seq=target_seq,
        at_stop=at_stop,
        max_stops=account.max_following_stops,
        fs_connections=fs_connections,
        stop_pressed=bool(stop_button.get("stopPressed")),
        tz=tz,
    )

    start_idx = _find_start_index(stops, target_seq) if stops and target_seq is not None else None
    current_stop_name = ""
    if start_idx is not None and start_idx < len(stops):
        current_stop_name = stops[start_idx].get("name", "")
    elif target_seq is not None:
        stop = _stop_by_sequence(stops, target_seq)
        current_stop_name = (stop or {}).get("name", "")

    destinations = _build_destinations(destination, dest_list, linkprogress, stops, tz)
    primary = destinations[0] if destinations else None

    delay_min = _delay_minutes(linkprogress, stopinfo or None)

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

    ld = _build_ld_area(connections, stops, next_sequence, stopinfo or None, tz)
    om = _build_om_area(
        connections,
        state_topics.get("announcement"),
        state_topics.get("list/announcements"),
        account,
        current_stop_name,
    )

    return {
        "FS": fs,
        "LD": ld,
        "TD": _empty_area(),
        "MD": _empty_area(),
        "OM": om,
    }


def _ld_sequences_match(
    conn_seq: int | None,
    call_sequence: int | None,
    stopinfo: dict[str, Any] | None,
) -> bool:
    if conn_seq is None:
        return True
    allowed: set[int] = set()
    if call_sequence is not None:
        allowed.add(int(call_sequence))
    if stopinfo and stopinfo.get("callSequenceNumber") is not None:
        allowed.add(int(stopinfo["callSequenceNumber"]))
    if not allowed:
        return True
    return conn_seq in allowed


def _parse_presented_departure_minutes(value: str) -> int | None:
    """Parse MQTT presentedDepartureTimes values like '00:06' (minutes:seconds)."""
    parts = value.strip().split(":")
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]) * 60 + int(parts[1])
    except ValueError:
        return None


def _departure_delay_seconds(planned: str | None, expected: str | None) -> int:
    planned_dt = _parse_iso_datetime(planned)
    expected_dt = _parse_iso_datetime(expected)
    if planned_dt is None or expected_dt is None:
        return 0
    return max(0, int((expected_dt - planned_dt).total_seconds()))


def _connection_departure_entries(conn: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize HSL departures[] or Vilnius next* / presentedDepartureTimes formats."""
    departures = conn.get("departures")
    if departures:
        return list(departures[:5])

    expected = conn.get("nextExpectedDepartureTime")
    planned = conn.get("nextPlannedDepartureTime") or expected
    presented = [str(v) for v in (conn.get("presentedDepartureTimes") or [])]

    if presented:
        entries: list[dict[str, Any]] = []
        for idx, presented_value in enumerate(presented[:5]):
            rel_min = _parse_presented_departure_minutes(presented_value)
            if rel_min is None:
                continue
            entry: dict[str, Any] = {"_relative_minutes": rel_min, "_presented": presented_value}
            if idx == 0 and (expected or planned):
                entry["plannedDepartureTime"] = planned
                entry["expectedDepartureTime"] = expected or planned
                entry["departureDelaySeconds"] = (
                    conn.get("departureDelaySeconds")
                    if conn.get("departureDelaySeconds") is not None
                    else _departure_delay_seconds(planned, expected)
                )
            entries.append(entry)
        if entries:
            return entries

    if expected or planned:
        return [
            {
                "plannedDepartureTime": planned,
                "expectedDepartureTime": expected or planned,
                "departureDelaySeconds": (
                    conn.get("departureDelaySeconds")
                    if conn.get("departureDelaySeconds") is not None
                    else _departure_delay_seconds(planned, expected)
                ),
            }
        ]

    return []


def _build_ld_departure_time(
    dep: dict[str, Any],
    tz: ZoneInfo,
) -> tuple[str, dict[str, Any]]:
    expected = dep.get("expectedDepartureTime") or dep.get("plannedDepartureTime")
    planned = dep.get("plannedDepartureTime") or expected
    rel_min = dep.get("_relative_minutes")
    if rel_min is None:
        rel_min = _minutes_until(expected)
    rel = _format_relative_minutes(rel_min, show_now=False) or ""
    absolute = _format_hhmm(expected, tz) or "" if expected else ""
    planned_local = _format_hhmm(planned, tz) or "" if planned else ""
    display = rel or absolute
    return display, {
        "PlannedTime": planned_local,
        "Absolute": absolute,
        "Relative": rel,
        "Live": True,
        "DelayMin": int((dep.get("departureDelaySeconds") or 0) // 60),
        "Cancelled": False,
        "StatusText": "",
    }


def _build_ld_area(
    connections_payload: dict[str, Any] | None,
    stops: list[dict[str, Any]],
    call_sequence: int | None,
    stopinfo: dict[str, Any] | None,
    tz: ZoneInfo,
) -> dict[str, Any]:
    if not connections_payload:
        return _empty_area()

    conn_seq = connections_payload.get("callSequenceNumber")
    if conn_seq is not None:
        conn_seq = int(conn_seq)
    if not _ld_sequences_match(conn_seq, call_sequence, stopinfo):
        return _empty_area()

    expiry = _parse_iso_datetime(connections_payload.get("expiryDateTime"))
    if expiry and expiry < datetime.now(timezone.utc):
        return _empty_area("Departures")

    content: list[dict[str, Any]] = []
    for conn in connections_payload.get("connections") or []:
        if conn.get("cancelled"):
            continue
        departures = _connection_departure_entries(conn)
        times: list[str] = []
        times_extended: list[dict[str, Any]] = []
        for dep in departures:
            display, extended = _build_ld_departure_time(dep, tz)
            if display:
                times.append(display)
            times_extended.append(extended)
        if not times and not times_extended and not conn.get("lineDesignation"):
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


def _om_entry_has_text(entry: dict[str, Any]) -> bool:
    data = entry.get("MessageData") or {}
    if data.get("Heading") or data.get("Detail"):
        return True
    heading_ml = data.get("Heading_Multilanguage") or {}
    detail_ml = data.get("Detail_Multilanguage") or {}
    return bool(heading_ml or detail_ml)


def _filter_om_content(content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [entry for entry in content if _om_entry_has_text(entry)]


def _build_om_area(
    connections_payload: dict[str, Any] | None,
    announcement: dict[str, Any] | None,
    announcements_queue: dict[str, Any] | None,
    account: AccountConfig,
    stop_name: str = "",
) -> dict[str, Any]:
    content: list[dict[str, Any]] = []
    base_language = account.base_language

    if connections_payload:
        for msg in connections_payload.get("situationMessages") or []:
            heading = str(msg.get("heading") or "")
            detail = str(msg.get("body") or "")
            if not heading and not detail and not msg.get("heading_Multilanguage") and not msg.get("body_Multilanguage"):
                continue
            content.append(
                _build_om_entry(
                    2,
                    heading,
                    detail,
                    heading_ml=msg.get("heading_Multilanguage"),
                    detail_ml=msg.get("body_Multilanguage"),
                    valid_from=_iso_or_empty(msg.get("validFrom") or msg.get("start")),
                    valid_to=_iso_or_empty(msg.get("validTo") or msg.get("end")),
                    base_language=base_language,
                )
            )

    if announcements_queue:
        for msg in announcements_queue.get("messages") or []:
            if not _message_active(msg.get("start"), msg.get("end")):
                continue
            lang_messages = msg.get("message") or []
            if not lang_messages:
                continue
            heading, detail, heading_ml, detail_ml = _om_from_language_array(lang_messages, base_language)
            if not heading and not detail:
                continue
            content.append(
                _build_om_entry(
                    2,
                    heading,
                    detail,
                    heading_ml=heading_ml,
                    detail_ml=detail_ml,
                    valid_from=_iso_or_empty(msg.get("start")),
                    valid_to=_iso_or_empty(msg.get("end")),
                    base_language=base_language,
                )
            )

    if announcement:
        messages = announcement.get("message") or []
        if messages:
            heading, detail, heading_ml, detail_ml = _om_from_language_array(messages, base_language)
            if heading or detail:
                content.append(
                    _build_om_entry(
                        0,
                        heading,
                        detail,
                        heading_ml=heading_ml,
                        detail_ml=detail_ml,
                        valid_from=_iso_or_empty(announcement.get("start")),
                        valid_to=_iso_or_empty(announcement.get("end")),
                        base_language=base_language,
                    )
                )

    content = _filter_om_content(content)

    if not content and account.inject_example_om_when_empty:
        for example in account.example_om_messages:
            content.append(
                _build_om_entry(
                    example.message_type,
                    example.heading,
                    example.detail,
                    heading_ml=example.heading_multilanguage,
                    detail_ml=example.detail_multilanguage,
                    valid_from=example.valid_from,
                    valid_to=example.valid_to,
                    base_language=base_language,
                )
            )

    heading = f"Traffic info for {stop_name}" if stop_name and content else ("Traffic info" if content else "")
    return {
        "Count": len(content),
        "Content": content,
        "StatusCode": STATUS_OK if content else STATUS_NO_CONTENT,
        "Heading": heading,
        "Display": -1,
        "Message": "",
    }


def format_tc_status_header(status_code: int) -> str:
    """Format X.TC-* header value per legacy tcoioh (Hogia backward compatibility).

    Examples: 200,-1 (has content), 204,0 (empty), 304,-1 (unchanged).
    """
    suffix = TC_HEADER_SUFFIX_NO_DATA if status_code == STATUS_NO_CONTENT else TC_HEADER_SUFFIX_HAS_DATA
    return f"{status_code},{suffix}"


def build_response_headers(payload: dict[str, Any], *, cache_max_age: int) -> dict[str, str]:
    """Build TCO response headers with legacy PaCIM-RT / Hogia names (X.TC-FS, …)."""
    return {
        "Content-Type": "application/json",
        "Cache-Control": f"max-age={cache_max_age}",
        "X.TC-FS": format_tc_status_header(int(payload["FS"]["StatusCode"])),
        "X.TC-LD": format_tc_status_header(int(payload["LD"]["StatusCode"])),
        "X.TC-TD": format_tc_status_header(int(payload["TD"]["StatusCode"])),
        "X.TC-MD": format_tc_status_header(int(payload["MD"]["StatusCode"])),
        "X.TC-OM": format_tc_status_header(int(payload["OM"]["StatusCode"])),
    }


def legacy_cased_header_items(headers: dict[str, str]) -> list[tuple[bytes, bytes]]:
    """Encode headers for Starlette without lowercasing names (Hogia expects X.TC-FS)."""
    return [(name.encode("latin-1"), value.encode("latin-1")) for name, value in headers.items()]
