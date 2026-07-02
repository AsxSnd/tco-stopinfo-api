# MQTT-PIS-PT → TCO Stopinfo API mapping

This service subscribes to **MQTT-PIS-PT V1.6.0** topics (see `docs/mqtt-pis-pt-specification.md`) and maps vehicle state into the TCO API2 JSON envelope.

## Topic naming

See **[mqtt-topic-layout.md](mqtt-topic-layout.md)** for full broker tree examples.

### Vilnius-style layout (broker root + vehicle + spec)

```
vilniustest/{vehicle_id}/pis/0/{suffix}
```

| MQTT topic | Example (vehicle 1232) |
|------------|------------------------|
| `{root}/{vehicle_id}/pis/0/journey` | `vilniustest/1232/pis/0/journey` |
| `{root}/{vehicle_id}/pis/0/linkprogress` | `vilniustest/1232/pis/0/linkprogress` |
| `{root}/{vehicle_id}/pis/0/list/stops` | `vilniustest/1232/pis/0/list/stops` |
| `{root}/{vehicle_id}/pis/0/stopinfo` | `vilniustest/1232/pis/0/stopinfo` |
| `{root}/{vehicle_id}/pis/0/connections` | `vilniustest/1232/pis/0/connections` |

Config:

```yaml
mqtt:
  root: "vilniustest"
  topic_prefix: "pis"
  pis_instance: "0"
```

Subscriptions: `vilniustest/+/pis/0/journey`, etc.

### Flat layout (legacy)

| MQTT topic | Example |
|------------|---------|
| `{prefix}/{vehicle_id}/journey` | `pis/1232/journey` |

Set `mqtt.root: ""` and `topic_prefix: pis`.

## Subscribed topics

| MQTT suffix | Retain | Used for TCO area |
|-------------|--------|-------------------|
| `journey` | yes | FS — line, journey id |
| `destination` | yes | FS — destination header |
| `linkprogress` | no (1 Hz) | FS — ETAs, delay, distance |
| `list/stops` | yes | FS — stop names, zones |
| `list/destinations` | yes | FS — multiple destinations |
| `stopinfo` | yes | FS — position (call sequence, ARRIVAL/DEPARTURE) |
| `connections` | yes | FS connections + **LD** + **OM** situations |
| `journeystate` | yes | (stored; future gating of FS when not in traffic) |
| `announcement` | yes | **OM** |
| `list/announcements` | yes | **OM** |
| `sensors/stop_button` | yes | FS — `Requested` on stops |
| `sensors/door` | yes | (stored; optional FS hint) |

Topics not listed are ignored.

## Account settings

Per-account options in `config.yaml` under `accounts.{name}`:

| Setting | Default | Purpose |
|---------|---------|---------|
| `base_language` | `fi` | OM / multilanguage text selection |
| `timezone` | `UTC` | Convert MQTT UTC ISO timestamps to local `hh:mm` (FS, LD) |
| `max_following_stops` | `5` | FS row count |
| `max_connections_per_stop` | `3` | FS compact connections per mode |
| `fs_connection_mode` | `compact` | `compact`, `none` |
| `inject_example_om_when_empty` | `false` | Inject test OM when MQTT has no messages |
| `example_om_messages` | `[]` | Sample OM rows (see below) |

**Windows:** install the `tzdata` package (included in project dependencies) so IANA timezones such as `Europe/Vilnius` work.

Example (Vilnius):

```yaml
accounts:
  vilnius:
    base_language: "lt"
    timezone: "Europe/Vilnius"
    inject_example_om_when_empty: true
    example_om_messages:
      - message_type: 2
        heading: "Eismo informacija"
        detail: "Bandomasis pranešimas ekranų testavimui."
        heading_multilanguage:
          lt: "Eismo informacija"
          en: "Traffic information"
```

Example messages are only used when no live OM data is present from MQTT (`connections.situationMessages`, `announcement`, `list/announcements`).

## FS — Following Stops

| TCO JSON field | MQTT source | Transformation |
|----------------|-------------|----------------|
| `Line` | `destination.externalDisplay.lineNumber` → `journey.lineNumber` | First non-empty |
| `JourneyIdent` | `journey.vehicleJourneyRef` → `list/stops.vehicleJourneyRef` | First non-empty; journey-scoped cache |
| `DelayMin` | `linkprogress.delaySeconds` → `stopinfo.estimate.delay` | `floor(seconds / 60)` |
| `DistanceToNext` | `linkprogress.distance` | Metres; `-1` if absent |
| `DistanceFromPrev` | — | `-1` (not in MQTT) |
| `DestinationName` | `destination.externalDisplay` | `destinationName` + optional ` via ` + `viaDestinationName` |
| `ETA` / `ETAMinutes` | `linkprogress.expectedArrivalTimeDestination` | Local `hh:mm`; minutes from now |
| `DestinationExtended[]` | `destination`, `list/destinations` | One row per unique destination |
| `DestinationExtended[].DestinationStopIdx` | Last stop in `list/stops` | `stops[].number` |
| `Content[].Name` | `list/stops.stops[].name` | Skip `blind` stops |
| `Content[].StopIdx` | `list/stops.stops[].number` | Call sequence (same as MQTT `callSequenceNumber`) |
| `Content[].TariffZone` | `stops[].zoneCode` → `stops[].zone` | String |
| `Content[].Time` | `linkprogress.followingStops[].expectedArrivalTime` or stop ETA | `"N min"`, `"Now"`, `"1 min"` |
| `Content[].TimeArrival` | Same ISO time | Local `hh:mm` (`accounts.*.timezone`) |
| `Content[].AtStop` | `stopinfo.type` | `ARRIVAL` → true on first row; `DEPARTURE` → false |
| `Content[].Requested` | `sensors/stop_button.stopPressed` or stop flags | `alightingAllowed` default true |
| `Content[].Note` | `stops[].cancelled` | `"cancelled"` or empty |
| `Content[].Connections` | `connections.connections[]` | Compact mode: unique lines per `transportModeCode` |
| `Connections[].TransportType` | `connections.transportModeCode` | BUS→700, TRAM→900, RAIL→100, METRO→400 |
| `Count` | Built rows | Max `accounts.*.max_following_stops` |
| `Heading` | constant | `"Following stops"` |
| `StatusCode` | — | 200 if `Count > 0`, else 204 |

