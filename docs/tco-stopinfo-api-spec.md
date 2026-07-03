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
| `X.TC-MD` | `204,0` | MD area |
| `X.TC-OM` | `204,0` | OM area |
| `X.TC-TD` | `204,0` | TD area |
| `Cache-Control` | `max-age=30` | Client cache hint |
| `Date` | GMT timestamp | Response time |

`X.TC-*` headers are sent in this order: **FS, LD, MD, OM, TD** (TD last).

Second header value: `0` when area `StatusCode` is 204, else `-1`.

Header **names** use legacy PaCIM-RT casing (`X.TC-FS`). The Python app emits that form when uvicorn runs with **`http=h11`** (the default for this service).

**Why lowercase sometimes appears:**

- **uvicorn `httptools`** lowercases all outgoing header names. Do not use it for this API.
- **HTTP/2** (nginx `listen 443 ssl http2` or default HTTPS curl) always sends `x.tc-fs`. Use HTTP/1.1 to the client if capital letters are required end-to-end.

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
| `TimeArrival` | string | Absolute arrival `hh:mm` (local, per account timezone) |
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

LD times support both the spec `departures[]` format and the Vilnius `nextPlannedDepartureTime` / `presentedDepartureTimes` format. Clock times in `TimeArrival`, `ETA`, and LD `PlannedTime` / `Absolute` are converted from UTC using `accounts.*.timezone`.

## OM — Operation messages

Each `Content[]` item:

| Field | Type |
|-------|------|
| `MessageType` | int (0=general, 1=transport, 2=line, 3=stop, 4=journey) |
| `MessageData.Heading` | string |
| `MessageData.Detail` | string |
| `MessageData.ValidFrom` | ISO 8601 (optional) |
| `MessageData.ValidTo` | ISO 8601 (optional) |
| `MessageData.Heading_Multilanguage` | object (optional) |
| `MessageData.Detail_Multilanguage` | object (optional) |

### Example OM for testing

When the MQTT feed has no operational messages, you can inject sample content per account:

```yaml
accounts:
  vilnius:
    base_language: "lt"
    inject_example_om_when_empty: true
    example_om_messages:
      - message_type: 2
        heading: "Eismo informacija"
        detail: "Bandomasis pranešimas ekranų testavimui."
        heading_multilanguage:
          lt: "Eismo informacija"
          en: "Traffic information"
      - message_type: 2
        heading: "Planuojami darbai"
        detail: "Gatvės remonto darbai gali sukelti vėlavimų."
```

Set `inject_example_om_when_empty: false` (default) in production. Live MQTT messages always replace examples when present.

See also `docs/mqtt-pis-mapping.md` for full MQTT → OM field mapping.

## Account configuration

| Setting | Description |
|---------|-------------|
| `base_language` | Language code for OM and multilanguage defaults |
| `timezone` | IANA timezone for FS/LD clock times (MQTT timestamps are UTC) |
| `max_following_stops` | FS `Content` row limit |
| `max_connections_per_stop` | FS compact connection limit |
| `fs_connection_mode` | `compact` or `none` |
| `inject_example_om_when_empty` | Use `example_om_messages` when MQTT OM is empty |
| `example_om_messages` | List of test OM entries (see above) |

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

`GET /health` → service status and cache overview:

```json
{
  "status": "ok",
  "http_port": 8084,
  "accounts_configured": ["vilnius", "hsl"],
  "mqtt": {
    "layout": "vilniustest/{vehicle}/pis/0/{suffix}",
    "broker": "172.160.242.170",
    "port": 11883,
    "connected": true,
    "messages_received": 42
  },
  "cache": {
    "vehicles_in_memory": 3,
    "vehicles_with_mqtt_data": 2,
    "cached_http_responses": 2,
    "vehicle_ids": ["1721", "1232"],
    "vehicles_with_data_ids": ["1721"],
    "cached_accounts": ["vilnius"]
  }
}
```

- **`vehicles_with_mqtt_data`** — vehicles that have received at least one MQTT message
- **`cached_http_responses`** — pre-built HTTP payloads ready to serve
- If `messages_received` stays 0, check MQTT topic layout in config (`root`, `topic_prefix`, `pis_instance`)

The `{account}` in `/api/stopinfo/{account}/{vehicle}` selects account settings. Any account name works; add preferred accounts under `accounts:` in config for defaults.
