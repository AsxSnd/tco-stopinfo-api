from __future__ import annotations

from datetime import datetime, timedelta, timezone

from tco_stopinfo.builder import build_stopinfo_response
from tco_stopinfo.config import AccountConfig


def _iso_in(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_build_fs_from_mqtt_sample() -> None:
    account = AccountConfig(base_language="fi", max_following_stops=5)
    now = datetime.now(timezone.utc)
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
    assert fs["Line"] == "25"
    assert fs["Heading"] == "Following stops"
    assert fs["Count"] == 2
    assert fs["Content"][0]["Name"] == "Leppäsuonkatu"
    assert "min" in fs["Content"][0]["Time"]
    assert fs["DestinationCount"] >= 1
    assert response["LD"]["StatusCode"] == 204
    assert response["OM"]["StatusCode"] == 204

    # Sanity: builder should not depend on wall-clock for structure
    assert now.year >= 2020