### Stop selection logic

Position comes from **`pis/0/stopinfo`** (not `linkprogress`):

1. **`ARRIVAL`** at sequence *N* → first row is stop *N*, `AtStop: true`.
2. **`DEPARTURE`** or **`PASSAGE`** at *N* → first row is stop *N+1*, `AtStop: false`.
3. Stop names and route from `list/stops` matched by `vehicleJourneyRef` (partial list updates are merged).
4. ETAs from `linkprogress.followingStops[]` or `stops[].estimatedArrivalFull`.

## LD — Line destinations

| TCO JSON field | MQTT source | Transformation |
|----------------|-------------|----------------|
| `Heading` | `connections.heading` | Or `"Departures at {stop name}"` |
| `Message` | `connections.message` | When empty list |
| `Display` | `connections.displayDurationSeconds` | Default -1 |
| `Content[].Mode` | `connections[].transportModeCode` | Uppercase string |
| `Content[].Line` | `connections[].lineDesignation` | Required |
| `Content[].Dest` | `connections[].directionName` | |
| `Content[].Stop` | `connections[].stopPointDesignation` | |
| `Content[].Times` | See departure formats below | Relative `"N min"` or local `hh:mm` |
| `Content[].TimesExtended` | Same departures | Planned/absolute/relative/delay |
| `StatusCode` | — | 200 if non-empty and not expired |

### Departure time formats

The builder accepts two connection shapes:

**HSL / spec `departures[]` array**

| MQTT field | TCO field |
|------------|-----------|
| `departures[].plannedDepartureTime` | `TimesExtended[].PlannedTime` (local) |
| `departures[].expectedDepartureTime` | `TimesExtended[].Absolute` (local) |
| computed from ISO | `Times[]`, `TimesExtended[].Relative` |
| `departures[].departureDelaySeconds` | `TimesExtended[].DelayMin` |

**Vilnius compact format** (no `departures` array)

| MQTT field | TCO field |
|------------|-----------|
| `presentedDepartureTimes[]` | `Times[]`, `TimesExtended[].Relative` (`"00:06"` → `"6 min"`) |
| `nextPlannedDepartureTime` | First row `TimesExtended[].PlannedTime` (local) |
| `nextExpectedDepartureTime` | First row `TimesExtended[].Absolute` (local) |

All ISO timestamps are UTC in MQTT; displayed clock times use `accounts.*.timezone`.

**Gating:** Shown when `connections.callSequenceNumber` matches the current or next stop from `stopinfo`, and `expiryDateTime` is not in the past.

## TD / MD — Train / Metro

Not produced from MQTT in this version. Areas always return `StatusCode: 204` with empty `Content`. (Full ITCS stack fills these from Darwin LDBWS / TfGM.)

## OM — Operation messages

| TCO JSON field | MQTT source |
|----------------|-------------|
| `Content[].MessageData.Heading` | `connections.situationMessages[].heading`, `list/announcements`, or `announcement.message[]` |
| `Content[].MessageData.Detail` | `...body` |
| `Content[].MessageData.Heading_Multilanguage` | `heading_Multilanguage` or per-language `message[]` |
| `Content[].MessageData.ValidFrom` / `ValidTo` | ISO 8601 UTC |
| `MessageType` | `0` general (`announcement`), `2` situation/line |
| `Heading` | `"Traffic info for {stop}"` when messages present |

Language: entries matching `accounts.*.base_language` (e.g. `lt`, `fi`, `en`).

**Testing without MQTT:** set `inject_example_om_when_empty: true` and define `example_om_messages` (see Account settings above). Live MQTT messages take precedence; examples appear only when OM would otherwise be empty.

## Status code summary

| Condition | FS | LD | OM |
|-----------|----|----|-----|
| No journey / stops | 204 | 204 | 204* |
| Journey active, following stops | 200 | — | — |
| Valid connections at current stop | — | 200 | — |
| Situation / announcement | — | — | 200 |
| Example OM configured, no MQTT OM | — | — | 200 |

\* OM may still be 200 when `inject_example_om_when_empty` is enabled and the vehicle has journey/stop context.

## Vehicle id alignment

HTTP `GET /api/stopinfo/vilnius/1232` reads MQTT state for vehicle **`1232`**.

Ensure on-board MQTT publishers use the same id in the topic path (`/1232/pis/0/...) as displays use in HTTP.

## Reference

- MQTT-PIS-PT specification: `docs/mqtt-pis-pt-specification.md`
- TCO HTTP spec: `docs/tco-stopinfo-api-spec.md`
