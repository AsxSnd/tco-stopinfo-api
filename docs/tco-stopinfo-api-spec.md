# TCO Stopinfo API — HTTP specification

This document describes the **TCO API2** stop-info response format implemented by this service. It is compatible with the legacy PaCIM-RT `tcoioh` service (`PPluginHSL.dll` deployment).

## Endpoint

| Item | Value |
|------|-------|
| Method | `GET` |
| Path | `/api/stopinfo/{account}/{vehicle}` |
| Example | `/api/stopinfo/hsl/1232` |
| Content-Type | `application/json` |

### Path parameters

| Parameter | Description |
|-----------|-------------|
| `account` | Operator/account id (e.g. `hsl`). Selects account-specific limits in `config.yaml`. |
| `vehicle` | Vehicle identifier used to look up cached MQTT state. |

### Optional query parameters

| Parameter | Description |
|-----------|-------------|
| `unit` | Reserved for multi-unit vehicles (accepted, not required for cache key today). |

## Top-level response

The body is a JSON object with five protocol areas:

```json
{
  "FS": { },
  "LD": { },
  "TD": { },
  "MD": { },
  "OM": { }
}
```

| Key | Name | Purpose |
|-----|------|---------|
| FS | Following Stops | Upcoming stops on the current journey |
| LD | Line/Bus Destinations | Connecting departures at the current stop |
| TD | Train Destinations | Rail departures (Darwin LDBWS in full ITCS stack) |
| MD | Metro Destinations | Metro departures (TfGM in full ITCS stack) |
| OM | Operation Messages | Traffic / operational messages |

Each area is independent. HTTP status is always **200**; per-area status is in `StatusCode`.

## Common area fields

| Field | Type | Description |
|-------|------|-------------|
| `StatusCode` | int | **200** = display new content; **204** = nothing to show; **304** = unchanged (legacy clients) |
| `Heading` | string | Section title for displays |
| `Count` | int | Items in `Content` |
| `Content` | array | Area-specific rows |
| `Display` | int | Recommended display seconds; **-1** = client decides |
| `Message` | string | Text when empty |

### HTTP response headers

| Header | Example | Meaning |
|--------|---------|---------|
| `X.TC-FS` | `200,-1` | FS area status + legacy flag |
| `X.TC-LD` | `204,0` | LD area |
| `X.TC-TD` | `204,0` | TD area |
| `X.TC-MD` | `204,0` | MD area |
| `X.TC-OM` | `204,0` | OM area |
| `Cache-Control` | `max-age=30` | Client cache hint |
| `Date` | GMT timestamp | Response time |

Second header value: `0` when area `StatusCode` is 204, else `-1`.

## FS — Following Stops

### Area fields (in addition to common)

| Field | Type | Description |
|-------|------|-------------|
| `Line` | string | Current line |
| `JourneyIdent` | string | Journey reference |
| `DelayMin` | int | Current delay in minutes |
| `DistanceFromPrev` | int | Metres from previous stop; `-1` if unknown |
| `DistanceToNext` | int | Metres to next stop; `-1` if unknown |
| `DestinationName` | string | Primary destination (legacy) |
| `ETA` | string | Primary destination arrival `hh:mm` |
| `ETAMinutes` | int | Minutes to primary destination |
| `DestinationCount` | int | Number of destinations |
| `DestinationExtended` | array | All destinations |
| `Via` | array | Via points `{ Seq, ViaText, Prio }` |

### `Content[]` stop row

| Field | Type | Description |
|-------|------|-------------|
| `Name` | string | Stop name |
| `StopIdx` | int | Stop sequence index |
| `Time` | string | Relative time (`2 min`, `Now`, `1 min`) |
| `TimeArrival` | string | Absolute arrival `hh:mm` |
| `TariffZone` | string | Fare zone |
| `Requested` | bool | Stop requested / alighting |
| `AtStop` | bool | Vehicle at this stop |
| `ConnectionPoint` | bool | Transfer hub |
| `Note` | string | Stop note |
| `Connections` | array | Compact connections (see below) |

### `Connections[]`

| Field | Type | Description |
|-------|------|-------------|
| `TransportType` | int | GTFS-like mode (Bus=700, Tram=900, Rail=100, Metro=400) |
| `Content` | array | `{ "Line": "..." }` in compact mode |

### `DestinationExtended[]`

| Field | Type |
|-------|------|
| `DestinationName` | string |
| `DestinationStopName` | string |
| `DestinationStopIdx` | int |
| `ETA` | string |
| `ETAMinutes` | int |

## LD / TD / MD — Departure boards

When populated, each `Content[]` item:

| Field | Type | Description |
|-------|------|-------------|
| `Mode` | string | Transport mode |
| `Line` | string | Line designation |
| `Dest` | string | Destination |
| `Dir` | string | Direction text |
| `Stop` | string | Stop/platform |
| `Times` | string[] | Legacy relative times |
| `TimesExtended` | array | Rich time objects |

### `TimesExtended[]`

| Field | Type |
|-------|------|
| `PlannedTime` | string |
| `Absolute` | string |
| `Relative` | string |
| `Live` | bool |
| `DelayMin` | int |
| `Cancelled` | bool |
| `StatusText` | string |

**Note:** This MQTT-backed service populates **LD** from `pis/{vehicle}/connections` and leaves **TD** / **MD** empty unless extended later.

## OM — Operation messages

Each `Content[]` item:

| Field | Type |
|-------|------|
| `MessageType` | int (0=general, 1=transport, 2=line, 3=stop, 4=journey) |
| `MessageData.Heading` | string |
| `MessageData.Detail` | string |
| `MessageData.ValidFrom` | ISO 8601 (optional) |
| `MessageData.ValidTo` | ISO 8601 (optional) |

## Example (vehicle 1232)

See live reference: [http://pacimitcs-scand.ltg-emea.com:8084/api/stopinfo/hsl/1232](http://pacimitcs-scand.ltg-emea.com:8084/api/stopinfo/hsl/1232)

```json
{
  "FS": {
    "StatusCode": 200,
    "Heading": "Following stops",
    "Count": 5,
    "Line": "25",
    "DestinationName": "Pajamäki via Munkkivuori",
    "Content": [
      {
        "Name": "Leppäsuonkatu",
        "Time": "2 min",
        "TimeArrival": "10:28",
        "StopIdx": 1,
        "TariffZone": "A",
        "Requested": true,
        "AtStop": false,
        "Connections": []
      }
    ]
  },
  "LD": { "StatusCode": 204, "Count": 0, "Content": [] },
  "TD": { "StatusCode": 204, "Count": 0, "Content": [] },
  "MD": { "StatusCode": 204, "Count": 0, "Content": [] },
  "OM": { "StatusCode": 204, "Count": 0, "Content": [] }
}
```

## Health check

`GET /health` → `{ "status": "ok" }`
