from __future__ import annotations

from datetime import datetime, timedelta, timezone

from tco_stopinfo.builder import build_stopinfo_response
from tco_stopinfo.config import AccountConfig, ExampleOmMessageConfig
from tco_stopinfo.journey_context import resolve_journey_stop_context
from tco_stopinfo.store import VehicleState


def _iso_in(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_ago(minutes: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _vilnius_stops() -> list[dict]:
    names = [
        "Senoji plytinė",
        "Gedimino technikos universitetas",
        "Vilniaus universitetas",
        "Saulėtekis",
        "Nemenčinės plentas",
        "Antakalnio žiedas",
        "Lizdeikos st.",
        "Oskaro Milašiaus st.",
        "Valakampių tiltas",
        "Kareivių st.",
        "Verkių st.",
        "Pramogų arena",
        "Tauragnų st.",
        "Giedraičių st.",
        "Žalgirio st.",
        "Kalvarijų turgus",
        "Žaliasis tiltas",
        "Operos ir baleto teatras",
        "Kražių st.",
        "Juozo Tumo-Vaižganto st.",
        "Mikalojaus Konstantino Čiurlionio st.",
        "Taraso Ševčenkos st.",
        "Vienaragių st.",
        "Prūsų st.",
        "Naujininkai",
    ]
    return [
        {
            "number": i + 1,
            "name": name,
            "estimatedArrivalFull": _iso_in(i + 5),
            "estimatedDepartureFull": _iso_in(i + 5),
            "cancelled": False,
        }
        for i, name in enumerate(names)
    ]


def test_build_fs_from_mqtt_sample() -> None:
    account = AccountConfig(base_language="fi", max_following_stops=5)
    topics = {
        "journey": {
            "lineNumber": "25",
            "journeyNumber": "1026",
            "vehicleJourneyRef": "1025_20260629_Ke_1_1026",
        },
        "destination": {
            "finalDestinationName": "Pajamäki",
            "externalDisplay": {
                "lineNumber": "25",
                "destinationName": "Pajamäki",
                "viaDestinationName": "Munkkivuori",
            },
        },
        "list/stops": {
            "vehicleJourneyRef": "1025_20260629_Ke_1_1026",
            "stops": [
                {"number": 1, "name": "Current", "zoneCode": "A"},
                {"number": 2, "name": "Leppäsuonkatu", "zoneCode": "A"},
                {"number": 3, "name": "Arkadiankatu", "zoneCode": "A"},
            ],
        },
        "stopinfo": {"callSequenceNumber": 1, "type": "DEPARTURE"},
        "linkprogress": {
            "callSequenceNumber": 2,
            "distance": 120,
            "expectedArrivalTime": _iso_in(2),
            "expectedArrivalTimeDestination": _iso_in(21),
            "delaySeconds": 0,
            "followingStops": [
                {"callSequenceNumber": 2, "expectedArrivalTime": _iso_in(2)},
                {"callSequenceNumber": 3, "expectedArrivalTime": _iso_in(5)},
            ],
        },
    }

    response = build_stopinfo_response(topics, account)
    fs = response["FS"]

    assert fs["StatusCode"] == 200
    assert fs["Count"] == 2
    assert fs["Content"][0]["Name"] == "Leppäsuonkatu"
    assert fs["Content"][0]["StopIdx"] == 2
    assert fs["Content"][0]["AtStop"] is False


def test_vilnius_departure_17_shows_stops_18_to_22() -> None:
    account = AccountConfig(base_language="lt", max_following_stops=5)
    journey_ref = "T10-05-1-260620-ab-1420"
    topics = {
        "journey": {"lineNumber": "10", "vehicleJourneyRef": f"10{journey_ref}"},
        "destination": {"externalDisplay": {"lineNumber": "10", "destinationName": "Naujininkai"}},
        "list/stops": {"vehicleJourneyRef": journey_ref, "stops": _vilnius_stops()},
        "stopinfo": {
            "callSequenceNumber": 17,
            "type": "DEPARTURE",
            "vehicleJourneyRef": journey_ref,
            "estimate": {"callSequenceNumberNext": 18, "delay": 120},
        },
        "linkprogress": {},
    }

    response = build_stopinfo_response(topics, account)
    fs = response["FS"]

    assert fs["StatusCode"] == 200
    assert fs["Count"] == 5
    assert fs["Content"][0]["Name"] == "Operos ir baleto teatras"
    assert fs["Content"][0]["StopIdx"] == 18
    assert fs["Content"][0]["AtStop"] is False
    assert fs["Content"][1]["Name"] == "Kražių st."
    assert fs["DelayMin"] == 2


def test_build_fs_at_stop_uses_stopinfo_arrival() -> None:
    account = AccountConfig(base_language="fi", max_following_stops=5)
    topics = {
        "journey": {"lineNumber": "41", "vehicleJourneyRef": "1041_20260629_Ke_2_1332"},
        "list/stops": {
            "stops": [
                {"number": 1, "name": "Pohjois-Haagan asema", "zoneCode": "B"},
                {"number": 2, "name": "Lassila", "zoneCode": "B"},
                {"number": 3, "name": "Näyttelijäntie", "zoneCode": "B"},
            ],
        },
        "stopinfo": {"callSequenceNumber": 1, "type": "ARRIVAL"},
        "linkprogress": {"delaySeconds": 540},
    }

    response = build_stopinfo_response(topics, account)
    fs = response["FS"]

    assert fs["DelayMin"] == 9
    assert fs["Content"][0]["AtStop"] is True
    assert fs["Content"][0]["StopIdx"] == 1
    assert fs["Content"][0]["Name"] == "Pohjois-Haagan asema"


def test_stale_stopinfo_from_other_journey_is_ignored() -> None:
    account = AccountConfig(base_language="lt", max_following_stops=5)
    stops = [{"number": i, "name": f"Stop {i}", "zoneCode": "A"} for i in range(1, 7)]
    topics = {
        "journey": {"lineNumber": "15", "vehicleJourneyRef": "15T15-01-1-260620-b1b-1410"},
        "list/stops": {"vehicleJourneyRef": "T15-01-1-260620-b1b-1410", "stops": stops},
        "stopinfo": {
            "callSequenceNumber": 1,
            "type": "DEPARTURE",
            "vehicleJourneyRef": "T15-01-1-260620-ba-1420",
        },
    }

    state = VehicleState(vehicle_id="1730")
    for suffix, payload in topics.items():
        state.set_topic(suffix, payload)

    stop_list, stopinfo, _ref = resolve_journey_stop_context(state)
    merged = {**topics, "list/stops": stop_list, "stopinfo": stopinfo or {}}
    response = build_stopinfo_response(merged, account)

    assert response["FS"]["Count"] == 0


def test_merge_stop_list_keeps_full_route_on_partial_update() -> None:
    from tco_stopinfo.journey_context import merge_stop_list_payload

    ref = "T10-05-1-260620-ab-1420"
    full = {"vehicleJourneyRef": ref, "stops": [{"number": i, "name": f"S{i}"} for i in range(1, 26)]}
    partial = {"vehicleJourneyRef": ref, "stops": [{"number": 22, "name": "Only22"}]}
    merged = merge_stop_list_payload(full, partial)
    assert len(merged["stops"]) == 25
    assert merged["stops"][21]["name"] == "Only22"


def test_partial_stop_list_update_still_returns_five_following_stops() -> None:
    from tco_stopinfo.app import ApplicationState
    from tco_stopinfo.config import load_config
    import orjson

    ref = "T10-05-1-260620-ab-1420"
    cfg = load_config("config.example.yaml")
    app = ApplicationState(cfg)
    state = app.store.get_or_create("1733")
    full = {"vehicleJourneyRef": ref, "stops": [{"number": i, "name": f"S{i}"} for i in range(1, 26)]}
    partial = {"vehicleJourneyRef": ref, "stops": [{"number": 22, "name": "Only22"}]}
    state.set_topic("journey", {"lineNumber": "10", "vehicleJourneyRef": f"10{ref}"})
    state.set_topic("list/stops", full)
    state.set_topic("list/stops", partial)
    state.set_topic(
        "stopinfo",
        {"callSequenceNumber": 17, "type": "DEPARTURE", "vehicleJourneyRef": ref},
    )
    app.rebuild_vehicle("1733", accounts=["vilnius"])
    fs = orjson.loads(app.store.get_response("vilnius", "1733", fast_response_seconds=0).body)["FS"]
    assert fs["Count"] == 5
    assert fs["Content"][0]["StopIdx"] == 18


def test_journey_cache_pairs_stopinfo_with_cached_stop_list() -> None:
    journey_ref = "T10-05-1-260620-ab-1420"
    state = VehicleState(vehicle_id="1733")
    state.set_topic(
        "journey",
        {"lineNumber": "10", "vehicleJourneyRef": f"10{journey_ref}"},
    )
    state.set_topic(
        "stopinfo",
        {
            "callSequenceNumber": 17,
            "type": "DEPARTURE",
            "vehicleJourneyRef": journey_ref,
        },
    )
    state.set_topic("list/stops", {"vehicleJourneyRef": journey_ref, "stops": []})
    state.set_topic(
        "list/stops",
        {"vehicleJourneyRef": journey_ref, "stops": _vilnius_stops()},
    )

    stop_list, stopinfo, _ref = resolve_journey_stop_context(state)
    topics = {
        **state.topics,
        "list/stops": stop_list,
        "stopinfo": stopinfo or {},
    }
    response = build_stopinfo_response(topics, AccountConfig(max_following_stops=5))

    assert response["FS"]["Count"] == 5
    assert response["FS"]["Content"][0]["Name"] == "Operos ir baleto teatras"


def test_build_om_from_situation_messages_with_multilanguage() -> None:
    account = AccountConfig(base_language="fi", max_following_stops=5)
    topics = {
        "journey": {"lineNumber": "41"},
        "list/stops": {
            "stops": [{"number": 1, "name": "Pohjois-Haagan asema", "zoneCode": "B"}],
        },
        "stopinfo": {"callSequenceNumber": 1, "type": "ARRIVAL"},
        "connections": {
            "situationMessages": [
                {
                    "heading": "Test",
                    "body": "Detail",
                    "heading_Multilanguage": {"fi": "Test", "en": "Test EN"},
                    "body_Multilanguage": {"fi": "Detail", "en": "Detail EN"},
                }
            ],
        },
    }

    response = build_stopinfo_response(topics, account)
    assert response["OM"]["StatusCode"] == 200


def test_build_om_from_announcement_queue() -> None:
    account = AccountConfig(base_language="en", max_following_stops=5)
    topics = {
        "journey": {"lineNumber": "41"},
        "list/stops": {"stops": [{"number": 1, "name": "Central", "zoneCode": "A"}]},
        "stopinfo": {"callSequenceNumber": 1, "type": "DEPARTURE"},
        "list/announcements": {
            "messages": [
                {
                    "messageId": "1",
                    "start": _iso_ago(5),
                    "end": _iso_in(60),
                    "message": [
                        {"language": "en", "heading": "Disruption", "body": "Delays expected"},
                    ],
                }
            ]
        },
    }

    response = build_stopinfo_response(topics, account)
    assert response["OM"]["Count"] == 1


def test_vilnius_timezone_converts_fs_time_arrival() -> None:
    account = AccountConfig(base_language="lt", timezone="Europe/Vilnius", max_following_stops=5)
    topics = {
        "journey": {"lineNumber": "10", "vehicleJourneyRef": "T10"},
        "list/stops": {
            "stops": [
                {
                    "number": 1,
                    "name": "Stop 1",
                    "estimatedArrivalFull": "2026-07-01T11:18:00Z",
                },
                {"number": 2, "name": "Stop 2"},
            ],
        },
        "stopinfo": {"callSequenceNumber": 1, "type": "ARRIVAL"},
        "linkprogress": {},
    }

    response = build_stopinfo_response(topics, account)
    assert response["FS"]["Content"][0]["TimeArrival"] == "14:18"


def test_ld_times_from_vilnius_connections_format() -> None:
    account = AccountConfig(base_language="lt", timezone="Europe/Vilnius", max_following_stops=5)
    topics = {
        "journey": {"lineNumber": "10"},
        "list/stops": {
            "stops": [
                {"number": 1, "name": "Stop A"},
                {"number": 2, "name": "Stop B"},
            ],
        },
        "stopinfo": {"callSequenceNumber": 2, "type": "ARRIVAL"},
        "connections": {
            "callSequenceNumber": 2,
            "expiryDateTime": "2026-07-01T13:57:00Z",
            "connections": [
                {
                    "transportModeCode": "Trolleybus",
                    "lineDesignation": "6",
                    "directionName": "Žemieji Paneriai (Apylanka be Reformatų st.)",
                    "nextPlannedDepartureTime": "2026-07-01T13:37:00Z",
                    "nextExpectedDepartureTime": "2026-07-01T13:37:00Z",
                    "presentedDepartureTimes": ["00:16", "00:30"],
                    "cancelled": False,
                }
            ],
        },
    }

    response = build_stopinfo_response(topics, account)
    row = response["LD"]["Content"][0]
    assert row["Line"] == "6"
    assert len(row["Times"]) >= 1
    assert row["TimesExtended"][0]["PlannedTime"] == "16:37"
    assert row["TimesExtended"][0]["Absolute"] == "16:37"
    assert row["TimesExtended"][0]["Relative"] == "16 min"
    assert len(row["Times"]) == 2
    assert row["TimesExtended"][1]["Relative"] == "30 min"


def test_ld_times_at_departure_stop_sequence() -> None:
    account = AccountConfig(base_language="lt", timezone="Europe/Vilnius", max_following_stops=5)
    topics = {
        "journey": {"lineNumber": "10"},
        "list/stops": {
            "stops": [
                {"number": 17, "name": "Žaliasis tiltas"},
                {"number": 18, "name": "Operos ir baleto teatras"},
            ],
        },
        "stopinfo": {"callSequenceNumber": 17, "type": "DEPARTURE"},
        "connections": {
            "callSequenceNumber": 17,
            "connections": [
                {
                    "transportModeCode": "BUS",
                    "lineDesignation": "53",
                    "directionName": "Centras",
                    "stopPointDesignation": "A",
                    "departures": [
                        {
                            "plannedDepartureTime": "2026-07-01T11:30:00Z",
                            "expectedDepartureTime": "2026-07-01T11:35:00Z",
                            "departureDelaySeconds": 300,
                        }
                    ],
                }
            ],
        },
    }

    response = build_stopinfo_response(topics, account)
    ld = response["LD"]
    assert ld["StatusCode"] == 200
    assert ld["Count"] == 1
    row = ld["Content"][0]
    assert row["Line"] == "53"
    assert row["TimesExtended"][0]["PlannedTime"] == "14:30"
    assert row["TimesExtended"][0]["Absolute"] == "14:35"
    assert row["TimesExtended"][0]["DelayMin"] == 5


def test_inject_example_om_when_mqtt_empty() -> None:
    account = AccountConfig(
        base_language="lt",
        inject_example_om_when_empty=True,
        example_om_messages=[
            ExampleOmMessageConfig(message_type=2, heading="Test 1", detail="Detail 1"),
            ExampleOmMessageConfig(message_type=2, heading="Test 2", detail="Detail 2"),
        ],
    )
    topics = {
        "journey": {"lineNumber": "10"},
        "list/stops": {"stops": [{"number": 1, "name": "Stop A"}]},
        "stopinfo": {"callSequenceNumber": 1, "type": "ARRIVAL"},
    }

    response = build_stopinfo_response(topics, account)
    om = response["OM"]

    assert om["StatusCode"] == 200
    assert om["Count"] == 2
    assert om["Content"][0]["MessageData"]["Heading"] == "Test 1"
    assert om["Content"][1]["MessageData"]["Detail"] == "Detail 2"


def test_mqtt_om_takes_precedence_over_examples() -> None:
    account = AccountConfig(
        base_language="lt",
        inject_example_om_when_empty=True,
        example_om_messages=[
            ExampleOmMessageConfig(message_type=2, heading="Example", detail="Should not appear"),
        ],
    )
    topics = {
        "journey": {"lineNumber": "10"},
        "list/stops": {"stops": [{"number": 1, "name": "Stop A"}]},
        "stopinfo": {"callSequenceNumber": 1, "type": "ARRIVAL"},
        "connections": {
            "situationMessages": [{"heading": "Live", "body": "From MQTT"}],
        },
    }

    response = build_stopinfo_response(topics, account)
    assert response["OM"]["Count"] == 1
    assert response["OM"]["Content"][0]["MessageData"]["Heading"] == "Live"

